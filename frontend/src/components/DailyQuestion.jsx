import { useEffect, useState } from "react";
import {
  fetchDailyMarket,
  fetchMarketResult,
  formatProbability,
} from "../utils/api";
import { loadAnswer, saveAnswer } from "../utils/storage";

const S = {
  card: {
    background: "#1e1e1e",
    border: "1px solid #2a2a2a",
    borderRadius: 16,
    padding: "1.25rem",
    color: "#fff",
    fontFamily: "system-ui, sans-serif",
  },
  labelRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 12,
    color: "#777",
    fontWeight: 500,
    marginBottom: "0.75rem",
  },
  dot: {
    width: 18,
    height: 18,
    border: "1.5px solid #444",
    borderRadius: 4,
    display: "inline-block",
  },
  question: {
    fontSize: 17,
    fontWeight: 700,
    lineHeight: 1.35,
    margin: "0 0 1rem",
  },
  divider: { border: "none", borderTop: "1px solid #2a2a2a", margin: "0.9rem 0" },

  /* prob bar */
  barBg: { background: "#2a2a2a", height: 5, borderRadius: 999, overflow: "hidden" },
  barFill: { height: "100%", borderRadius: 999, background: "#5b9cf6", transition: "width 0.4s" },
  probLabel: { fontSize: 13, color: "#777", textAlign: "center", marginTop: 8 },

  /* vote buttons */
  voteBtn: (selected, variant) => ({
    width: "100%",
    border: selected
      ? `1px solid ${variant === "yes" ? "#4ade80" : "#f87171"}`
      : "1px solid #333",
    borderRadius: 12,
    padding: 14,
    textAlign: "center",
    background: selected
      ? variant === "yes"
        ? "rgba(74,222,128,0.08)"
        : "rgba(248,113,113,0.08)"
      : "#252525",
    cursor: "pointer",
    marginBottom: 10,
    display: "block",
    transition: "all 0.15s",
  }),
  voteBtnTitle: { fontSize: 15, fontWeight: 700, color: "#fff" },
  voteBtnSub:  { fontSize: 12, color: "#666", marginTop: 2 },

  onceNote: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 12,
    color: "#555",
    justifyContent: "center",
    marginTop: 4,
  },
  onceSq: { width: 12, height: 12, border: "1.5px solid #3a3a3a", borderRadius: 3 },

  /* result grid */
  resultGrid: { display: "grid", gridTemplateColumns: "1fr 1px 1fr 1px 1fr" },
  resultSep:  { background: "#2a2a2a" },
  resultCol:  { textAlign: "center", padding: "0 8px" },
  resultLbl:  { fontSize: 11, color: "#666", marginBottom: 4 },
  resultVal:  (color) => ({ fontSize: 15, fontWeight: 700, color }),

  /* pending */
  pendingGrid: { display: "grid", gridTemplateColumns: "1fr 1px 1fr" },
  badge: (bg, color) => ({
    display: "inline-block",
    fontSize: 11,
    fontWeight: 600,
    padding: "3px 10px",
    borderRadius: 999,
    background: bg,
    color,
    marginBottom: "0.75rem",
  }),
  hint: { fontSize: 13, color: "#555", marginTop: "0.75rem" },
  learn: { fontSize: 13, color: "#777", lineHeight: 1.6, marginTop: "0.75rem" },
  settledRow: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 12,
    color: "#555",
    marginTop: "0.75rem",
  },
  settleSq: { width: 12, height: 12, border: "1.5px solid #444", borderRadius: 3 },
  meta: { fontSize: 12, color: "#555", textAlign: "center", marginTop: "0.5rem" },
};

