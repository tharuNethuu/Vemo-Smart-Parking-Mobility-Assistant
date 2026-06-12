import { useState } from "react";
import axios from "axios";
import { Brain, MapPin, Layers, Landmark, Loader } from "lucide-react";
import "./Pages.css";
import ReactMarkdown from "react-markdown";

export default function Memory() {
  const [note,    setNote]    = useState("");
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState("");

  async function handleSubmit() {
    if (!note.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await axios.post("https://vemo-smart-parking-mobility-assistant-production.up.railway.app/api/memory", { note });
      setResult(res.data);
    } catch {
      setError("Could not connect to backend. Make sure Flask is running.");
    }
    setLoading(false);
  }

  return (
    <div className="page">
      {/* Header */}
      <div className="page-header">
        <img
            src="vemo.png"
            alt="vemo-logo"
            className="vemo-logo"
          />
        <div className="header-icon"><Brain size={20} color="#fff" /></div>
        <div>
          <h1 className="header-title">Parking Memory Assistant</h1>
          <p className="header-sub">Remember your spot, return with ease.</p>
        </div>
      </div>

      {/* Input Card */}
      <div className="card">
        <div className="card-label">
           <span>
            Tell us where you parked, and Vemo will help you remember it when you return.
          </span>
          <img
            src="car2.png"
            alt="Car"
            className="card-label-icon"
          />
        </div>
        <textarea
          className="text-area"
          placeholder="e.g. I parked near the blue pillar in Zone A on Level 2..."
          value={note}
          onChange={e => setNote(e.target.value)}
          rows={4}
        />
        <button className="btn-primary" onClick={handleSubmit} disabled={loading || !note.trim()}>
          {loading
            ? <><Loader size={16} className="spin"/> Processing...</>
            : <><Brain size={16}/> Save & Analyze</>
          }
        </button>
        {error && <p className="error-text">{error}</p>}
      </div>

      {/* Results */}
     {result && (
  <>
    {/* Conflict Warning */}
    {result.conflict && (
      <div className="card conflict-card">
        <p className="conflict-title">⚠️ Location Conflict Detected</p>
        <p className="conflict-text">
          You mentioned <strong>Zone {result.conflict.stated}</strong> but your 
          landmark is usually in <strong>Zone {result.conflict.inferred}</strong>. 
          Please double check.
        </p>
      </div>
    )}

    {/* Extracted + Inferred Entities */}
    <div className="card">
      <p className="card-label">Here's what Vemo understood from your note</p>
      <div className="entity-grid">
        <div className="entity-item">
          <MapPin size={16} color="#2d7a4f"/>
          <span className="entity-label">Zone</span>
          <span className="entity-value">
            {result.final.ZONE || "—"}
          </span>
          {result.inferred.ZONE && (
            <span className="inferred-badge">inferred</span>
          )}
        </div>
        <div className="entity-item">
          <Layers size={16} color="#2d7a4f"/>
          <span className="entity-label">Floor</span>
          <span className="entity-value">
            {result.final.FLOOR || "—"}
          </span>
          {result.inferred.FLOOR && (
            <span className="inferred-badge">inferred</span>
          )}
        </div>
        <div className="entity-item">
          <Landmark size={16} color="#2d7a4f"/>
          <span className="entity-label">Landmark</span>
          <span className="entity-value" style={{fontSize:"11px"}}>
            {result.final.LANDMARK || "—"}
          </span>
        </div>
      </div>

      {/* Confidence Score */}
      {result.lookup && result.lookup.found && (
        <div className="confidence-row">
          <span className="confidence-label">Landmark Match Confidence</span>
          <div className="confidence-bar-wrap">
            <div
              className="confidence-bar"
              style={{width: `${result.lookup.score * 100}%`}}
            />
          </div>
          <span className="confidence-score">
            {Math.round(result.lookup.score * 100)}%
          </span>
        </div>
      )}
    </div>

    {/* Other Possible Matches */}
    {result.lookup && result.lookup.candidates && result.lookup.candidates.length > 1 && (
      <div className="card">
        <p className="card-label">📍 Similar parking locations Vemo found</p>
        {result.lookup.candidates.slice(1).map((c, i) => (
          <div key={i} className="candidate-row">
            <span className="candidate-landmark">{c.landmark}</span>
            <span className="candidate-info">
              {c.zone ? `Zone ${c.zone}` : ""}
              {c.zone && c.floor ? " · " : ""}
              {c.floor ? `Floor ${c.floor}` : ""}
            </span>
            <span className="candidate-score">{Math.round(c.score * 100)}%</span>
          </div>
        ))}
      </div>
    )}

    {/* AI Summary */}
    <div className="card ai-card">
      <div className="ai-header">
        <div className="ai-dot"/>
        <span>AI Summary</span>
      </div>
      <p className="ai-text"><ReactMarkdown>{result.summary}</ReactMarkdown></p>
    </div>

    {/* Original Note */}
    <div className="card">
      <p className="card-label">Your Note</p>
      <p className="note-text">"{result.note}"</p>
    </div>
  </>
)}
    </div>
  );
}