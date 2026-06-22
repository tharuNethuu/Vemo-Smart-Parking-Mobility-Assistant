# Vemo AI - Smart Parking & Mobility Assistant

Vemo AI is an AI-powered parking assistant with two core modules:

1. **Green Parking Optimizer** — predicts parking occupancy across multiple car parks and recommends the best one based on arrival time and day, with estimated time and CO₂ savings.
2. **AI Memory Assistant** — lets users save a natural-language parking note (e.g. *"parked near the yellow barrier"*) and automatically extracts zone, floor, and landmark details, inferring missing information from a landmark knowledge base when needed.

The app is built as a mobile-first React web app backed by a Flask API, combining classic machine learning, NLP/transformer models, and a generative AI layer.

---

## Features

- 📍 **Occupancy prediction** for 18 parking zones using Random Forest / XGBoost
- 🌱 **CO₂ savings estimate** comparing recommended vs. busiest parking zone
- 🧠 **Natural language parking notes** parsed with a custom-trained SpaCy NER model (benchmarked against BERT)
- 🔎 **Landmark knowledge-base lookup** with fuzzy matching to infer missing zone/floor details, including conflict detection
- 💬 **AI-generated recommendations and summaries** via Groq's LLaMA 3.1 model
- 📱 **Mobile-first UI** with a clean, minimal design and bottom navigation

---

## Tech Stack

**Machine Learning / Data**
- Python, Pandas, NumPy
- Scikit-learn (Random Forest)
- XGBoost

**NLP**
- SpaCy (custom-trained NER model)
- Hugging Face Transformers (BERT, for comparison)

**Generative AI**
- Groq API — LLaMA 3.1 (`llama-3.1-8b-instant`)

**Backend**
- Flask, Flask-CORS
- Gunicorn (production server)

**Frontend**
- React (Create React App)
- Axios
- Lucide React (icons)

