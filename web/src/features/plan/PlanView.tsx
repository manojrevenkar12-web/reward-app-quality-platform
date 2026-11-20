/** Plan a release: the changes in it, then where the tests and the exploratory hours go. */
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { type ApiError, post, useResource } from "../../shared/api";
import { FLOW, one, pct } from "../../shared/format";
import type { Catalogue, PlanOut } from "../../shared/types";
import { EmptyState, ErrorState, Skeleton } from "../../shared/ui/states";
import { motionTokens } from "../../theme/motion";

type Row = { module: string; lines: number; api_change: boolean; new_author: boolean };

const START: Row[] = [
  { module: "payout_service", lines: 640, api_change: true, new_author: true },
  { module: "event_ui", lines: 120, api_change: false, new_author: false },
  { module: "settings_ui", lines: 40, api_change: false, new_author: false },
];

export function PlanView() {
  const cat = useResource<Catalogue>("/api/catalogue");
  const [rows, setRows] = useState<Row[]>(START);
  const [plan, setPlan] = useState<PlanOut | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const run = async (rs: Row[]) => {
    setRunning(true);
    setFailure(null);
    try {
      setPlan(await post<PlanOut>("/api/plan", { changes: rs }));
    } catch (e) {
      setPlan(null);
      setFailure((e as ApiError).message);
    } finally {
      setRunning(false);
    }
  };
  useEffect(() => {
    void run(START);
  }, []);

  if (cat.loading) return <Skeleton label="Loading the module catalogue" rows={5} />;
  if (cat.error || !cat.data) return <ErrorState error={cat.error!} retry={cat.retry} what="the module catalogue" />;
  const modules = cat.data.modules;
  const side = (m: string) => modules.find((x) => x.name === m)?.side ?? "app";
  const set = (i: number, patch: Partial<Row>) => setRows(rows.map((r, k) => (k === i ? { ...r, ...patch } : r)));
  const maxRisk = plan ? Math.max(...Object.values(plan.flows), 0.0001) : 1;

  return (
    <div className="flex flex-col gap-6">
      <section className="flex max-w-hero flex-col gap-3">
        <h1 className="text-title font-bold">Plan a release</h1>
        <p className="max-w-prose">
          List what the release changes. The planner scores each change, ranks the flows it puts at risk, picks the device matrix and the exploratory
          hours, and names the contract suites that must pass before the backend deploys.
        </p>
      </section>
      <section aria-labelledby="changes" className="flex flex-col gap-4 rounded-card bg-sheet p-5">
        <h2 id="changes" className="text-lead font-bold">Changes in this release</h2>
        {rows.length === 0 ? (
          <EmptyState title="No changes yet">Add the modules this release touches.</EmptyState>
        ) : (
          <ul className="flex flex-col gap-3">
            {rows.map((r, i) => (
              <li key={i} className="grid items-end gap-3 sm:grid-cols-[1.4fr_0.6fr_auto_auto_auto]">
                <label className="flex flex-col gap-1 text-small font-semibold text-ink">
                  Module
                  <select value={r.module} onChange={(e) => set(i, { module: e.target.value })} className="rounded-soft border border-line bg-ground px-3 py-2 font-code font-normal">
                    {modules.map((m) => (
                      <option key={m.name} value={m.name}>{m.name} ({m.side})</option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-1 text-small font-semibold text-ink">
                  Lines changed
                  <input type="number" min={1} value={r.lines} onChange={(e) => set(i, { lines: Math.max(1, Number(e.target.value) || 1) })}
                    className="rounded-soft border border-line bg-ground px-3 py-2 font-normal" />
                </label>
                <label className={`flex items-center gap-2 pb-2 text-small ${side(r.module) === "app" ? "text-muted" : "text-copy"}`}>
                  <input type="checkbox" checked={r.api_change} disabled={side(r.module) === "app"} onChange={(e) => set(i, { api_change: e.target.checked })} />
                  Changes the API
                </label>
                <label className="flex items-center gap-2 pb-2 text-small">
                  <input type="checkbox" checked={r.new_author} onChange={(e) => set(i, { new_author: e.target.checked })} />
                  Author new to it
                </label>
                <button type="button" onClick={() => setRows(rows.filter((_, k) => k !== i))} className="pb-2 text-small font-semibold text-muted hover:text-bad">
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="flex flex-wrap gap-3">
          <button type="button" onClick={() => setRows([...rows, { module: modules[0]!.name, lines: 100, api_change: false, new_author: false }])}
            className="rounded-pill border border-line px-4 py-2 font-semibold hover:border-ink">
            Add a change
          </button>
          <button type="button" disabled={running || rows.length === 0} onClick={() => run(rows)} className="rounded-pill bg-ink px-5 py-2 font-semibold text-sheet disabled:opacity-60">
            {running ? "Planning…" : "Plan this release"}
          </button>
        </div>
        {failure && <p role="alert" className="rounded-soft border border-bad bg-badWash p-3 text-bad">{failure}</p>}
      </section>
      <AnimatePresence mode="wait">
        {plan && (
          <motion.div key={JSON.stringify(plan.flows)} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            transition={{ duration: motionTokens.quick * 2, ease: motionTokens.ease }} className="grid gap-5 lg:grid-cols-2">
            <section aria-labelledby="flows" className="flex flex-col gap-3 rounded-card bg-sheet p-5">
              <h2 id="flows" className="text-lead font-bold">Flows at risk</h2>
              <ol className="flex flex-col gap-2">
                {Object.entries(plan.flows).map(([f, v]) => (
                  <li key={f} className="grid grid-cols-[9rem_1fr_3.5rem] items-center gap-3 text-small">
                    <span className="font-semibold text-ink">{FLOW[f] ?? f}</span>
                    <span className="h-2 rounded-pill bg-line" aria-hidden>
                      <span className="block h-2 rounded-pill bg-focus" style={{ width: `${(v / maxRisk) * 100}%` }} />
                    </span>
                    <span className="text-right">{pct(v, 1)}</span>
                  </li>
                ))}
              </ol>
              <p className="text-small text-muted">Chance that some change touching the flow carries a defect. Scored with the {plan.model}.</p>
            </section>
            <section aria-labelledby="where" className="flex flex-col gap-4 rounded-card bg-sheet p-5">
              <h2 id="where" className="text-lead font-bold">Where the testing goes</h2>
              <div>
                <h3 className="text-small font-bold">Exploratory hours</h3>
                <p className="text-small">{Object.entries(plan.exploratory).map(([f, h]) => `${FLOW[f] ?? f} ${one(h)} h`).join(" · ") || "None"}</p>
              </div>
              <div>
                <h3 className="text-small font-bold">Device matrix: {plan.devices.length} classes, {pct(plan.device_share)} of players</h3>
                <ul className="mt-1 flex flex-wrap gap-2">
                  {plan.devices.map((d) => (
                    <li key={d.name} className="rounded-pill bg-ground px-3 py-1 font-code text-small">{d.name}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-small font-bold">Contract suites that must pass</h3>
                <p className="font-code text-small">{plan.contracts.join(", ") || "None: no backend change"}</p>
              </div>
              <div>
                <h3 className="text-small font-bold">Rollout</h3>
                <p className="text-small">{plan.rollout.map(([s, h]) => (h ? `${pct(s)} for ${h} h` : `${pct(s)}`)).join(", then ")}, halted by guardrails on a real excess.</p>
              </div>
            </section>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
