import { PlanView } from "./features/plan/PlanView";
import { PlayersView } from "./features/players/PlayersView";
import { ProductionView } from "./features/production/ProductionView";
import { ReleaseView } from "./features/release/ReleaseView";
import { TicketsView } from "./features/tickets/TicketsView";
import { type View, go, useRoute } from "./shared/route";

const TABS: { view: View; label: string }[] = [
  { view: "players", label: "Players" },
  { view: "release", label: "Before release" },
  { view: "production", label: "In production" },
  { view: "plan", label: "Plan a release" },
  { view: "tickets", label: "Player tickets" },
];

export function App() {
  const view = useRoute();
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-sheet">
        <div className="mx-auto flex max-w-page flex-wrap items-end justify-between gap-4 px-6 pt-5">
          <div className="pb-4">
            <p className="text-lead font-bold text-ink">Reward app quality</p>
            <p className="text-small text-muted">Testing, rollout and player tickets for a rewarded mobile-gaming app, on simulated releases</p>
          </div>
          <nav aria-label="Views" className="flex flex-wrap gap-1">
            {TABS.map((t) => (
              <button key={t.view} type="button" onClick={() => go(t.view)} aria-current={view === t.view ? "page" : undefined}
                className={`border-b-rule px-3 pb-3 pt-2 font-semibold transition-colors ${view === t.view ? "border-focus text-ink" : "border-transparent text-muted hover:text-ink"}`}>
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-page px-6 py-7">
        {view === "players" && <PlayersView />}
        {view === "release" && <ReleaseView />}
        {view === "production" && <ProductionView />}
        {view === "plan" && <PlanView />}
        {view === "tickets" && <TicketsView />}
      </main>
    </div>
  );
}
