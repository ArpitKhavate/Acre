"use client";

import { TreatmentRow } from "@/lib/api";

// Pesticide summary grouped by zone (PRD 10.2).
export function TreatmentTable({ rows }: { rows: TreatmentRow[] }) {
  if (!rows.length) {
    return <p className="muted">No treatments needed — all scanned plants healthy.</p>;
  }
  const sorted = [...rows].sort((a, b) => a.zone_id.localeCompare(b.zone_id));
  return (
    <table>
      <thead>
        <tr>
          <th>Zone</th>
          <th>Finding</th>
          <th>Count</th>
          <th>Conf.</th>
          <th>Pesticide</th>
          <th>Organic</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((r, i) => (
          <tr key={`${r.zone_id}-${r.class_name}-${i}`}>
            <td><span className="pill">{r.zone_id}</span></td>
            <td>{r.class_name.replaceAll("___", " · ")}</td>
            <td>{r.count}</td>
            <td>{(r.max_conf * 100).toFixed(0)}%</td>
            <td>{r.treatment?.pesticide_name ?? "—"}</td>
            <td className="muted">{r.treatment?.organic_alternative ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
