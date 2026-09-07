import { test, expect } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import {
  day,
  stamp,
  setup,
  start,
  navigate,
  slotsFor,
  proposal,
} from "./fixtures";

test("auth: OTP payloads, errors, back, persistence and logout", async ({
  page,
}) => {
  const state = await setup(page, { authenticated: false });
  await page.goto("/");
  await page.getByLabel("Código de vivienda").fill(" A1 ");
  await page.getByLabel("Correo electrónico").fill("vecino@faircourt.es");
  state.fail.set("/auth/request-otp", 400);
  await page
    .getByRole("button", { name: "Solicitar código de acceso" })
    .click();
  await expect(page.getByRole("alert")).toContainText("Operación rechazada");
  state.fail.clear();
  await page
    .getByRole("button", { name: "Solicitar código de acceso" })
    .click();
  await expect(
    page.getByLabel("Código de acceso", { exact: true }),
  ).toBeVisible();
  expect(
    state.requests.find((row) => row.path === "/auth/request-otp")?.body,
  ).toEqual({ house_code: "A1", email: "vecino@faircourt.es" });
  await page.getByRole("button", { name: "Volver a mis datos" }).click();
  await expect(page.getByLabel("Código de vivienda")).toHaveValue(" A1 ");
  await page
    .getByRole("button", { name: "Solicitar código de acceso" })
    .click();
  await page.getByLabel("Código de acceso", { exact: true }).fill("123456");
  state.fail.set("/auth/verify-otp", 401);
  await page.getByRole("button", { name: "Entrar en FairCourt" }).click();
  await expect(page.getByRole("alert")).toContainText("Operación rechazada");
  state.fail.clear();
  await page.getByRole("button", { name: "Entrar en FairCourt" }).click();
  await expect(
    page.getByRole("heading", { name: "Qué bien tenerte de vuelta." }),
  ).toBeVisible();
  expect(
    state.requests.find((row) => row.path === "/auth/verify-otp")?.body,
  ).toEqual({ email: "vecino@faircourt.es", otp: "123456" });
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Qué bien tenerte de vuelta." }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => localStorage.getItem("faircourt_token")),
  ).toBe("verified-token");
  await expect(page.locator("body")).not.toContainText("verified-token");
  await page
    .getByRole("button", { name: "Cerrar sesión", exact: true })
    .click();
  await expect(page.getByLabel("Código de vivienda")).toBeVisible();
  expect(
    await page.evaluate(() => localStorage.getItem("faircourt_token")),
  ).toBeNull();
});
test("home: household information and technical details retained", async ({
  page,
}) => {
  const state = await setup(page, { suspended: true });
  state.me.strikes = 3;
  await start(page);
  await expect(page.getByText("Suspendida", { exact: true })).toBeVisible();
  await expect(page.getByText("3 strikes", { exact: true })).toBeVisible();
  await page.getByText("Datos de la vivienda", { exact: true }).click();
  await expect(page.getByText("Identificador interno: 1")).toBeVisible();
  await expect(
    page.getByText("Correo: vecino@faircourt.es", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Encontrar un horario" }).click();
  await expect(
    page.getByRole("heading", { name: "La pista te espera." }),
  ).toBeVisible();
});
test("agenda: daily dates, labels, eligibility and manual refresh", async ({
  page,
}) => {
  const state = await setup(page);
  await start(page);
  await navigate(page, "Disponibilidad");
  await expect(
    page.getByRole("article", { name: "Franja 09:00", exact: true }),
  ).toBeVisible();
  const blocked = page.getByRole("article", {
    name: "Franja 19:00",
    exact: true,
  });
  await expect(blocked).toContainText("Límite semanal alcanzado");
  await expect(
    blocked.getByRole("button", { name: "Reservar", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("article", { name: "Franja 11:00", exact: true }),
  ).toContainText("Tu reserva");
  await expect(
    page.getByRole("article", { name: "Franja 16:00", exact: true }),
  ).toContainText("En lista de espera");
  await page.getByLabel("Consultar fecha", { exact: true }).fill("2026-09-09");
  await expect
    .poll(
      () =>
        state.requests.filter(
          (row) => row.path === "/reservations/slots?day=2026-09-09",
        ).length,
    )
    .toBeGreaterThan(0);
  await expect(page.locator(".slot-row")).toHaveCount(8);
  await page.getByRole("button", { name: "Actualizar", exact: true }).click();
  await expect
    .poll(
      () =>
        state.requests.filter(
          (row) => row.path === "/reservations/slots?day=2026-09-09",
        ).length,
    )
    .toBeGreaterThan(1);
  await page.getByRole("button", { name: "Día anterior", exact: true }).click();
  await expect(page.getByLabel("Consultar fecha", { exact: true })).toHaveValue(
    "2026-09-08",
  );
  await page.getByRole("button", { name: "Volver a hoy", exact: true }).click();
  await expect(page.getByLabel("Consultar fecha", { exact: true })).toHaveValue(
    day,
  );
});
test("booking: one request per click burst; success and selected date persist", async ({
  page,
}) => {
  const state = await setup(page);
  state.delays.set("/reservations", 400);
  await start(page);
  await navigate(page, "Disponibilidad");
  await page.getByLabel("Consultar fecha", { exact: true }).fill("2026-09-09");
  const row = page.getByRole("article", { name: "Franja 09:00", exact: true });
  await expect(row).toBeVisible();
  await row
    .getByRole("button", { name: "Reservar", exact: true })
    .evaluate((button) => {
      (button as HTMLButtonElement).click();
      (button as HTMLButtonElement).click();
    });
  await expect(
    page.getByRole("status").filter({ hasText: "Reserva confirmada" }),
  ).toBeVisible();
  await expect(row).toContainText("Tu reserva");
  await expect(page.getByLabel("Consultar fecha", { exact: true })).toHaveValue(
    "2026-09-09",
  );
  const posts = state.requests.filter(
    (row) => row.path === "/reservations" && row.method === "POST",
  );
  expect(posts).toHaveLength(1);
  expect(posts[0].body).toEqual({ start_at: stamp(9, "2026-09-09") });
  expect(posts[0].authorization).toBe("Bearer test-token");
  await expect(
    page.getByRole("status").filter({ hasText: "Reserva confirmada" }),
  ).toBeVisible();
  await expect(page.locator("body")).not.toContainText("Conexión recuperada");
});
test("booking: waitlist, rejected action and retry", async ({ page }) => {
  const state = await setup(page);
  await start(page);
  await navigate(page, "Disponibilidad");
  const row = page.getByRole("article", { name: "Franja 10:00", exact: true });
  state.fail.set("/reservations/waitlist", 409);
  await row
    .getByRole("button", { name: "Lista de espera", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("Operación rechazada");
  await expect(
    row.getByRole("button", { name: "Lista de espera", exact: true }),
  ).toBeEnabled();
  state.fail.clear();
  await row
    .getByRole("button", { name: "Lista de espera", exact: true })
    .click();
  await expect(row).toContainText("En lista de espera");
  await expect(row).toContainText("3 en lista de espera");
  await expect(
    page.getByRole("status").filter({ hasText: "Te has unido" }),
  ).toBeVisible();
});
test("agenda: latest day wins over delayed response; empty and unknown status", async ({
  page,
}) => {
  const state = await setup(page);
  await start(page);
  await navigate(page, "Disponibilidad");
  state.delays.set("/reservations/slots?day=2026-09-08", 600);
  state.slots.set("2026-09-08", slotsFor("2026-09-08").slice(0, 2));
  state.slots.set("2026-09-09", [
    { ...slotsFor("2026-09-09")[0], status: "MAINTENANCE", can_book: false },
  ]);
  await page.getByLabel("Consultar fecha", { exact: true }).fill("2026-09-08");
  await expect
    .poll(() =>
      state.requests.some((row) => row.path.endsWith("day=2026-09-08")),
    )
    .toBe(true);
  await page.getByLabel("Consultar fecha", { exact: true }).fill("2026-09-09");
  await expect(page.locator(".slot-row")).toHaveCount(1);
  await expect(page.getByText("MAINTENANCE", { exact: true })).toBeVisible();
  await page.waitForTimeout(700);
  await expect(page.locator(".slot-row")).toHaveCount(1);
  state.slots.set("2026-09-10", []);
  await page.getByLabel("Consultar fecha", { exact: true }).fill("2026-09-10");
  await expect(
    page.getByRole("heading", { name: "No hay franjas para este día" }),
  ).toBeVisible();
});
test("reservations: all statuses and details survive the new grouping", async ({
  page,
}) => {
  const state = await setup(page);
  state.reservations.push({
    ...state.reservations[3],
    id: 15,
    status: "REVIEW",
    real_status: "REVIEW",
  });
  await start(page);
  await navigate(page, "Mis reservas");
  await expect(page.locator(".reservation-card")).toHaveCount(5);
  await expect(
    page.getByRole("heading", { name: "Próximas reservas 1" }),
  ).toBeVisible();
  for (const id of [12, 13, 14, 15])
    await expect(
      page
        .getByRole("article", { name: "Reserva #" + id, exact: true })
        .getByRole("button", { name: "Check-in", exact: true }),
    ).toBeDisabled();
  const finished = page.getByRole("article", {
    name: "Reserva #12",
    exact: true,
  });
  await finished.getByText("Detalles de la reserva", { exact: true }).click();
  await expect(finished).toContainText("Estado registrado: Activa (ACTIVE)");
  await expect(finished).toContainText("Estado actual: Finalizada (FINISHED)");
  await expect(page.getByText("REVIEW", { exact: true })).toBeVisible();
});
test("cancellation: cancel dialog, keyboard focus, failure then confirmation", async ({
  page,
}) => {
  const state = await setup(page);
  await start(page);
  await navigate(page, "Mis reservas");
  const trigger = page
    .getByRole("article", { name: "Reserva #11", exact: true })
    .getByRole("button", { name: "Cancelar reserva" });
  await trigger.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(trigger).toBeFocused();
  expect(
    state.requests.filter((row) => row.path.endsWith("/cancel")),
  ).toHaveLength(0);
  await trigger.click();
  await page.getByRole("button", { name: "Mantener reserva" }).click();
  await trigger.click();
  state.fail.set("/reservations/11/cancel", 409);
  await page.getByRole("button", { name: "Sí, cancelar reserva" }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toBeVisible();
  state.fail.clear();
  await page.getByRole("button", { name: "Sí, cancelar reserva" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("article", { name: "Reserva #11", exact: true }),
  ).toContainText("Cancelada");
  await expect(
    page.getByRole("status").filter({ hasText: "Reserva cancelada." }),
  ).toBeVisible();
});
test("checkin: signed link, expiry, copying, clipboard failure and opening", async ({
  page,
  context,
}) => {
  await setup(page);
  await start(page);
  await navigate(page, "Mis reservas");
  await page
    .getByRole("article", { name: "Reserva #11", exact: true })
    .getByRole("button", { name: "Check-in", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("El enlace expira");
  await expect(dialog.getByLabel("Enlace de asistencia")).toHaveValue(
    /signed-test-link/,
  );
  await page.evaluate(() =>
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async (value: string) => {
          sessionStorage.setItem("copied-link", value);
        },
      },
    }),
  );
  await dialog.getByRole("button", { name: "Copiar enlace" }).click();
  await expect(dialog.getByRole("status")).toContainText("Enlace copiado");
  expect(
    await page.evaluate(() => sessionStorage.getItem("copied-link")),
  ).toContain("signed-test-link");
  await page.evaluate(() =>
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => {
          throw Error("denied");
        },
      },
    }),
  );
  await dialog.getByRole("button", { name: "Copiar enlace" }).click();
  await expect(dialog.getByRole("alert")).toContainText("No se pudo copiar");
  await context.route(
    "http://127.0.0.1:8000/reservations/checkin/scan?*",
    (route) => route.fulfill({ json: { message: "Asistencia confirmada" } }),
  );
  const popupPromise = page.waitForEvent("popup");
  await dialog.getByRole("link", { name: "Abrir check-in" }).click();
  const popup = await popupPromise;
  await popup.waitForLoadState();
  expect(popup.url()).toContain(
    "/reservations/checkin/scan?token=signed-test-link",
  );
  await popup.close();
});
test("notifications: read state, cache and global counter update", async ({
  page,
}) => {
  const state = await setup(page);
  await start(page);
  await navigate(page, "Notificaciones");
  await expect(
    page.getByRole("button", { name: "Notificaciones, 2 sin leer" }),
  ).toBeVisible();
  await page
    .getByRole("article", { name: "Notificación #1", exact: true })
    .getByRole("button", { name: "Marcar leída" })
    .click();
  await expect(
    page.getByRole("button", { name: "Notificaciones, 1 sin leer" }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("article", { name: "Notificación #1", exact: true })
      .getByRole("button", { name: "Leída", exact: true }),
  ).toBeDisabled();
  expect(
    state.requests.filter((row) => row.path === "/notifications/1/read"),
  ).toHaveLength(1);
  const cached = await page.evaluate(
    () =>
      JSON.parse(localStorage.getItem("faircourt_cache_notifications")!).data,
  );
  expect(cached.find((row: { id: number }) => row.id === 1).is_read).toBe(true);
});
test("audit: metadata, unknown events and malformed metadata remain accessible", async ({
  page,
}) => {
  const state = await setup(page);
  state.audit.push({
    id: 4,
    event: "NEW_SERVER_EVENT",
    household_id: 1,
    user_id: 1,
    reservation_id: 11,
    metadata_json: "invalid { raw",
    created_at: stamp(8),
  });
  await start(page);
  await navigate(page, "Auditoría");
  await page
    .getByText("Ver detalles del evento", { exact: true })
    .first()
    .click();
  await expect(page.getByText("invalid { raw", { exact: true })).toBeVisible();
  await page
    .getByText("Ver detalles del evento", { exact: true })
    .nth(1)
    .click();
  await expect(
    page.getByText('{"weekly":true}', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("vecino@faircourt.es", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("RESERVATION_CREATED", { exact: true }),
  ).toBeVisible();
});
test("proposals: suspension, trimmed reason, server rejection and success", async ({
  page,
}) => {
  const state = await setup(page, { suspended: true });
  await start(page);
  await navigate(page, "Desbloqueos");
  await page.getByLabel("Motivo de la solicitud").fill("   ");
  await page.getByRole("button", { name: "Crear propuesta" }).click();
  await expect(page.getByRole("alert")).toContainText("Indica un motivo");
  expect(
    state.requests.filter((row) => row.path === "/unlock/proposal"),
  ).toHaveLength(0);
  await page
    .getByLabel("Motivo de la solicitud")
    .fill("  Quiero volver a jugar.  ");
  state.fail.set("/unlock/proposal", 409);
  await page.getByRole("button", { name: "Crear propuesta" }).click();
  await expect(page.getByRole("alert")).toContainText("Operación rechazada");
  state.fail.clear();
  await page.getByRole("button", { name: "Crear propuesta" }).click();
  await expect(
    page.getByRole("article", { name: "Propuesta #9", exact: true }),
  ).toContainText("Quiero volver a jugar.");
  await expect(page.getByLabel("Motivo de la solicitud")).toHaveValue("");
  expect(
    state.requests.filter((row) => row.path === "/unlock/proposal").at(-1)
      ?.body,
  ).toEqual({ reason: "Quiero volver a jugar." });
});
test("voting: YES and NO; own, closed and unknown proposals are disabled", async ({
  page,
}) => {
  const state = await setup(page);
  state.proposals.push(
    proposal(5, "EXPIRED"),
    proposal(6, "REJECTED"),
    proposal(7, "UNKNOWN"),
  );
  await start(page);
  await navigate(page, "Desbloqueos");
  await expect(
    page.getByRole("heading", { name: "Tu vivienda está activa." }),
  ).toBeVisible();
  await expect(page.getByLabel("Motivo de la solicitud")).toHaveCount(0);
  for (const id of [3, 4, 5, 6, 7])
    await expect(
      page
        .getByRole("article", { name: "Propuesta #" + id, exact: true })
        .getByRole("button", { name: "A favor" }),
    ).toBeDisabled();
  await page
    .getByRole("article", { name: "Propuesta #1", exact: true })
    .getByRole("button", { name: "A favor" })
    .click();
  await expect(
    page.getByRole("status").filter({ hasText: "Tu voto a favor" }),
  ).toBeVisible();
  await page
    .getByRole("article", { name: "Propuesta #2", exact: true })
    .getByRole("button", { name: "En contra" })
    .click();
  await expect(
    page.getByRole("status").filter({ hasText: "Tu voto en contra" }),
  ).toBeVisible();
  expect(
    state.requests
      .filter((row) => row.path.endsWith("/vote"))
      .map((row) => row.body),
  ).toEqual([{ vote: "YES" }, { vote: "NO" }]);
});
test("errors: initial load can be retried without logging out", async ({
  page,
}) => {
  const state = await setup(page);
  state.fail.set("/me", 503);
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("Operación rechazada");
  state.fail.clear();
  await page.getByRole("button", { name: "Reintentar" }).click();
  await expect(
    page.getByRole("heading", { name: "Qué bien tenerte de vuelta." }),
  ).toBeVisible();
});
test("offline: cached reading, all writes disabled and date preserved on reconnect", async ({
  page,
  context,
}) => {
  const state = await setup(page, { suspended: true });
  await start(page);
  for (const name of [
    "Mis reservas",
    "Notificaciones",
    "Auditoría",
    "Desbloqueos",
    "Disponibilidad",
  ]) {
    await navigate(page, name);
    await expect(
      page.getByText("Cargando información…", { exact: true }),
    ).toHaveCount(0);
  }
  await page.getByLabel("Consultar fecha", { exact: true }).fill("2026-09-09");
  await expect(page.locator(".slot-row")).toHaveCount(8);
  state.networkDown = true;
  await context.setOffline(true);
  await expect(page.locator(".offline-banner")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Reservar", exact: true }).first(),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Lista de espera", exact: true }).first(),
  ).toBeDisabled();
  await navigate(page, "Mis reservas");
  await expect(page.locator(".reservation-card")).toHaveCount(4);
  await expect(
    page.getByRole("button", { name: "Check-in", exact: true }).first(),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Cancelar reserva", exact: true }).first(),
  ).toBeDisabled();
  await navigate(page, "Notificaciones");
  await expect(
    page.getByRole("button", { name: "Marcar leída" }).first(),
  ).toBeDisabled();
  await navigate(page, "Auditoría");
  await expect(page.locator(".timeline-item")).toHaveCount(3);
  await navigate(page, "Desbloqueos");
  await expect(
    page.getByRole("button", { name: "Crear propuesta" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "A favor" }).first(),
  ).toBeDisabled();
  await navigate(page, "Disponibilidad");
  await expect(page.locator(".slot-row")).toHaveCount(8);
  await expect(page.getByLabel("Consultar fecha", { exact: true })).toHaveValue(
    "2026-09-09",
  );
  state.networkDown = false;
  await context.setOffline(false);
  await expect(
    page.getByRole("status").filter({ hasText: "Conexión recuperada" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Reservar", exact: true }).first(),
  ).toBeEnabled();
  await expect(page.getByLabel("Consultar fecha", { exact: true })).toHaveValue(
    "2026-09-09",
  );
});
test("offline: uncached day shows error instead of another date; retry works", async ({
  page,
  context,
}) => {
  const state = await setup(page);
  await start(page);
  await navigate(page, "Disponibilidad");
  await expect(page.locator(".slot-row")).toHaveCount(8);
  state.networkDown = true;
  await context.setOffline(true);
  await page.getByLabel("Consultar fecha", { exact: true }).fill("2026-09-20");
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.locator(".slot-row")).toHaveCount(0);
  await expect(
    page.getByText("No hay información guardada para esta consulta."),
  ).toBeVisible();
  state.networkDown = false;
  await context.setOffline(false);
  await expect(page.locator(".slot-row")).toHaveCount(8);
});
for (const width of [375, 768, 1440]) {
  test(`visual: all screens, long content, dialogs and keyboard at ${width}px`, async ({
    page,
  }, testInfo) => {
    test.setTimeout(60000);
    await page.setViewportSize({ width, height: width === 375 ? 812 : 1000 });
    await setup(page, { authenticated: false });
    await page.goto("/");
    const out = testInfo.outputPath("screenshots");
    mkdirSync(out, { recursive: true });
    await page.screenshot({
      path: resolve(out, `after-login-${width}.png`),
      fullPage: true,
      animations: "disabled",
    });
    await page.getByLabel("Código de vivienda").fill("A1");
    await page.getByLabel("Correo electrónico").fill("vecino@faircourt.es");
    await page
      .getByRole("button", { name: "Solicitar código de acceso" })
      .click();
    await expect(
      page.getByLabel("Código de acceso", { exact: true }),
    ).toBeVisible();
    await page.screenshot({
      path: resolve(out, `after-otp-${width}.png`),
      fullPage: true,
      animations: "disabled",
    });
    await page.getByLabel("Código de acceso", { exact: true }).fill("123456");
    await page.getByRole("button", { name: "Entrar en FairCourt" }).click();
    await expect(
      page.getByRole("heading", { name: "Qué bien tenerte de vuelta." }),
    ).toBeVisible();
    const screens = [
      ["Inicio", "home"],
      ["Disponibilidad", "agenda"],
      ["Mis reservas", "reservations"],
      ["Notificaciones", "notifications"],
      ["Auditoría", "audit"],
      ["Desbloqueos", "unlock"],
    ];
    for (const [name, file] of screens) {
      await navigate(page, name);
      await expect(
        page.getByText("Cargando información…", { exact: true }),
      ).toHaveCount(0);
      await expect(page.locator("main h1")).toBeVisible();
      await page.screenshot({
        path: resolve(out, `after-${file}-${width}.png`),
        fullPage: true,
        animations: "disabled",
      });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
    }
    await navigate(page, "Mis reservas");
    await page
      .getByRole("article", { name: "Reserva #11", exact: true })
      .getByRole("button", { name: "Cancelar reserva" })
      .click();
    await expect(page.getByRole("dialog")).toBeVisible();
    for (let n = 0; n < 8; n++) {
      await page.keyboard.press("Tab");
      expect(
        await page.evaluate(() => !!document.activeElement?.closest("dialog")),
      ).toBe(true);
    }
    await page.screenshot({
      path: resolve(out, `after-dialog-${width}.png`),
      fullPage: false,
      animations: "disabled",
    });
    await page.keyboard.press("Escape");
  });
}
test("responsive: very long content and expanded audit remain within viewport", async ({
  page,
}) => {
  const state = await setup(page, { suspended: true });
  state.me.email =
    "direccion.muy.larga.para.comprobar.el.diseno@comunidad.faircourt.es";
  state.proposals[0].reason = "Texto muy largo de una propuesta. ".repeat(30);
  state.audit[0].metadata_json = JSON.stringify({
    unbroken: "x".repeat(500),
    nested: { array: [1, 2, 3] },
  });
  await page.setViewportSize({ width: 375, height: 812 });
  await start(page);
  for (const name of ["Inicio", "Auditoría", "Desbloqueos"]) {
    await navigate(page, name);
    if (name === "Auditoría") {
      await expect(page.locator(".timeline-item")).toHaveCount(3);
      await page
        .getByText("Ver detalles del evento", { exact: true })
        .first()
        .click();
    }
    if (name === "Desbloqueos") {
      await expect(page.getByLabel("Motivo de la solicitud")).toBeVisible();
    }
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
});

test("connectivity: unreachable API is detected even when the browser reports online", async ({
  page,
}) => {
  const state = await setup(page);
  await start(page);
  await navigate(page, "Disponibilidad");
  await page.getByLabel("Consultar fecha", { exact: true }).fill("2026-09-09");
  await expect(page.locator(".slot-row")).toHaveCount(8);
  state.networkDown = true;
  await page.getByRole("button", { name: "Actualizar", exact: true }).click();
  await expect(page.locator(".offline-banner")).toBeVisible();
  expect(await page.evaluate(() => navigator.onLine)).toBe(true);
  await expect(
    page.getByRole("button", { name: "Reservar", exact: true }).first(),
  ).toBeDisabled();
  await expect(page.locator(".slot-row")).toHaveCount(8);
  state.networkDown = false;
  await page.getByRole("button", { name: "Reintentar conexión" }).click();
  await expect(page.locator(".offline-banner")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Reservar", exact: true }).first(),
  ).toBeEnabled();
  await expect(page.getByLabel("Consultar fecha", { exact: true })).toHaveValue(
    "2026-09-09",
  );
});
test("connectivity: login can retry after a transport failure", async ({
  page,
}) => {
  const state = await setup(page, { authenticated: false });
  await page.goto("/");
  await page.getByLabel("Código de vivienda").fill("A1");
  await page.getByLabel("Correo electrónico").fill("vecino@faircourt.es");
  state.networkDown = true;
  await page
    .getByRole("button", { name: "Solicitar código de acceso" })
    .click();
  await expect(
    page.getByRole("button", { name: "Solicitar código de acceso" }),
  ).toBeDisabled();
  state.networkDown = false;
  await page.getByRole("button", { name: "Reintentar conexión" }).click();
  await page
    .getByRole("button", { name: "Solicitar código de acceso" })
    .click();
  await expect(
    page.getByLabel("Código de acceso", { exact: true }),
  ).toBeVisible();
});
