import { test, expect, chromium } from "@playwright/test";
import { setup, navigate } from "./fixtures";
test("pwa: production manifest, valid icons, installability and offline cold opening", async ({}, testInfo) => {
  const context = await chromium.launchPersistentContext(
    testInfo.outputPath("pwa-profile"),
    {
      channel: process.env.PW_CHANNEL || "msedge",
      headless: true,
      serviceWorkers: "allow",
      viewport: { width: 1440, height: 1000 },
      locale: "es-ES",
      timezoneId: "Europe/Madrid",
    },
  );
  try {
    const page = context.pages()[0];
    const state = await setup(page);
    await page.goto("http://127.0.0.1:4173");
    await expect(
      page.getByRole("heading", { name: "Qué bien tenerte de vuelta." }),
    ).toBeVisible();
    const manifest = await (
      await page.request.get("http://127.0.0.1:4173/manifest.webmanifest")
    ).json();
    expect(manifest.name).toBe("FairCourt");
    expect(manifest.display).toBe("standalone");
    expect(manifest.theme_color).toBe("#173f35");
    for (const size of [192, 512]) {
      const icon = await (
        await page.request.get(`http://127.0.0.1:4173/pwa-${size}x${size}.png`)
      ).body();
      expect(icon.readUInt32BE(16)).toBe(size);
      expect(icon.readUInt32BE(20)).toBe(size);
    }
    await page.evaluate(() => navigator.serviceWorker.ready.then(() => true));
    await page.reload();
    await page.waitForFunction(
      () => navigator.serviceWorker.controller !== null,
    );
    const cdp = await context.newCDPSession(page);
    const installability = await cdp.send("Page.getInstallabilityErrors");
    expect(installability.installabilityErrors).toEqual([]);
    await navigate(page, "Disponibilidad");
    await expect(page.locator(".slot-row")).toHaveCount(8);
    await navigate(page, "Mis reservas");
    await expect(page.locator(".reservation-card")).toHaveCount(4);
    state.networkDown = true;
    // Modern CDP separates network failures from navigator's connection state.
    // Disable the HTTP cache so only the installed service worker can serve the shell.
    await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
    await cdp.send("Network.emulateNetworkConditionsByRule", {
      offline: true,
      matchedNetworkConditions: [{ urlPattern: "", latency: 0, downloadThroughput: -1, uploadThroughput: -1 }],
    });
    await cdp.send("Network.overrideNetworkState", {
      offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1,
    });
    await context.route("http://127.0.0.1:4173/**", route => route.abort("internetdisconnected"));
    await page.reload();
    const offline = page;
    await expect(
      offline.getByRole("heading", { name: "Qué bien tenerte de vuelta." }),
    ).toBeVisible();
    await expect(offline.locator(".offline-banner")).toBeVisible();
    await navigate(offline, "Mis reservas");
    await expect(offline.locator(".reservation-card")).toHaveCount(4);
    await expect(
      offline.getByRole("button", { name: "Check-in", exact: true }).first(),
    ).toBeDisabled();
    expect(
      await offline.evaluate(() => getComputedStyle(document.body).fontFamily),
    ).toContain("Segoe UI");
  } finally {
    await context.close();
  }
});
