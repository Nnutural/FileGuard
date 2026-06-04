import { StatusPanel } from "./components/StatusPanel";
import { RiskSummary } from "./components/RiskSummary";
import { AlertTimeline } from "./components/AlertTimeline";
import { ScoreChart } from "./components/ScoreChart";

export default function App() {
  return (
    <div className="app">
      <h1>FileGuard 文件安全风险感知系统</h1>
      <div className="grid">
        <StatusPanel />
        <RiskSummary />
        <AlertTimeline />
        <ScoreChart />
      </div>
    </div>
  );
}
