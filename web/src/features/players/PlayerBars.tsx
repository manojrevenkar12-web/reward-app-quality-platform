/** Player-days hit by escaped defects, per design, with the 95% interval as a whisker. */
import { motion } from "framer-motion";
import { NAME, bar, ink, int } from "../../shared/format";
import type { DesignSummary } from "../../shared/types";
import { motionTokens } from "../../theme/motion";

export function PlayerBars({ rows }: { rows: [string, DesignSummary][] }) {
  const max = Math.max(...rows.map(([, d]) => d.player_days_ci[1]));
  return (
    <ul className="flex flex-col gap-2">
      {rows.map(([name, d], i) => {
        const [lo, hi] = d.player_days_ci;
        return (
          <li key={name} className="grid grid-cols-1 items-center gap-1 sm:grid-cols-[13rem_1fr] sm:gap-4">
            <span className={`text-small font-semibold sm:text-right ${ink(name)}`}>{NAME[name] ?? d.label}</span>
            <div className="relative flex h-bar items-center" role="img"
              aria-label={`${NAME[name] ?? d.label}: ${int(d.player_days_per_week)} player-days a week, 95% interval ${int(lo)} to ${int(hi)}`}>
              <motion.div
                className={`h-3/4 rounded-soft ${bar(name)}`}
                initial={{ width: 0 }}
                animate={{ width: `${(d.player_days_per_week / max) * 86}%` }}
                transition={{ duration: motionTokens.fill, delay: i * motionTokens.stagger, ease: motionTokens.ease }}
              />
              <span aria-hidden className="absolute h-px bg-ink" style={{ left: `${(lo / max) * 86}%`, width: `${Math.max(((hi - lo) / max) * 86, 0.3)}%` }} />
              <span className="ml-3 whitespace-nowrap text-small font-semibold text-ink" style={{ position: "absolute", left: `${(hi / max) * 86 + 1}%` }}>
                {int(d.player_days_per_week)}
              </span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