export default function DailyQuestion() {
  const [market, setMarket]   = useState(null);
  const [answer, setAnswer]   = useState(loadAnswer());
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    fetchDailyMarket()
      .then((d) => { setMarket(d.market); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, []);

  useEffect(() => {
    if (!answer || !market) return;
    if (market.status === "finalized" || market.result) {
      setResult(market.result);
      return;
    }
    fetchMarketResult(answer.ticker)
      .then((d) => { if (d.market?.result) setResult(d.market.result); })
      .catch(() => {});
  }, [answer, market]);

  function handleAnswer(choice) {
    const saved = saveAnswer({
      ticker: market.ticker,
      choice,
      probability: market.probability,
      title: market.title,
    });
    setAnswer(saved);
  }

  /* ── States ─────────────────────────────────────────────────────────────── */

  if (loading)
    return <div style={{ ...S.card, color: "#777", fontSize: 14 }}>Selecting today's question…</div>;

  if (error)
    return <div style={{ ...S.card, color: "#f87171", fontSize: 14 }}>⚠ {error}</div>;

  if (!market)
    return <div style={{ ...S.card, color: "#777", fontSize: 14 }}>No question available today. Check back later.</div>;

  const prob = formatProbability(market.probability);

  /* ── Result ─────────────────────────────────────────────────────────────── */
  if (result && answer) {
    const correct = answer.choice === result;
    return (
      <div style={S.card}>
        <div style={S.labelRow}>
          <span style={S.dot} />
          Yesterday's Result
        </div>
        <p style={S.question}>{market.title}</p>
        <hr style={S.divider} />
        <div style={S.resultGrid}>
          <div style={S.resultCol}>
            <div style={S.resultLbl}>You said</div>
            <div style={S.resultVal(correct ? "#4ade80" : "#f87171")}>{answer.choice}</div>
          </div>
          <div style={S.resultSep} />
          <div style={S.resultCol}>
            <div style={S.resultLbl}>Market was</div>
            <div style={S.resultVal("#fff")}>{prob} YES</div>
          </div>
          <div style={S.resultSep} />
          <div style={S.resultCol}>
            <div style={S.resultLbl}>Result</div>
            <div style={S.resultVal(correct ? "#4ade80" : "#f87171")}>{result}</div>
            <div style={{ fontSize: 11, color: correct ? "#4ade80" : "#f87171", marginTop: 2 }}>
              {correct ? "You were right!" : "Not quite"}
            </div>
          </div>
        </div>
        <div style={S.settledRow}>
          <span style={S.settleSq} />
          Market settled
        </div>
        <p style={S.learn}>
          {correct
            ? "Your instinct aligned with the market. Markets aggregate information from many people—when you agree, you're likely drawing on similar signals."
            : "The market leaned your way but the outcome differed. Probability isn't certainty—even a 57% market resolves NO almost half the time."}
        </p>
      </div>
    );
  }

  /* ── Pending ────────────────────────────────────────────────────────────── */
  if (answer) {
    return (
      <div style={S.card}>
        <div style={S.labelRow}>
          <span style={S.dot} />
          Today's Probability
        </div>
        <div style={S.badge("rgba(74,222,128,0.12)", "#4ade80")}>Answer locked in</div>
        <p style={S.question}>{market.title}</p>
        <hr style={S.divider} />
        <div style={S.pendingGrid}>
          <div style={S.resultCol}>
            <div style={S.resultLbl}>You said</div>
            <div style={S.resultVal("#4ade80")}>{answer.choice}</div>
          </div>
          <div style={S.resultSep} />
          <div style={S.resultCol}>
            <div style={S.resultLbl}>Market says</div>
            <div style={S.resultVal("#fff")}>{prob} YES</div>
          </div>
        </div>
        <p style={S.hint}>Check back tomorrow to see the result.</p>
      </div>
    );
  }

  /* ── Unanswered ─────────────────────────────────────────────────────────── */
  return (
    <div style={S.card}>
      <div style={S.labelRow}>
        <span style={S.dot} />
        Today's Probability
      </div>
      <p style={S.question}>{market.title}</p>

      <div style={S.barBg}>
        <div style={{ ...S.barFill, width: `${market.probability}%` }} />
      </div>
      <p style={S.probLabel}>
        Market says <strong style={{ color: "#fff" }}>{prob} YES</strong>
      </p>

      <hr style={S.divider} />

      <button style={S.voteBtn(false, "yes")} onClick={() => handleAnswer("YES")}>
        <div style={S.voteBtnTitle}>YES</div>
        <div style={S.voteBtnSub}>It will happen</div>
      </button>
      <button style={S.voteBtn(false, "no")} onClick={() => handleAnswer("NO")}>
        <div style={S.voteBtnTitle}>NO</div>
        <div style={S.voteBtnSub}>It won't happen</div>
      </button>

      <div style={S.onceNote}>
        <span style={S.onceSq} />
        You can only answer once per day
      </div>

      <p style={S.meta}>
        {market.volume.toLocaleString()} trades · {market.hours_until_close}h left
      </p>
    </div>
  );
}