**Dataset**
- [Parking Birmingham Dataset](https://archive.ics.uci.edu/dataset/482/parking+birmingham) (UCI Machine Learning Repository) — ~35,000 occupancy records across 18 car parks
- A custom-built dataset of parking notes for NLP entity extraction (`data/raw/parking_notes.csv`)

**Hosting**
- Backend: Railway
- Frontend: Vercel

---

## Project Structure

```
Vemo/
├── api/
│   └── index.py                # Flask backend (production entry point)
├── app/
│   ├── backend/
│   │   └── app.py              # Flask backend (local development)
│   └── frontend/                # React app
│       ├── public/
│       └── src/
│           ├── App.js
│           ├── App.css
│           ├── index.css
│           └── pages/
│               ├── Optimizer.jsx
│               ├── Memory.jsx
│               └── Pages.css
├── data/
│   ├── raw/
│   │   ├── dataset.csv          # Parking Birmingham dataset
│   │   └── parking_notes.csv    # Custom NLP dataset / knowledge base
│   └── processed/                # Cleaned data, train/test splits, plots
├── models/
│   ├── best_model.pkl           # Trained occupancy prediction model
│   ├── spacy_ner_model/         # Trained SpaCy NER model
│   ├── ner_comparison.json
│   └── app_config.json
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_training.ipynb
│   ├── 04_recommendation.ipynb
│   ├── 05_spacy_ner.ipynb
│   ├── 06_bert_ner.ipynb
│   └── 07_generative_ai.ipynb
├── requirements.txt
├── vercel.json
├── Procfile
└── .gitignore
```

---

## Prerequisites

- **Python** 3.9 – 3.12
- **Node.js** 18.x and npm
- A free **Groq API key** — [console.groq.com](https://console.groq.com)

---

## Dependencies

### Python (backend / ML)

```
flask
flask-cors
joblib
pandas
numpy
scikit-learn
xgboost
spacy
groq
gunicorn
```

Install with:
```bash
pip install -r requirements.txt --break-system-packages
```

You also need the SpaCy base model (used during training/comparison steps):
```bash
python -m spacy download en_core_web_sm
```

### Frontend (Node)

```
react
react-dom
axios
lucide-react
```

Installed automatically via `npm install` (see setup below).

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/tharuNethuu/Vemo-Smart-Parking-Mobility-Assistant.git
cd Vemo-Smart-Parking-Mobility-Assistant
```

### 2. Set up a Python virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Add your Groq API key

In `app/backend/app.py` (local dev) and `api/index.py` (production), the key is read from an environment variable:

```python
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
```

Set it locally before running the backend:

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

**macOS / Linux:**
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

Alternatively, create a `.env` file and load it, or hardcode it temporarily for local testing only (never commit real keys).

### 5. Run the backend (Flask)

```bash
cd app/backend
python app.py
```

The API will be available at `http://localhost:5000`. Health check:
```
GET http://localhost:5000/api/health
```

### 6. Install frontend dependencies

```bash
cd app/frontend
npm install
```

### 7. Run the frontend (React)

```bash
npm start
```

The app will open at `http://localhost:3000`.

> **Note:** Make sure the API base URL in `src/pages/Optimizer.jsx` and `src/pages/Memory.jsx` points to `http://localhost:5000` for local development, or your deployed backend URL in production.

### 8. Access on mobile (same WiFi)

1. Find your computer's local IP:
   ```bash
   ipconfig        # Windows
   ifconfig        # macOS / Linux
   ```
2. Run Flask with `host='0.0.0.0'` (already configured).
3. Allow port 5000 through your firewall if needed.
4. On your phone, open `http://<your-local-ip>:3000`.

---

## Rebuilding the Models (Optional)

The trained models are already included in `models/`. If you want to retrain them from scratch, run the notebooks in order:

| Notebook | Purpose |
|---|---|
| `01_eda.ipynb` | Clean and explore the Birmingham parking dataset |
| `02_feature_engineering.ipynb` | Build features (hour, day, lag occupancy) and train/test split |
| `03_model_training.ipynb` | Train and compare Random Forest vs. XGBoost |
| `04_recommendation.ipynb` | Build the parking recommendation + CO₂ logic |
| `05_spacy_ner.ipynb` | Train the SpaCy NER model on parking notes |
| `06_bert_ner.ipynb` | Compare SpaCy vs. BERT for entity extraction |
| `07_generative_ai.ipynb` | Test the Groq LLaMA recommendation and memory prompts |

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/recommend` | POST | Returns best parking recommendation, ranked predictions, and CO₂ savings for a given hour/day |
| `/api/memory` | POST | Extracts zone/floor/landmark from a parking note, infers missing details, and returns an AI-generated summary |

**Example request — `/api/recommend`:**
```json
{
  "hour": 8,
  "dayEncoded": 2
}
```

**Example request — `/api/memory`:**
```json
{
  "note": "I parked near the yellow barrier"
}
```

---

## Deployment

This project is split across two free hosting platforms:

| Component | Platform | Notes |
|---|---|---|
| Backend (Flask) | [Railway](https://railway.app) | Set `GROQ_API_KEY` as an environment variable; start command `gunicorn api.index:app --bind 0.0.0.0:8080` |
| Frontend (React) | [Vercel](https://vercel.com) | Root directory `app/frontend`; build command `npm run build`; output directory `build` |

> Vercel's serverless functions have a 500MB bundle limit, which the combined ML/NLP dependencies (SpaCy + XGBoost + scikit-learn) exceed — this is why the backend is hosted separately on Railway.

---

## Dataset Credits

- **Parking Birmingham Dataset** — Daniel H. Stolfi, University of Málaga, Spain. Sourced from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/482/parking+birmingham). Occupancy records (08:00–16:30) from 2016-10-04 to 2016-12-19 across 18 car parks.
- **Parking notes dataset** — custom-created for this project to train and evaluate the NLP entity extraction module.

---

## Demo

- 🎥 **Video walkthrough:** 
- 📱 **Live app:** https://vemo-ai.vercel.app/


---

## Team

EG/2021/4408	Arachchi N.A.N.N.N.
EG/2021/4412	Arachchi W.A.T.T.W
EG/2021/4538	Jayaweera J.A.P.V
EG/2021/4706	Peiris P R S

---

