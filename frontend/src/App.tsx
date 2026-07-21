import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { FleetOverview } from "./pages/FleetOverview";
import { DriveDetails } from "./pages/DriveDetails";
import { PredictionExplorer } from "./pages/PredictionExplorer";
import { Chat } from "./pages/Chat";
import { Metrics } from "./pages/Metrics";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<FleetOverview />} />
        <Route path="drives" element={<DriveDetails />} />
        <Route path="predictions" element={<PredictionExplorer />} />
        <Route path="chat" element={<Chat />} />
        <Route path="metrics" element={<Metrics />} />
      </Route>
    </Routes>
  );
}
