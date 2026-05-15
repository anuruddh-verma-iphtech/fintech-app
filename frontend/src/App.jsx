import ProbabilityTicker from "./components/ProbabilityTicker";
import DailyQuestion from "./components/DailyQuestion";
import "./App.css";

export default function App() {
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric",
  });

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Probability Daily</h1>
        <p className="app-date">{today}</p>
      </header>

      <main className="app-main">
        <section className="section">
          <h2 className="section-label">Live markets</h2>
          <ProbabilityTicker />
        </section>

        <section className="section">
          <h2 className="section-label">Today's question</h2>
          <DailyQuestion />
        </section>
      </main>

      <footer className="app-footer">
        <p>Powered by <a href="https://kalshi.com" target="_blank" rel="noreferrer">Kalshi</a> · No login required</p>
      </footer>
    </div>
  );
}
