/** One table shape for every report view: designs down, measures across, the main designs coloured. */
import { NAME, ink } from "../format";
import type { DesignSummary } from "../types";

export type Column = { label: string; value: (d: DesignSummary) => string; note?: string };

export function DesignTable({ title, rows, columns }: { title: string; rows: [string, DesignSummary][]; columns: Column[] }) {
  return (
    <div className="overflow-x-auto rounded-card bg-sheet p-5">
      <table className="min-w-table text-small">
        <caption className="pb-3 text-left text-lead font-bold text-ink">{title}</caption>
        <thead>
          <tr className="border-b border-line text-left text-muted">
            <th scope="col" className="py-2 pr-4 font-semibold">Design</th>
            {columns.map((c) => (
              <th key={c.label} scope="col" className="py-2 pr-4 text-right font-semibold" title={c.note}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(([n, d]) => (
            <tr key={n} className="border-b border-line last:border-0">
              <th scope="row" className={`py-2 pr-4 text-left font-semibold ${ink(n)}`}>{NAME[n] ?? d.label}</th>
              {columns.map((c) => (
                <td key={c.label} className="py-2 pr-4 text-right">{c.value(d)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
