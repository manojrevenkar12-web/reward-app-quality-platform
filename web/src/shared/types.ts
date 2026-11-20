export type DesignSummary = {
  label: string;
  player_days_per_week: number;
  player_days_ci: [number, number];
  money_player_days_per_week: number;
  player_eur_per_week: number;
  qa_hours_per_week: number;
  eng_hours_per_week: number;
  device_eur_per_week: number;
  cost_eur_per_week: number;
  defects: number;
  found_before_release: number;
  found_share: number;
  escaped: number;
  escaped_money: number;
  undetected: number;
  flaky_failures_per_week: number;
  halts: number;
  false_halts: number;
  lead_hours_median: number;
  detect_hours_median: number | null;
  channels: Record<string, number>;
  reader_accuracy: number | null;
  devices_tested: number;
};

export type Report = {
  designs: Record<string, DesignSummary>;
  world: { orgs: number; seeds: number[]; weeks: number; releases: number; changes: number; defects: number; dau: number };
};

export type Results = { dev: Report; heldout: Report | null; gate: { dev: string[]; heldout: string[] | null } };

export type Module = { name: string; side: "app" | "backend"; flows: string[] };
export type Catalogue = { modules: Module[]; flows: Record<string, { usage: number; money: boolean }>; devices: { name: string; share: number }[] };

export type PlanOut = {
  changes: { module: string; side: string; flows: string[]; risk: number }[];
  flows: Record<string, number>;
  devices: { name: string; share: number }[];
  device_share: number;
  exploratory: Record<string, number>;
  contracts: string[];
  rollout: [number, number][];
  model: string;
};

export type Reading = { flow: string | null; symptom: string | null; source: string };
