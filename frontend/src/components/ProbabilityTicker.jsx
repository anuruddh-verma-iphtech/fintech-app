import { useEffect, useRef, useState } from "react";
import {
  fetchTickerMarkets,
  formatProbability,
  formatTimeLeft,
} from "../utils/api";
import "../App.css"

const CAT_COLOR = {
  weather: "#0ea5e9",
  sports: "#4ade80",
  finance: "#f59e0b",
  other: "#8b5cf6",
};

const S = {
  wrap: {
    fontFamily: "system-ui, sans-serif",
  },

  /* ── Scrollable chip row ───────────────────────── */
  chipRow: {
    display: "flex",
    gap: 8,

    overflowX: "auto",
    overflowY: "hidden",

    whiteSpace: "nowrap",

    cursor: "grab",

    WebkitOverflowScrolling: "touch",

    scrollbarWidth: "none",
    msOverflowStyle: "none",

    padding: "0.5rem 0",
  },

  chip: (color) => ({
    flex: "0 0 auto",

    display: "flex",
    alignItems: "center",
    gap: 6,

    border: "1px solid #333",
    borderRadius: 999,

    padding: "5px 12px",

    fontSize: 12,

    background: "#1c1c1c",

    whiteSpace: "nowrap",

    color: "#ccc",

    cursor: "pointer",

    minWidth: "max-content",
  }),

  chipPct: (color) => ({
    fontWeight: 700,
    color,
  }),

  /* ── Banner card ───────────────────────── */
  bannerCard: {
    background: "#1e1e1e",
    border: "1px solid #2a2a2a",
    borderRadius: 16,
    marginTop: "0.75rem",
    overflow: "hidden",
  },

  livePill: {
    fontSize: 10,
    fontWeight: 700,
    background: "#f87171",
    color: "#fff",
    borderRadius: 999,
    padding: "2px 7px",
    letterSpacing: 0.5,
  },

  bannerBody: {
    padding: "0.85rem 1rem",
  },

  activeTitle: {
    fontSize: 16,
    fontWeight: 700,
    color: "#fff",
    lineHeight: 1.35,
    marginBottom: "0.6rem",
  },

  activeMeta: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    fontSize: 12,
    color: "#555",
    flexWrap: "wrap",
  },

  activeProb: (color) => ({
    fontSize: 13,
    fontWeight: 700,
    color,
  }),

  /* ── Dots ───────────────────────── */
  dotRow: {
    display: "flex",
    justifyContent: "center",
    gap: 6,
    padding: "0.6rem 0 0.85rem",
  },

  dot: (active) => ({
    width: active ? 18 : 6,
    height: 6,
    borderRadius: 999,
    background: active ? "#5b9cf6" : "#333",
    border: "none",
    cursor: "pointer",
    transition: "all 0.2s",
    padding: 0,
  }),

  state: {
    fontSize: 13,
    color: "#555",
    padding: "0.75rem 0",
  },
};

export default function ProbabilityTicker() {
  const [markets, setMarkets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [index, setIndex] = useState(0);

  const scrollRef = useRef(null);

  /* ── Fetch data ───────────────────────── */
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

  /* ── Auto rotate ───────────────────────── */
  useEffect(() => {
    if (markets.length < 2) return;

    const id = setInterval(() => {
      setIndex((i) => (i + 1) % markets.length);
    }, 4000);

    return () => clearInterval(id);
  }, [markets]);

  /* ── Mouse drag + wheel scroll ───────────────────────── */
  useEffect(() => {
    const slider = scrollRef.current;

    if (!slider) return;

    let isDown = false;
    let startX;
    let scrollLeft;

    const mouseDown = (e) => {
      isDown = true;

      slider.style.cursor = "grabbing";

      startX = e.pageX - slider.offsetLeft;
      scrollLeft = slider.scrollLeft;
    };

    const mouseLeave = () => {
      isDown = false;
      slider.style.cursor = "grab";
    };

    const mouseUp = () => {
      isDown = false;
      slider.style.cursor = "grab";
    };

    const mouseMove = (e) => {
      if (!isDown) return;

      e.preventDefault();

      const x = e.pageX - slider.offsetLeft;

      const walk = (x - startX) * 1.5;

      slider.scrollLeft = scrollLeft - walk;
    };

    /* Mouse wheel horizontal scroll */
    const wheelScroll = (e) => {
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
        e.preventDefault();

        slider.scrollLeft += e.deltaY;
      }
    };

    slider.addEventListener("mousedown", mouseDown);
    slider.addEventListener("mouseleave", mouseLeave);
    slider.addEventListener("mouseup", mouseUp);
    slider.addEventListener("mousemove", mouseMove);

    slider.addEventListener("wheel", wheelScroll, {
      passive: false,
    });

    return () => {
      slider.removeEventListener("mousedown", mouseDown);
      slider.removeEventListener("mouseleave", mouseLeave);
      slider.removeEventListener("mouseup", mouseUp);
      slider.removeEventListener("mousemove", mouseMove);

      slider.removeEventListener("wheel", wheelScroll);
    };
  }, []);

  if (loading) {
    return <div style={S.state}>Loading live markets…</div>;
  }

  if (error) {
    return (
      <div style={{ ...S.state, color: "#f87171" }}>
        ⚠ {error}
      </div>
    );
  }

  if (!markets.length) {
    return <div style={S.state}>No live markets available</div>;
  }

  const active = markets[index];

  const activeColor =
    CAT_COLOR[active?.category] || CAT_COLOR.other;

  return (
    <div style={S.wrap}>

    
      {/* ── Chip row ───────────────────────── */}
      <div
        ref={scrollRef}
        style={S.chipRow}
        className="hide-scrollbar"
      >
        {markets.map((m, i) => {
          const color =
            CAT_COLOR[m.category] || CAT_COLOR.other;

          return (
            <div
              key={m.ticker}
              style={S.chip(color)}
              onClick={() => setIndex(i)}
            >
              <span>{m.card_title}</span>

              <span style={S.chipPct(color)}>
                {m.probability}%
              </span>
            </div>
          );
        })}
      </div>

      {/* ── Banner card ───────────────────────── */}
      <div style={S.bannerCard}>
        <div
          style={{
            borderTop: "1px solid #2a2a2a",
            ...S.bannerBody,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              marginBottom: "0.5rem",
            }}
          >
            <span style={S.livePill}>LIVE</span>

            <span
              style={{
                fontSize: 11,
                color: "#555",
              }}
            >
              {active?.category}
            </span>
          </div>

          <div style={S.activeTitle}>
            {active?.title}
          </div>

          <div style={S.activeMeta}>
            <span style={S.activeProb(activeColor)}>
              {formatProbability(active?.probability)} YES
            </span>

            <span>·</span>

            <span>
              {active?.volume?.toLocaleString()} trades
            </span>

            <span>·</span>

            <span>
              {formatTimeLeft(active?.hours_until_close)}
            </span>
          </div>
        </div>

        {/* ── Dot nav ───────────────────────── */}
        <div style={S.dotRow}>
          {markets.map((_, i) => (
            <button
              key={i}
              style={S.dot(i === index)}
              onClick={() => setIndex(i)}
              aria-label={`Market ${i + 1}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}