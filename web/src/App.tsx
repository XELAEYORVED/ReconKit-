import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { CompareView } from "./components/CompareView";
import { History } from "./pages/History";
import { Home } from "./pages/Home";
import { Results } from "./pages/Results";
import { Scan } from "./pages/Scan";
import { Settings } from "./pages/Settings";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/scan" element={<Scan />} />
        <Route path="/scan/:id" element={<Scan />} />
        <Route path="/results/:id" element={<Results />} />
        <Route path="/history" element={<History />} />
        <Route path="/compare" element={<CompareView />} />
        <Route path="/compare/:a/:b" element={<CompareView />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
