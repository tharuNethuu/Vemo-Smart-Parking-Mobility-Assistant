import { useState } from "react";
import axios from "axios";
import { MapPin, Clock, Leaf, ChevronRight, Loader } from "lucide-react";
import "./Pages.css";
import ReactMarkdown from "react-markdown";

const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];

export default function Optimizer() {
  const [hour,       setHour]       = useState(8);
  const [dayEncoded, setDayEncoded] = useState(0);
  const [loading,    setLoading]    = useState(false);
  const [result,     setResult]     = useState(null);
  const [error,      setError]      = useState("");

  async function handleSubmit() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await axios.post("http://localhost:5000/api/recommend", {
        hour, dayEncoded
      });
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
        <div className="header-icon"><Leaf size={20} color="#fff" /></div>
        <div>
          <h1 className="header-title">Smart Parking Assistant</h1>
          <p className="header-sub">Smarter parking decisions in seconds.</p>
        </div>
      </div>

      {/* Input Card */}
      <div className="card">
        <div className="card-label">
          <span>
            Tell us when you're planning to leave, and Vemo will find the best parking
            option for you.
          </span>
          <img
            src="car1.png"
            alt="Car"
            className="card-label-icon"
          />
        </div>
        <div className="input-group">
          <label className="input-label"><Clock size={14}/> Hour</label>
          <input
            type="range" min={8} max={16} value={hour}
            onChange={e => setHour(Number(e.target.value))}
            className="slider"
          />
          <span className="slider-value">{hour}:00</span>
        </div>

        <div className="input-group">
          <label className="input-label">Day of Week</label>
          <select
            value={dayEncoded}
            onChange={e => setDayEncoded(Number(e.target.value))}
            className="select-input"
          >
            {DAYS.map((d, i) => (
              <option key={i} value={i}>{d}</option>
            ))}
          </select>
        </div>

        <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
          {loading
            ? <><Loader size={16} className="spin"/> Analyzing...</>
            : <><MapPin size={16}/> Find Best Parking</>
          }
        </button>

        {error && <p className="error-text">{error}</p>}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Best Park */}
          <div className="card highlight-card">
            <div className="highlight-row">
              <div>
                <p className="highlight-label">Best Park</p>
                <p className="highlight-value">{result.bestPark.parkId}</p>
              </div>
              <div className="occupancy-badge">
                {result.bestPark.occupancy}%
              </div>
            </div>
            <div className="co2-row">
              <Leaf size={14} color="#2d7a4f"/>
              <span>{result.co2Saved}g CO₂ saved vs busiest park</span>
            </div>
          </div>

          {/* Top 5 Parks */}
          <div className="card">
            <p className="card-label">🅿 Parking options ranked from best to busiest</p>
            {result.predictions.map((p, i) => (
              <div key={i} className="park-row">
                <span className="park-rank">#{i + 1}</span>
                <span className="park-name">{p.parkId}</span>
                <div className="park-bar-wrap">
                  <div
                    className="park-bar"
                    style={{
                      width: `${p.occupancy}%`,
                      background: p.occupancy < 40
                        ? "#039e44"
                        : p.occupancy < 70
                        ? "#fc7100"
                        : "#fd0e22"
                    }}
                  />
                </div>
                <span className="park-pct">{p.occupancy}%</span>
              </div>
            ))}
          </div>

          {/* AI Recommendation */}
          <div className="card ai-card">
            <div className="ai-header">
              <div className="ai-dot" />
              <span>AI Recommendation</span>
            </div>
            <p className="ai-text"><ReactMarkdown>{result.recommendation}</ReactMarkdown></p>
          </div>
        </>
      )}
    </div>
  );
}