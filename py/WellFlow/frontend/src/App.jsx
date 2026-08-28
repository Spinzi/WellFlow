import Dashboard from "./pages/Dashboard";
import { useArduinoState } from "./state/useArduinoState";

export default function App() {
  const { wsStatus, arduinoState, sendCommand, pendingCommandKeys } = useArduinoState();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__title">
          <div className="app-header__mark">
            <DropIcon />
          </div>
          <div>
            <h1 className="app-header__name">WellFlow</h1>
            <p className="app-header__sub">Water monitoring &amp; control dashboard</p>
          </div>
        </div>
      </header>

      <Dashboard
        wsStatus={wsStatus}
        arduinoState={arduinoState}
        sendCommand={sendCommand}
        pendingCommandKeys={pendingCommandKeys}
      />

      <footer className="app-footer">WellFlow — Raspberry Pi bridge dashboard</footer>
    </div>
  );
}

function DropIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path
        d="M12 3s7 7.4 7 12a7 7 0 11-14 0c0-4.6 7-12 7-12z"
        stroke="var(--color-on-accent)"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  );
}
