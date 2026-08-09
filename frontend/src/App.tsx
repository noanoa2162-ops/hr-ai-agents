import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./App.css";

const CandidatePage = lazy(() => import("./pages/CandidatePage"));
const HRDashboard = lazy(() => import("./pages/HRDashboard"));
const CandidateDetails = lazy(() => import("./components/CandidateDetails"));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div style={{ padding: 40, textAlign: "center" }}>טוען...</div>}>
        <Routes>
          <Route path="/" element={<CandidatePage />} />
          <Route path="/dashboard" element={<HRDashboard />} />
          <Route path="/candidate/:id" element={<CandidateDetails />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
export default App;
