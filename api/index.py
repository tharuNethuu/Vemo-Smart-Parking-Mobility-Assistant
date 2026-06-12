from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import os
from groq import Groq
from difflib import SequenceMatcher



app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

        
# Base path — points to project root from api/ folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load models
best_model    = joblib.load(os.path.join(BASE_DIR, 'models', 'best_model.pkl'))

import spacy
spacy_nlp     = spacy.load(os.path.join(BASE_DIR, 'models', 'spacy_ner_model'))

# Groq client
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY")
client        = Groq(api_key=GROQ_API_KEY)

# Knowledge base
knowledge_base = pd.read_csv(os.path.join(BASE_DIR, 'data', 'raw', 'parking_notes.csv'))

DAY_NAMES = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday",6:"Sunday"}

# ── helpers ──────────────────────────────────────────────

def predict_all_parks(hour, day_encoded, num_parks=18, prev_occupancy=50.0):
    results = []
    for park_id in range(num_parks):
        sample = pd.DataFrame([{
            'Hour': hour,
            'DayOfWeek_encoded': day_encoded,
            'ParkID_encoded': park_id,
            'OccupancyRate_lag1': prev_occupancy
        }])
        pred = float(best_model.predict(sample)[0])
        pred = max(0, min(100, pred))
        results.append({'parkId': f"Park_{park_id}", 'occupancy': round(pred, 1)})
    return sorted(results, key=lambda x: x['occupancy'])


def build_prompt(hour, day_name, predictions):
    park_lines = ""

    for p in predictions[:5]:
        occ = p['occupancy']

        if occ < 40:
            status = "🟢 Low traffic"
        elif occ < 70:
            status = "🟡 Moderate traffic"
        else:
            status = "🔴 Busy"

        park_lines += f"- {p['parkId']} → {occ}% occupied ({status})\n"

    return f"""
You are Vemo, a friendly AI parking assistant.

Your goal is to help drivers find parking quickly, reduce unnecessary driving, save time, and lower vehicle emissions.

Current Situation:
- Arrival Time: {hour}:00
- Day: {day_name}

Predicted Parking Occupancy:

{park_lines}

Instructions:
1. Recommend the BEST parking location.
2. Explain WHY it is the best choice in simple words.
3. Estimate how much time the driver may save compared to the busiest parking area.
4. Estimate CO₂ emissions saved.
5. Give one short eco-friendly parking tip.
6. Keep the response positive, practical, and easy to understand.
7. Use bullet points where appropriate.
8. Keep the answer under 150 words.

Write as if you are talking directly to the driver. Use some emojis to make it friendly and engaging!
"""

def fuzzy_match_score(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def lookup_landmark(landmark_text, threshold=0.6):
    best_score  = 0
    best_match  = None
    candidates  = []

    for _, row in knowledge_base.iterrows():
        if pd.isna(row['landmark']) or str(row['landmark']).strip() == '':
            continue

        score = fuzzy_match_score(landmark_text, str(row['landmark']))

        if score > threshold:
            candidates.append({
                'landmark' : str(row['landmark']),
                'zone'     : str(row['zone'])     if pd.notna(row['zone'])  and str(row['zone']).strip()  != '' else None,
                'floor'    : str(row['floor'])    if pd.notna(row['floor']) and str(row['floor']).strip() != '' else None,
                'score'    : round(score, 2)
            })

        if score > best_score:
            best_score = score
            best_match = row

    candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)[:3]

    if best_score >= threshold and best_match is not None:
        return {
            'found'      : True,
            'score'      : round(best_score, 2),
            'zone'       : str(best_match['zone'])  if pd.notna(best_match['zone'])  and str(best_match['zone']).strip()  != '' else None,
            'floor'      : str(best_match['floor']) if pd.notna(best_match['floor']) and str(best_match['floor']).strip() != '' else None,
            'landmark'   : str(best_match['landmark']),
            'candidates' : candidates
        }

    return {'found': False, 'candidates': candidates}
# ── routes ───────────────────────────────────────────────

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data        = request.json
    hour        = int(data.get('hour', 8))
    day_encoded = int(data.get('dayEncoded', 0))
    day_name    = DAY_NAMES.get(day_encoded, "Monday")

    predictions = predict_all_parks(hour, day_encoded)
    prompt      = build_prompt(hour, day_name, predictions)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
    {
        "role": "system",
        "content": """
You are Vemo.

Vemo is a smart, friendly, and eco-conscious parking assistant.

Your personality:
- Helpful
- Positive
- Friendly
- Easy to understand

Always:
- Give practical advice
- Explain recommendations clearly
- Encourage eco-friendly decisions
- Use simple language

Avoid:
- Technical jargon
- Long paragraphs
- Complex explanations
"""
    },
    {
        "role": "user",
        "content": prompt
    }
],
        temperature=0.7,
        max_tokens=400
    )

    return jsonify({
        'recommendation': response.choices[0].message.content,
        'predictions'   : predictions[:5],
        'bestPark'      : predictions[0],
        'worstPark'     : predictions[-1],
        'co2Saved'      : round((predictions[-1]['occupancy'] - predictions[0]['occupancy']) * 1.2, 1)
    })


