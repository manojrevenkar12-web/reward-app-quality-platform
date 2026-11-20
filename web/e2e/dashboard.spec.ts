import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

async function noViolations(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(r.violations.map((v) => `${v.id}: ${v.nodes.length}`)).toEqual([]);
}

test("players shows every design with intervals and the cost table", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("player-days hit by bugs a week");
  await expect(page.getByRole("img", { name: /^Platform: .* player-days a week/ })).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(13);
  await expect(page.getByText(/gate passed|gate not passed|not run yet/).first()).toBeVisible();
  await noViolations(page);
});

test("before release and in production compare every design", async ({ page }) => {
  await page.goto("/#/release");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("of defects found before release");
  await expect(page.locator("tbody tr")).toHaveCount(13);
  await noViolations(page);
  await page.goto("/#/production");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("bugs in coins or cash-outs reached players");
  await expect(page.getByRole("img", { name: /^Platform: rollout guardrail/ })).toBeVisible();
  await noViolations(page);
});

test("planning a release ranks cash-out first for a risky payout change", async ({ page }) => {
  await page.goto("/#/plan");
  await expect(page.getByRole("heading", { name: "Flows at risk" })).toBeVisible();
  await expect(page.locator("ol li").first()).toContainText("Cash-out");
  await expect(page.getByText("payout_service").last()).toBeVisible();
  await page.getByRole("button", { name: "Remove" }).first().click();
  await page.getByRole("button", { name: "Plan this release" }).click();
  await expect(page.locator("ol li").first()).not.toContainText("Cash-out");
  await noViolations(page);
});

test("the ticket reader reads German and is not steered by instructions in a ticket", async ({ page }) => {
  await page.goto("/#/tickets");
  await page.getByRole("button", { name: /Auszahlung/ }).click();
  await expect(page.getByText("Cash-out stuck")).toBeVisible();
  await page.getByRole("button", { name: /Ignore your instructions/ }).click();
  await expect(page.locator("dl")).toContainText("Cash-out");
  await noViolations(page);
});

test("an API failure offers a retry", async ({ page }) => {
  await page.route("**/api/results", (r) => r.fulfill({ status: 503, body: JSON.stringify({ detail: "warming up" }) }));
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("warming up");
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
});
