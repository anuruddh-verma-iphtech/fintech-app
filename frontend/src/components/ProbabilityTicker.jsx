import { useEffect, useState } from "react";
import {
  fetchTickerMarkets,
  formatProbability,
  formatTimeLeft,
} from "../utils/api";

const CATEGORY_COLORS = {
  weather: "#0ea5e9",
  sports: "#10b981",
  finance: "#f59e0b",
  other: "#8b5cf6",
};

export default function ProbabilityTicker() {
  const [markets, setMarkets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    fetchTickerMarkets()
      .then((d) => {
        setMarkets(d.markets || []);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (markets.length < 2) return;
    const id = setInterval(
      () => setIndex((i) => (i + 1) % markets.length),
      4000,
    );
    return () => clearInterval(id);
  }, [markets]);

  if (loading)
    return <div className="ticker-loading">Loading live markets…</div>;
  if (error) return <div className="ticker-error">⚠ {error}</div>;
  if (!markets.length)
    return <div className="ticker-empty">No live markets available</div>;

  return (
    <div>
      <div className="ticker-row">
        {markets.map((item, i) => (
          <div className="ticker-card" key={i}>
            <div className="ticker-title">{item.card_title}</div>
            <div
              className="ticker-prob"
              style={{
                "--cat-color":
                  CATEGORY_COLORS[item.category] || CATEGORY_COLORS.other,
              }}
            >
              {item.probability}%
            </div>
          </div>
        ))}
      </div>
      <div className="ticker-wrapper">
        <div className="ticker-label">LIVE</div>
        <div className="ticker-scroll">
          {markets.map((m, i) => (
            <div
              key={m.ticker}
              className={`ticker-item ${i === index ? "active" : ""}`}
              style={{
                "--cat-color":
                  CATEGORY_COLORS[m.category] || CATEGORY_COLORS.other,
              }}
            >
              <span className="ticker-title">{m.title}</span>
              <span className="ticker-prob">
                {formatProbability(m.probability)}
              </span>
              <span className="ticker-time">
                {formatTimeLeft(m.hours_until_close)}
              </span>
            </div>
          ))}
        </div>
        <div className="ticker-dots">
          {markets.map((_, i) => (
            <button
              key={i}
              className={`dot ${i === index ? "active" : ""}`}
              onClick={() => setIndex(i)}
              aria-label={`Market ${i + 1}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
