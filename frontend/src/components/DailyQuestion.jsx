import { useEffect, useState } from "react";
import {
  fetchDailyMarket,
  fetchMarketResult,
  formatProbability,
} from "../utils/api";
import { loadAnswer, saveAnswer } from "../utils/storage";

export default function DailyQuestion() {
  const [market, setMarket] = useState(null);
  const [answer, setAnswer] = useState(loadAnswer());
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDailyMarket()
      .then((d) => {
        setMarket(d.market);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!answer || !market) return;
    if (market.status === "finalized" || market.result) {
      setResult(market.result);
      return;
    }
    fetchMarketResult(answer.ticker)
      .then((d) => {
        if (d.market?.result) setResult(d.market.result);
      })
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

  if (loading)
    return <div className="dq-loading">Selecting today's question…</div>;
  if (error) return <div className="dq-error">⚠ {error}</div>;
  if (!market)
    return (
      <div className="dq-empty">
        No question available today. Check back later.
      </div>
    );

  const prob = formatProbability(market.probability);

  if (result && answer) {
    const correct = answer.choice === result;
    return (
      <div className="dq-card dq-result">
        <div className={`result-badge ${correct ? "correct" : "incorrect"}`}>
          {correct ? "✓ You got it!" : "✗ Not quite"}
        </div>
        <p className="dq-question">{market.title}</p>
        <div className="dq-meta-row">
          <span>
            You said: <strong>{answer.choice}</strong>
          </span>
          <span>
            Market: <strong>{prob} YES</strong>
          </span>
          <span>
            Result: <strong>{result}</strong>
          </span>
        </div>
        <p className="dq-learn">
          {correct
            ? "Your instinct aligned with the market. Markets aggregate information from many people—when you agree, you're likely drawing on similar signals."
            : "The market leaned your way but the outcome differed. Probability isn't certainty—even a 57% market resolves NO almost half the time."}
        </p>
      </div>
    );
  }

  if (answer) {
    return (
      <div className="dq-card dq-pending">
        <div className="pending-badge">Answer locked in</div>
        <p className="dq-question">{market.title}</p>
        <div className="dq-meta-row">
          <span>
            You said: <strong>{answer.choice}</strong>
          </span>
          <span>
            Market says: <strong>{prob} YES</strong>
          </span>
        </div>
        <p className="dq-hint">Check back tomorrow to see the result.</p>
      </div>
    );
  }

  return (
    <div className="dq-card">
      <div className="dq-category-tag">{market.category}</div>
      <p className="dq-question">{market.title}</p>
      <div className="dq-market-prob">
        <span className="prob-label">Market says</span>
        <span className="prob-value">{prob} YES</span>
      </div>
      <div className="dq-prob-bar">
        <div
          className="prob-fill"
          style={{ width: `${market.probability}%` }}
        />
      </div>
      <div className="dq-actions">
        <button className="btn-yes" onClick={() => handleAnswer("YES")}>
          YES
        </button>
        <button className="btn-no" onClick={() => handleAnswer("NO")}>
          NO
        </button>
      </div>
      <p className="dq-volume">
        {market.volume.toLocaleString()} trades · {market.hours_until_close}h
        left
      </p>
    </div>
  );
}
