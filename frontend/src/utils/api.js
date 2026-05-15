const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

export async function fetchTickerMarkets() {
  const res = await fetch(`${BACKEND_URL}/markets/ticker`);
  if (!res.ok) throw new Error(`Ticker fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchDailyMarket() {
  const res = await fetch(`${BACKEND_URL}/markets/daily`);
  if (!res.ok) throw new Error(`Daily market fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchMarketResult(ticker) {
  const res = await fetch(`${BACKEND_URL}/markets/${ticker}`);
  if (!res.ok) throw new Error(`Market result fetch failed: ${res.status}`);
  return res.json();
}

export function formatProbability(prob) {
  return `${Math.round(prob)}%`;
}

export function formatTimeLeft(hoursUntilClose) {
  if (hoursUntilClose < 1) {
    return `${Math.round(hoursUntilClose * 60)}m left`;
  }
  return `${Math.round(hoursUntilClose)}h left`;
}
