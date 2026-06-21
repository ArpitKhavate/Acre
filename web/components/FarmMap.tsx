"use client";

import { Zone } from "@/lib/api";

const COLORS: Record<string, string> = {
  green: "var(--green)",
  amber: "var(--amber)",
  red: "var(--red)",
  gray: "var(--gray)",
};

// Schematic SVG map from normalized zone coordinates (PRD 10.1).
// Logical layout, not satellite imagery — deliberate given no GPS hardware.
export function FarmMap({ zones }: { zones: Zone[] }) {
  const W = 460;
  const H = 320;
  const R = 34;
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Farm map">
        <rect x="0" y="0" width={W} height={H} rx="10" fill="#10180f" />
        {zones.map((z) => {
          const cx = z.map_x * W;
          const cy = z.map_y * H;
          return (
            <g key={z.zone_id}>
              <circle
                cx={cx}
                cy={cy}
                r={R}
                fill={COLORS[z.color] ?? COLORS.gray}
                opacity={0.85}
              />
              <text x={cx} y={cy - 2} textAnchor="middle" fontSize="13"
                    fontWeight="700" fill="#07120b">
                {z.zone_id}
              </text>
              <text x={cx} y={cy + 13} textAnchor="middle" fontSize="10"
                    fill="#07120b">
                {z.score != null ? z.score : "—"}
              </text>
              <text x={cx} y={cy + R + 14} textAnchor="middle" fontSize="10"
                    fill="var(--muted)">
                {z.crop_type ?? ""}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="legend">
        <span><i className="dot green" /> healthy ≥80</span>
        <span><i className="dot amber" /> watch 50–79</span>
        <span><i className="dot red" /> treat &lt;50</span>
        <span><i className="dot gray" /> no data</span>
      </div>
    </div>
  );
}
