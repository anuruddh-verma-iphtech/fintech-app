# Kalshi Daily Probability App

Teach probability using real Kalshi prediction market data.  
No login. No backend account needed. Just open and learn.

---

## Project Structure

```
kalshi-app/
├── backend/          # Python FastAPI proxy
│   ├── main.py
│   └── requirements.txt
└── frontend/         # React JS app
    ├── package.json
    └── src/
        ├── App.jsx
        ├── App.css
        ├── components/
        │   ├── ProbabilityTicker.jsx
        │   └── DailyQuestion.jsx
        └── utils/
            ├── api.js
            └── storage.js
```

---

## Setup

### 1. Backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API runs at: http://localhost:8000

Endpoints:
- GET /health
- GET /markets/ticker   → 3–5 live markets for the ticker
- GET /markets/daily    → today's daily question
- GET /markets/{ticker} → single market result

### 2. Frontend (JavaScript / React)

```bash
cd frontend
npm install
npm start
```

App runs at: http://localhost:3000

The `"proxy": "http://localhost:8000"` in package.json routes
/markets/* calls to the FastAPI backend automatically.

---

## How It Works

### Core Loop
Observe → Predict → Compare → Learn

### Live Ticker
- Fetches 3–5 open markets closing within 48h
- Filters: volume ≥ 100, probability 10–90%
- Rotates through markets every 4 seconds
- Color-coded by category (weather/sports/finance)

### Daily Question
- Rotates by day: Mon/Thu=Finance, Tue/Fri/Sat=Sports, Wed/Sun=Weather
- Filters: closes within 24h, volume ≥ 500 (fallback 100), probability 20–80%
- Ranked by: highest volume → soonest close → shortest title
- Fallback chain: sports → weather → finance → any

### Answer Storage
- Stored in localStorage (no server, no login)
- Locked after answer — shows pending state
- Next day: fetches result from Kalshi and compares

---

## Environment Variables

Create `frontend/.env`:
```
REACT_APP_BACKEND_URL=http://localhost:8000
```

---

## Tech Stack

| Layer    | Technology        |
|----------|-------------------|
| Frontend | React 18, CSS     |
| Backend  | Python, FastAPI   |
| API      | Kalshi Trade API  |
| Storage  | localStorage      |
| Auth     | None              |
# fintech-app
