import { api, FarmMap as FarmMapData, Report, TreatmentRow } from "@/lib/api";
import { FarmMap } from "@/components/FarmMap";
import { TreatmentTable } from "@/components/TreatmentTable";
import { SummaryCard } from "@/components/SummaryCard";

const FARM_ID = process.env.NEXT_PUBLIC_ACRE_FARM ?? "demo-farm-1";

export default async function Page() {
  let map: FarmMapData | null = null;
  let treatments: TreatmentRow[] = [];
  let report: Report = null;
  let apiError: string | null = null;

  try {
    map = await api.farmMap(FARM_ID);
    treatments = (await api.treatments(FARM_ID)).rows;
    report = (await api.latestReport(FARM_ID)).report;
  } catch (e) {
    apiError = String(e);
  }

  return (
    <div className="wrap">
      <header className="app">
        <h1>Acre</h1>
        <span className="tag">offline-first handheld plant scanner</span>
      </header>
      <p className="subtitle">
        Farm <strong>{FARM_ID}</strong> · scores computed on-device, the red/green
        LED is the spray signal · this dashboard is the cloud report.
      </p>

      {apiError && (
        <div className="card" style={{ marginBottom: 20 }}>
          <p className="error">Could not reach the Acre API ({apiError}).</p>
          <p className="muted">
            Start it with <code>uvicorn cloud.app.main:app --port 8000</code> and
            seed via <code>python -m cloud.seed</code>.
          </p>
        </div>
      )}

      <div className="grid">
        <div className="card">
          <h2>Farm map</h2>
          {map ? <FarmMap zones={map.zones} /> : <p className="muted">No map data.</p>}
        </div>
        <SummaryCard farmId={FARM_ID} initial={report} farmScore={map?.farm_score ?? null} />
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2>Treatments needed by zone</h2>
        <TreatmentTable rows={treatments} />
      </div>
    </div>
  );
}
