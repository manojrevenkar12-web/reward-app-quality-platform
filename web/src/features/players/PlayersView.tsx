import { ORDER, eur, int, one } from "../../shared/format";
import type { DesignSummary } from "../../shared/types";
import { DesignTable } from "../../shared/ui/DesignTable";
import { ErrorState, Gate, Skeleton } from "../../shared/ui/states";
import { useResults } from "../../shared/useResults";
import { PlayerBars } from "./PlayerBars";

export function PlayersView() {
  const { data, error, loading, retry } = useResults();
  if (loading) return <Skeleton label="Loading the evaluation" rows={10} />;
  if (error || !data) return <ErrorState error={error!} retry={retry} what="the evaluation" />;
  const r = data.heldout ?? data.dev;
  const d = r.designs;
  const rows = ORDER.filter((n) => d[n]).map((n) => [n, d[n]!] as [string, DesignSummary]);
  const a = d.as_found!;
  const p = d.platform!;
  const w = r.world;
  return (
    <div className="flex flex-col gap-7">
      <section className="flex max-w-hero flex-col gap-4">
        <h1 className="text-hero font-bold">
          {int(p.player_days_per_week)} player-days hit by bugs a week, against {int(a.player_days_per_week)} as found
        </h1>
        <p className="max-w-prose text-lead">
          {w.orgs} simulated app teams, {w.weeks} weeks each, {int(w.dau)} daily players: {w.releases} releases with {w.defects} defects, the same for
          every design. A player-day is one player meeting a bug on one day. The platform finds {p.found_before_release} of {p.defects} defects
          before release (as found: {a.found_before_release}) and costs {eur(p.cost_eur_per_week)} a week in lost player value, QA time and devices,
          against {eur(a.cost_eur_per_week)}.
        </p>
        <div className="flex flex-wrap gap-4">
          <Gate fails={data.gate.dev} what="Development orgs" />
          <Gate fails={data.gate.heldout} what="Held-out orgs" />
        </div>
        <p className="text-small text-muted">{data.heldout ? "Showing the held-out orgs, run once." : "Showing the development orgs; the held-out run has not happened yet."}</p>
      </section>
      <section aria-labelledby="bars" className="flex flex-col gap-4 rounded-card bg-sheet p-5">
        <h2 id="bars" className="text-title font-bold">Player-days hit a week, by design</h2>
        <p className="text-small text-muted">Line: 95% interval over org-weeks. Each grey design is the platform with one part taken away.</p>
        <PlayerBars rows={rows} />
      </section>
      <DesignTable
        title="What each design costs a week"
        rows={rows}
        columns={[
          { label: "Lost player value", value: (x) => eur(x.player_eur_per_week) },
          { label: "QA hours", value: (x) => one(x.qa_hours_per_week) },
          { label: "Engineering hours", value: (x) => one(x.eng_hours_per_week) },
          { label: "Device farm", value: (x) => eur(x.device_eur_per_week) },
          { label: "Total", value: (x) => eur(x.cost_eur_per_week) },
        ]}
      />
    </div>
  );
}
