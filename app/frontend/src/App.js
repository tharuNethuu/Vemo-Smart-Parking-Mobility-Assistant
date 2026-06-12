import { useState } from "react";
import Optimizer from "./pages/Optimizer";
import Memory    from "./pages/Memory";
import { Car, Brain } from "lucide-react";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("optimizer");

  return (
    <div className="app-shell">
      <div className="page-content">
        {page === "optimizer" ? <Optimizer /> : <Memory />}
      </div>

      <nav className="bottom-nav">
        <button
          className={`nav-item ${page === "optimizer" ? "active" : ""}`}
          onClick={() => setPage("optimizer")}
        >
          <Car size={22} />
          <span>Optimizer</span>
        </button>
        <button
          className={`nav-item ${page === "memory" ? "active" : ""}`}
          onClick={() => setPage("memory")}
        >
          <Brain size={22} />
          <span>Memory</span>
        </button>
      </nav>
    </div>
  );
}