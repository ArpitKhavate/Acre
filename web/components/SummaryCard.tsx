"use client";

import { useState } from "react";
import { api, Report } from "@/lib/api";

// AI summary card with the health score above it (PRD 10.3).
export function SummaryCard({
  farmId,
  initial,
  farmScore,
}: {
  farmId: string;
  initial: Report;
  farmScore: number | null;
}) {
  const [report, setReport] = useState<Report>(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function regenerate() {
    setBusy(true);
    setError(null);
    try {
      const r = await api.generateReport(farmId);
      setReport({
        period: "daily",
        health_score: r.health_score,
        ai_summary: r.ai_summary,
        generated_at: new Date().toISOString(),
      });
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  const score = report?.health_score ?? farmScore;
  const color = score == null ? "gray" : score >= 80 ? "green" : score >= 50 ? "amber" : "red";

  return (
    <div className="card">
      <h2>AI summary</h2>
      <div className="farm-score">
        <span className={`dot ${color}`} style={{ width: 16, height: 16, marginRight: 10 }} />
        {score != null ? Math.round(score) : "—"}
        <small> / 100 farm health</small>
      </div>
      <p className="summary">
        {report?.ai_summary ?? "No report yet — generate one from the latest scans."}
      </p>
      <button className="btn" onClick={regenerate} disabled={busy}>
        {busy ? "Generating…" : "Regenerate report"}
      </button>
      {error && <p className="error">{error}</p>}
      {report?.generated_at && (
        <p className="muted" style={{ fontSize: 12, marginTop: 10 }}>
          Updated {new Date(report.generated_at).toLocaleString()}
        </p>
      )}
    </div>
  );
}
