import { NAME, ORDER, ink, int, one } from "../../shared/format";
import type { DesignSummary } from "../../shared/types";
import { DesignTable } from "../../shared/ui/DesignTable";
import { ErrorState, Skeleton } from "../../shared/ui/states";
import { useResults } from "../../shared/useResults";

const CHANNELS = [
  { key: "guardrail", label: "Rollout guardrail", cls: "bg-part1" },
  { key: "ticket_agent", label: "Ticket agent", cls: "bg-part3" },
  { key: "crash_report", label: "Daily crash check", cls: "bg-part4" },
  { key: "support", label: "Support escalation", cls: "bg-part2" },
  { key: "none", label: "Nobody, within two weeks", cls: "bg-part5" },
] as const;

function Channels({ rows }: { rows: [string, DesignSummary][] }) {
  return (
    <figure className="flex flex-col gap-3">
      <figcaption className="flex flex-wrap gap-x-5 gap-y-2 text-small text-copy sm:pl-[14rem]">
        {CHANNELS.map((c) => (
          <span key={c.key} className="inline-flex items-center gap-2">
            <span className={`inline-block h-swatch w-swatch rounded-soft ${c.cls}`} aria-hidden />
            {c.label}
          </span>
        ))}
      </figcaption>
      <ul className="flex flex-col gap-2">
        {rows.map(([n, d]) => {
          const total = CHANNELS.reduce((s, c) => s + (d.channels[c.key] ?? 0), 0) || 1;
          return (
            <li key={n} className="grid grid-cols-1 items-center gap-1 sm:grid-cols-[13rem_1fr] sm:gap-4">
              <span className={`text-small font-semibold sm:text-right ${ink(n)}`}>{NAME[n] ?? d.label}</span>
              <div className="flex h-bar gap-px overflow-hidden rounded-soft" role="img"
                aria-label={`${NAME[n]}: ${CHANNELS.map((c) => `${c.label.toLowerCase()} ${d.channels[c.key] ?? 0}`).join(", ")}`}>
                {CHANNELS.map((c) => (
                  <div key={c.key} className={c.cls} style={{ width: `${((d.channels[c.key] ?? 0) / total) * 100}%` }} />
                ))}
              </div>
            </li>
          );
        })}
      </ul>
    </figure>
  );
}

export function ProductionView() {
  const { data, error, loading, retry } = useResults();
  if (loading) return <Skeleton label="Loading production" />;
  if (error || !data) return <ErrorState error={error!} retry={retry} what="production" />;
  const r = data.heldout ?? data.dev;
  const d = r.designs;
  const rows = ORDER.filter((n) => d[n]).map((n) => [n, d[n]!] as [string, DesignSummary]);
  const main = ["as_found", "automate_everything", "platform_no_ticket_agent", "platform_no_guardrails", "platform"]
    .filter((n) => d[n]).map((n) => [n, d[n]!] as [string, DesignSummary]);
  const p = d.platform!;
  const a = d.as_found!;
  return (
    <div className="flex flex-col gap-6">
      <section className="flex max-w-hero flex-col gap-3">
        <h1 className="text-title font-bold">
          {p.escaped_money} bugs in coins or cash-outs reached players, against {a.escaped_money}; the rest were found in {one(p.detect_hours_median ?? 0)} hours, not {one(a.detect_hours_median ?? 0)}
        </h1>
        <p className="max-w-prose">
          The platform rolls out to 1%, 10%, 50% then everyone, 12 hours a step. Guardrails compare crashes, failed cash-outs and odd coin balances
          on the new version, per device class, with what that segment normally sees, and halt the rollout on a real excess. A ticket agent reads
          what players write in English, German and French, counts tickets per flow and symptom, and files a bug when a count jumps.
        </p>
      </section>
      <section aria-labelledby="ch" className="flex flex-col gap-4 rounded-card bg-sheet p-5">
        <h2 id="ch" className="text-title font-bold">Who found the bugs that reached players</h2>
        <Channels rows={main} />
      </section>
      <DesignTable
        title="In production"
        rows={rows}
        columns={[
          { label: "Escaped", value: (x) => int(x.escaped) },
          { label: "In coins or cash-outs", value: (x) => int(x.escaped_money) },
          { label: "Hours to find (median)", value: (x) => (x.detect_hours_median == null ? "–" : one(x.detect_hours_median)) },
          { label: "Nobody found", value: (x) => int(x.undetected) },
          { label: "Rollouts halted", value: (x) => `${x.halts} (${x.false_halts} false)` },
          { label: "Guardrail", value: (x) => int(x.channels.guardrail ?? 0) },
          { label: "Ticket agent", value: (x) => int(x.channels.ticket_agent ?? 0) },
          { label: "Support", value: (x) => int(x.channels.support ?? 0) },
          { label: "Crash check", value: (x) => int(x.channels.crash_report ?? 0) },
        ]}
      />
    </div>
  );
}
