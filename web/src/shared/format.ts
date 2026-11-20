export const int = (v: number) => Math.round(v).toLocaleString("en-GB");
export const one = (v: number) => v.toLocaleString("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
export const pct = (v: number, d = 0) => `${(v * 100).toFixed(d)}%`;
export const eur = (v: number) => `€${Math.round(v).toLocaleString("en-GB")}`;

export const ORDER = [
  "as_found",
  "automate_everything",
  "platform_static_risk",
  "platform_top_devices",
  "platform_us_only",
  "platform_no_contracts",
  "platform_no_ledger",
  "platform_no_quarantine",
  "platform_no_exploratory",
  "platform_no_staged_rollout",
  "platform_no_guardrails",
  "platform_no_ticket_agent",
  "platform",
];

export const NAME: Record<string, string> = {
  as_found: "As found",
  automate_everything: "Automate everything",
  platform_static_risk: "Fixed risk ranking",
  platform_top_devices: "7 most popular devices",
  platform_us_only: "US locale only",
  platform_no_contracts: "No contract tests",
  platform_no_ledger: "No coin-ledger checks",
  platform_no_quarantine: "No flaky quarantine",
  platform_no_exploratory: "No exploratory testing",
  platform_no_staged_rollout: "20% then 100%",
  platform_no_guardrails: "No rollout guardrails",
  platform_no_ticket_agent: "Support escalates by hand",
  platform: "Platform",
};

export const FLOW: Record<string, string> = {
  login: "Login",
  onboarding: "Onboarding",
  play_round: "Playing a round",
  offerwall: "Offer wall",
  cashout: "Cash-out",
  live_event: "Live event",
  notifications: "Notifications",
  identity_check: "Identity check",
  settings: "Settings",
};

export const SYMPTOM: Record<string, string> = {
  crash: "Crash",
  cashout_stuck: "Cash-out stuck",
  coins_wrong: "Coins wrong",
  display_broken: "Display broken",
  slow: "Slow",
  error: "Error message",
};

export const ink = (name: string) =>
  name === "platform" ? "text-platformInk" : name === "as_found" ? "text-asFoundInk" : name === "automate_everything" ? "text-everythingInk" : "text-copy";
export const bar = (name: string) =>
  name === "platform" ? "bg-platform" : name === "as_found" ? "bg-asFound" : name === "automate_everything" ? "bg-everything" : "bg-ablation";