@app.route('/api/memory', methods=['POST'])
def memory():
    data = request.json
    note = data.get('note', '')

    # Step 1 - Extract entities with SpaCy
    doc       = spacy_nlp(note)
    extracted = {ent.label_: ent.text for ent in doc.ents}

    # Step 2 - Check for gaps and do landmark lookup
    lookup_result  = None
    inferred       = {}
    conflict       = None

    if 'LANDMARK' in extracted:
        lookup_result = lookup_landmark(extracted['LANDMARK'])

        if lookup_result['found']:
            # Fill missing zone
            if 'ZONE' not in extracted and lookup_result['zone']:
                inferred['ZONE'] = lookup_result['zone']

            # Fill missing floor
            if 'FLOOR' not in extracted and lookup_result['floor']:
                inferred['FLOOR'] = lookup_result['floor']

            # Detect conflict - user said Zone A but landmark belongs to Zone D
            if 'ZONE' in extracted and lookup_result['zone']:
                if extracted['ZONE'].strip().upper() != lookup_result['zone'].strip().upper():
                    conflict = {
                        'field'   : 'ZONE',
                        'stated'  : extracted['ZONE'],
                        'inferred': lookup_result['zone']
                    }

    # Step 3 - Merge extracted + inferred
    final = {**extracted, **inferred}

    # Step 4 - Build smart prompt
    inferred_note = ""
    if inferred:
        parts = []
        if 'ZONE' in inferred:
            parts.append(f"Zone {inferred['ZONE']} (inferred from landmark)")
        if 'FLOOR' in inferred:
            parts.append(f"Floor {inferred['FLOOR']} (inferred from landmark)")
        inferred_note = f"Additionally inferred from landmark database: {', '.join(parts)}."

    conflict_note = ""
    if conflict:
        conflict_note = f"WARNING: The driver said Zone {conflict['stated']} but the landmark database suggests Zone {conflict['inferred']}. Flag this conflict politely."

    candidates_note = ""
    if lookup_result and len(lookup_result.get('candidates', [])) > 1:
        others = [f"{c['landmark']} (Zone {c['zone'] or '?'}, Floor {c['floor'] or '?'})" 
                  for c in lookup_result['candidates'][1:]]
        candidates_note = f"Other possible matches in database: {', '.join(others)}."

    prompt = f"""
You are Vemo, a friendly parking memory assistant.

A driver saved this note about where they parked:

"{note}"

What Vemo found from the note:
• Zone: {extracted.get('ZONE', 'Not mentioned')}
• Floor: {extracted.get('FLOOR', 'Not mentioned')}
• Landmark: {extracted.get('LANDMARK', 'Not mentioned')}

{inferred_note}

{conflict_note}

{candidates_note}

Your job is to help the driver remember where their vehicle is parked.

Write a warm and friendly response that:

1. Confirms the parking location in simple words.
2. Naturally include any details inferred from nearby landmarks.
3. If there is conflicting information, politely point it out and suggest double-checking.
4. Give a helpful tip that will make it easier to find the vehicle later.
5. Sound reassuring and conversational.
6. Keep the response short (2-4 sentences).

Write directly to the driver as Vemo.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": """
            You are Vemo, a friendly parking companion.

            Your personality:
            - Warm and helpful
            - Easy to understand
            - Reassuring and positive
            - Supportive without sounding robotic

            Always:
            - Speak directly to the driver
            - Use simple everyday language
            - Help the driver feel confident about finding their vehicle later

            Avoid:
            - Technical terms
            - Database terminology
            - NLP, extraction, inference, entity, prediction, or model-related wording
            - Long explanations
            """
            },
            {"role": "user",   "content": prompt}
        ],
        temperature=0.5,
        max_tokens=200
    )

    return jsonify({
        'extracted'    : extracted,
        'inferred'     : inferred,
        'final'        : final,
        'conflict'     : conflict,
        'lookup'       : lookup_result,
        'summary'      : response.choices[0].message.content,
        'note'         : note
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Vemo AI backend running'})


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')