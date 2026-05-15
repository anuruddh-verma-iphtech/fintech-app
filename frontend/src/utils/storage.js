const STORAGE_KEY = "kalshi_daily_answer";

export function getTodayKey() {
  return new Date().toISOString().split("T")[0];
}

export function saveAnswer({ ticker, choice, probability, title }) {
  const entry = {
    ticker,
    choice,
    probability,
    title,
    date: getTodayKey(),
    savedAt: new Date().toISOString(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entry));
  return entry;
}

export function loadAnswer() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const entry = JSON.parse(raw);
    if (entry.date !== getTodayKey()) return null;
    return entry;
  } catch {
    return null;
  }
}

export function clearAnswer() {
  localStorage.removeItem(STORAGE_KEY);
}

export function getUserId() {
  let id = localStorage.getItem("kalshi_user_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("kalshi_user_id", id);
  }
  return id;
}
