import { ORDER, eur, one, pct } from "../../shared/format";
import type { DesignSummary } from "../../shared/types";
import { DesignTable } from "../../shared/ui/DesignTable";
import { ErrorState, Skeleton } from "../../shared/ui/states";
import { useResults } from "../../shared/useResults";

export function ReleaseView() {
  const { data, error, loading, retry } = useResults();
  if (loading) return <Skeleton label="Loading release testing" />;
  if (error || !data) return <ErrorState error={error!} retry={retry} what="release testing" />;
  const r = data.heldout ?? data.dev;
  const d = r.designs;
  const rows = ORDER.filter((n) => d[n]).map((n) => [n, d[n]!] as [string, DesignSummary]);
  const p = d.platform!;
  const a = d.as_found!;
  const e = d.automate_everything!;
  return (
    <div className="flex flex-col gap-6">
      <section className="flex max-w-hero flex-col gap-3">
        <h1 className="text-title font-bold">
          {pct(p.found_share)} of defects found before release, with {one(p.qa_hours_per_week)} QA hours a week instead of {one(a.qa_hours_per_week)}
        </h1>
        <p className="max-w-prose">
          As found, four people run a manual checklist on the four most popular phones. Automating every test on all 15 device classes finds
          {" "}{pct(e.found_share)}: end-to-end tests miss layout and coin-balance bugs a person sees. The platform runs end-to-end tests on a device
          matrix that covers every maker and Android version many players use, adds contract tests between app and backend and a check that every
          coin balance equals its ledger, and spends its exploratory hours where a model of the team&apos;s own history puts the risk.
        </p>
      </section>
      <DesignTable
        title="Before release"
        rows={rows}
        columns={[
          { label: "Found before release", value: (x) => `${x.found_before_release} of ${x.defects}` },
          { label: "Device classes", value: (x) => one(x.devices_tested) },
          { label: "QA hours a week", value: (x) => one(x.qa_hours_per_week) },
          { label: "Flaky failures a week", value: (x) => one(x.flaky_failures_per_week) },
          { label: "Device farm a week", value: (x) => eur(x.device_eur_per_week) },
          { label: "Freeze to every player (h)", value: (x) => one(x.lead_hours_median), note: "Median hours from code freeze to 100% rollout" },
        ]}
      />
    </div>
  );
}
