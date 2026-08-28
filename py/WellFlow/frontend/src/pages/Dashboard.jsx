import ConnectionCard from "../components/ConnectionCard";
import SensorsCard from "../components/SensorsCard";
import OutputsCard from "../components/OutputsCard";
import SystemCard from "../components/SystemCard";
import ControlsCard from "../components/ControlsCard";

export default function Dashboard({ wsStatus, arduinoState, sendCommand, pendingCommandKeys }) {
  return (
    <div className="dashboard-grid">
      <div className="col-4">
        <ConnectionCard arduinoState={arduinoState} wsStatus={wsStatus} />
      </div>
      <div className="col-4">
        <SensorsCard data={arduinoState.data} />
      </div>
      <div className="col-4">
        <OutputsCard data={arduinoState.data} />
      </div>
      <div className="col-8">
        <SystemCard arduinoState={arduinoState} />
      </div>
      <div className="col-4">
        <ControlsCard
          arduinoState={arduinoState}
          sendCommand={sendCommand}
          pendingCommandKeys={pendingCommandKeys}
        />
      </div>
    </div>
  );
}
