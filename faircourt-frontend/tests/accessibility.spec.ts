import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { setup, start, navigate } from "./fixtures";
for (const theme of ["light", "dark"] as const) {
  for (const width of [375, 1440]) {
    test(`accessibility: ${theme} contrast and semantics across all screens at ${width}px`, async ({
      page,
    }) => {
      test.setTimeout(60000);
      await page.setViewportSize({ width, height: 1000 });
      await page.emulateMedia({ reducedMotion: "reduce" });
      await page.addInitScript((selectedTheme) => {
        localStorage.setItem("faircourt_theme", selectedTheme);
      }, theme);
      await setup(page, { authenticated: false, suspended: true });
      await page.goto("/");
      async function check(name: string) {
        const results = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze();
        expect
          .soft(
            results.violations.map((v) => ({
              id: v.id,
              nodes: v.nodes.map((n) => ({
                target: n.target,
                summary: n.failureSummary,
              })),
            })),
            name,
          )
          .toEqual([]);
      }
      await expect(page.getByLabel("Código de vivienda")).toBeVisible();
      await check("Acceso");
      await page.getByLabel("Código de vivienda").fill("A1");
      await page.getByLabel("Correo electrónico").fill("vecino@faircourt.es");
      await page
        .getByRole("button", { name: "Solicitar código de acceso" })
        .click();
      await page.getByLabel("Código de acceso", { exact: true }).fill("123456");
      await check("OTP");
      await page.getByRole("button", { name: "Entrar en FairCourt" }).click();
      await expect(
        page.getByRole("heading", { name: "Qué bien tenerte de vuelta." }),
      ).toBeVisible();
      for (const name of [
        "Inicio",
        "Disponibilidad",
        "Mis reservas",
        "Notificaciones",
        "Auditoría",
        "Desbloqueos",
        "Contacto",
      ]) {
        await navigate(page, name);
        await expect(
          page.getByText("Cargando información…", { exact: true }),
        ).toHaveCount(0);
        await check(name);
      }
      await navigate(page, "Inicio");
      await page
        .getByRole("button", {
          name: "Notificaciones, 2 sin leer",
          exact: true,
        })
        .click();
      await expect(
        page.getByRole("dialog", { name: "Notificaciones" }),
      ).toBeVisible();
      await check("Vista previa de notificaciones");
      await page.keyboard.press("Escape");
      await navigate(page, "Mis reservas");
      await page
        .getByRole("article", { name: "Reserva #11", exact: true })
        .getByRole("button", { name: "Cancelar reserva" })
        .click();
      await check("Diálogo");
    });
  }
}
test("accessibility: skip link and reduced motion", async ({ page }) => {
  await setup(page);
  await start(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Saltar al contenido" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
  expect(
    await page
      .locator(".page-stack")
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe("none");
});

for (const theme of ["light", "dark"] as const) {
  for (const width of [375, 1440]) {
    test(`accessibility: admin ${theme} at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 1000 });
      await page.emulateMedia({ reducedMotion: "reduce" });
      await page.addInitScript((selectedTheme) => {
        localStorage.setItem("faircourt_theme", selectedTheme);
      }, theme);
      await setup(page, { authenticated: false });
      await page.goto("/admin");
      async function check(name: string) {
        const results = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze();
        expect.soft(results.violations, name).toEqual([]);
      }
      await check("Acceso administrativo");
      await page
        .getByLabel("Correo administrativo")
        .fill("admin@faircourt.es");
      await page
        .getByRole("button", { name: "Solicitar acceso administrativo" })
        .click();
      await page.getByLabel("Código de acceso").fill("123456");
      await page.getByRole("button", { name: "Entrar al panel" }).click();
      await expect(
        page.getByRole("heading", {
          name: "Elige la comunidad que vas a gestionar.",
        }),
      ).toBeVisible();
      await check("Selector administrativo");
      await page
        .getByRole("article")
        .filter({ hasText: "Gran Parque" })
        .getByRole("button", { name: "Administrar comunidad" })
        .click();
      await check("Contexto administrativo");
      await page.getByRole("button", { name: "Nueva vivienda" }).click();
      await expect(
        page.getByRole("dialog", { name: "Nueva vivienda" }),
      ).toBeVisible();
      await check("Formulario administrativo de viviendas");
      await page.keyboard.press("Escape");
      await page
        .getByRole("article", { name: "GRP0001", exact: true })
        .getByRole("button", { name: "Editar GRP0001" })
        .click();
      await expect(
        page.getByRole("dialog", { name: "Editar GRP0001" }),
      ).toBeVisible();
      await check("Edición administrativa de viviendas");
      await page.keyboard.press("Escape");
      await page
        .getByRole("article", { name: "GRP0001", exact: true })
        .getByRole("button", { name: "Gestionar acceso de GRP0001" })
        .click();
      await expect(
        page.getByRole("dialog", { name: "Gestionar acceso de GRP0001" }),
      ).toBeVisible();
      await check("Gestión administrativa de acceso residencial");
      await page.keyboard.press("Escape");
      await page.getByRole("button", { name: "Nueva instalación" }).click();
      await expect(
        page.getByRole("dialog", { name: "Nueva instalación" }),
      ).toBeVisible();
      await check("Formulario administrativo de instalaciones");
      await page.keyboard.press("Escape");
      await page.getByRole("button", { name: "Editar reglas básicas" }).click();
      await expect(
        page.getByRole("dialog", { name: "Editar reglas básicas" }),
      ).toBeVisible();
      await check("Formulario administrativo de reglas básicas");
      await page.keyboard.press("Escape");
    });
  }
}
