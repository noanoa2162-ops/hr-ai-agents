import { useState, useEffect } from "react";
import CandidatesTable from "../components/CandidatesTable";
import { fetchCandidatesList, type CandidateResponse } from "../services/candidatesService";

export default function HRDashboard() {
  const [candidates, setCandidates] = useState<CandidateResponse[]>([]);
  const [adminKey, setAdminKey] = useState(
    () => sessionStorage.getItem("candidatesAdminKey") || "",
  );
  const [draftKey, setDraftKey] = useState(adminKey);
  const [loading, setLoading] = useState(Boolean(adminKey));
  const [error, setError] = useState("");

  useEffect(() => {
    if (!adminKey) return;

    const load = async () => {
      try {
        const data = await fetchCandidatesList(adminKey);
        setCandidates(data);
        setError("");
      } catch (err) {
        setError(err instanceof Error ? err.message : "שגיאה");
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [adminKey]);

  if (!adminKey) {
    return (
      <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "var(--bg)" }}>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const normalizedKey = draftKey.trim();
            if (!normalizedKey) return;
            sessionStorage.setItem("candidatesAdminKey", normalizedKey);
            setLoading(true);
            setAdminKey(normalizedKey);
          }}
          style={{ width: 340, padding: 28, borderRadius: 12, background: "var(--card)", boxShadow: "var(--shadow-sm)" }}
        >
          <h1 style={{ fontSize: 22, marginTop: 0 }}>גישת מנהל</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>יש להזין קוד מנהל כדי לצפות בפרטי מועמדים.</p>
          <input
            type="password"
            value={draftKey}
            onChange={(event) => setDraftKey(event.target.value)}
            autoComplete="off"
            style={{ width: "100%", boxSizing: "border-box", padding: 10, marginBottom: 12 }}
          />
          <button type="submit" style={{ width: "100%", padding: 10, cursor: "pointer" }}>כניסה</button>
        </form>
      </div>
    );
  }

  const tableData = candidates.map((c) => ({
    name: c.analysis.dashboard_view.full_name,
    phone: c.analysis.dashboard_view.phone,
    email: c.analysis.dashboard_view.email,
    profile: c.analysis.dashboard_view.status || "מועמד",
    score: Math.round(c.analysis.dashboard_view.match_percent * 10),
  }));

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", padding: "40px 20px" }}>
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--primary)", margin: 0 }}>דאשבורד HR</h1>
            <p style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 2 }}>כל המועמדים שנותחו</p>
          </div>
          <span style={{ fontSize: 14, color: "var(--text-secondary)" }}>
            {candidates.length} מועמדים
          </span>
          <button
            onClick={() => {
              sessionStorage.removeItem("candidatesAdminKey");
              setAdminKey("");
              setDraftKey("");
              setCandidates([]);
            }}
          >
            יציאה
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: "center", padding: 60 }}>
            <div className="spinner" />
            <style>{`.spinner{width:40px;height:40px;border:3px solid var(--border);border-top-color:var(--primary);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto}@keyframes spin{to{transform:rotate(360deg)}}`}</style>
          </div>
        )}

        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: 14, color: "#b91c1c", fontSize: 14 }}>
            {error}
          </div>
        )}

        {!loading && !error && <CandidatesTable data={tableData} rawData={candidates} />}
      </div>
    </div>
  );
}
