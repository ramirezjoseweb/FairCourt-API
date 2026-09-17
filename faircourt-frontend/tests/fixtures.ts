import { expect } from "@playwright/test";
import type { Page } from "@playwright/test";
import type { MeResponse } from "../src/api/me";
import type { Slot, Reservation } from "../src/api/reservations";
import type { Facility } from "../src/api/facilities";
import type { UnlockProposal } from "../src/api/unlock";

export const day = "2026-09-07";
export const stamp = (hour: number, date = day) =>
  `${date}T${String(hour).padStart(2, "0")}:00:00+02:00`;
const makeFacility = (
  id: number,
  slug: string,
  name: string,
  category: string,
  priority: number,
): Facility => ({
  id,
  slug,
  name,
  category,
  description: `${name} comunitario`,
  icon: category === "Deporte" ? "court" : "calendar",
  priority,
  is_reservable: true,
  opening_hour: 9,
  closing_hour: 22,
  slot_duration_minutes: 60,
});
export const facilities: Facility[] = [
  makeFacility(1, "padel", "Pádel", "Deporte", 10),
  makeFacility(2, "tenis", "Tenis", "Deporte", 20),
  makeFacility(3, "pergola-1", "Pérgola 1", "Encuentros", 30),
  makeFacility(4, "pergola-2", "Pérgola 2", "Encuentros", 31),
  makeFacility(5, "pergola-3", "Pérgola 3", "Encuentros", 32),
  makeFacility(6, "pergola-4", "Pérgola 4", "Encuentros", 33),
  makeFacility(7, "petanca", "Petanca", "Deporte", 40),
  makeFacility(8, "polideportiva", "Fútbol / baloncesto / polideportiva", "Deporte", 41),
  makeFacility(9, "barra-bar", "Barra de bar", "Encuentros", 50),
  makeFacility(10, "mesa-1", "Mesa 1", "Mesas", 60),
  makeFacility(11, "mesa-2", "Mesa 2", "Mesas", 61),
  makeFacility(12, "mesa-3", "Mesa 3", "Mesas", 62),
  makeFacility(13, "mesa-4", "Mesa 4", "Mesas", 63),
  makeFacility(14, "sala-multiusos", "Sala multiusos · Tenis de mesa", "Interior", 70),
  makeFacility(15, "sauna", "Sauna", "Bienestar", 80),
];
export function slotsFor(date: string): Slot[] {
  return [9, 10, 11, 12, 16, 17, 18, 19]
    .map((hour, index) => ({
      start_at: stamp(hour, date),
      end_at: stamp(hour + 1, date),
      status: [1, 2, 4].includes(index) ? "OCCUPIED" : "FREE",
      reservation_id: index === 2 ? 11 : null,
      is_mine: index === 2,
      can_book: ![1, 2, 4, 7].includes(index),
      can_join_waitlist: [1, 4].includes(index),
      waitlist_count: index === 1 ? 2 : 0,
      in_waitlist: index === 4,
      book_reason:
        index === 7
          ? "Límite semanal alcanzado"
          : [1, 2, 4].includes(index)
            ? "La franja ya está reservada"
            : null,
      waitlist_reason:
        index === 4
          ? "Ya estás en la lista de espera"
          : index === 2
            ? "Es tu propia reserva"
            : null,
    }))
    .map((slot) =>
      slot.in_waitlist ? { ...slot, can_join_waitlist: false } : slot,
    );
}
export const initialReservations: Reservation[] = [
  {
    id: 11,
    household_id: 1,
    facility_id: 1,
    facility: facilities[0],
    start_at: stamp(11),
    end_at: stamp(12),
    status: "ACTIVE",
    real_status: "ACTIVE",
    created_at: stamp(8),
  },
  {
    id: 12,
    household_id: 1,
    facility_id: 2,
    facility: facilities[1],
    start_at: stamp(10, "2026-09-04"),
    end_at: stamp(11, "2026-09-04"),
    status: "ACTIVE",
    real_status: "FINISHED",
    created_at: stamp(8, "2026-09-03"),
  },
  {
    id: 13,
    household_id: 1,
    facility_id: 1,
    facility: facilities[0],
    start_at: stamp(16, "2026-09-02"),
    end_at: stamp(17, "2026-09-02"),
    status: "NO_SHOW",
    real_status: "NO_SHOW",
    created_at: stamp(8, "2026-09-01"),
  },
  {
    id: 14,
    household_id: 1,
    facility_id: 3,
    facility: facilities[2],
    start_at: stamp(18, "2026-09-03"),
    end_at: stamp(19, "2026-09-03"),
    status: "CANCELLED",
    real_status: "CANCELLED",
    created_at: stamp(8, "2026-09-01"),
  },
];
export function proposal(
  id: number,
  status = "OPEN",
  own = false,
): UnlockProposal {
  return {
    id,
    target_household_id: own ? 1 : id + 1,
    target_household_code: own ? "A1" : `B${id}`,
    created_by_user_id: id,
    reason:
      "No pude asistir por un imprevisto familiar. Solicito volver a reservar y me comprometo a avisar con antelación.",
    status,
    created_at: stamp(8, "2026-09-06"),
    closes_at: stamp(20, "2026-09-08"),
    resolved_at: status === "OPEN" ? null : stamp(9),
  };
}
export async function setup(
  page: Page,
  options: { authenticated?: boolean; suspended?: boolean } = {},
) {
  await page.clock.setFixedTime(new Date("2026-09-07T08:00:00+02:00"));
  const me: MeResponse = {
    id: 1,
    email: "vecino@faircourt.es",
    household_id: 1,
    household_code: "A1",
    community_id: 1,
    community_slug: "faircourt",
    community_name: "Comunidad FairCourt",
    strikes: 0,
    suspended_until: options.suspended ? stamp(20, "2026-09-09") : null,
    active_waitlists_count: 1,
  };
  const state = {
    me,
    reservations: structuredClone(initialReservations),
    proposals: [
      proposal(1),
      proposal(2),
      proposal(3, "OPEN", true),
      proposal(4, "APPROVED"),
    ],
    notifications: [
      {
        id: 1,
        user_id: 1,
        household_id: 1,
        type: "RESERVATION_CREATED",
        message:
          "Tu reserva para hoy a las 11:00 está confirmada. ¡Nos vemos en la pista!",
        is_read: false,
        created_at: stamp(7),
      },
      {
        id: 2,
        user_id: 1,
        household_id: 1,
        type: "WAITLIST_JOINED",
        message:
          "Ya estás en la lista de espera. Te avisaremos si llega tu turno.",
        is_read: false,
        created_at: stamp(6),
      },
      {
        id: 3,
        user_id: 1,
        household_id: 1,
        type: "RESERVATION_CANCELLED",
        message: "Tu reserva anterior se canceló correctamente.",
        is_read: true,
        created_at: stamp(8, "2026-09-04"),
      },
    ],
    audit: [
      {
        id: 1,
        event: "RESERVATION_CREATED",
        household_id: 1,
        user_id: 1,
        reservation_id: 11,
        metadata_json: JSON.stringify({
          email: "vecino@faircourt.es",
          start_at: stamp(11),
          rules: { weekly: true },
          strikes: 0,
        }),
        created_at: stamp(7),
      },
      {
        id: 2,
        event: "WAITLIST_JOINED",
        household_id: 1,
        user_id: 1,
        reservation_id: null,
        metadata_json: JSON.stringify({ start_at: stamp(16) }),
        created_at: stamp(6),
      },
      {
        id: 3,
        event: "OTP_VERIFIED",
        household_id: 1,
        user_id: 1,
        reservation_id: null,
        metadata_json: null,
        created_at: stamp(5),
      },
    ],
    slots: new Map<string, Slot[]>(),
    requests: [] as {
      path: string;
      method: string;
      body: unknown;
      authorization: string | undefined;
    }[],
    fail: new Map<string, number>(),
    delays: new Map<string, number>(),
    networkDown: false,
    adminCommunities: [
      {
        id: 1,
        slug: "gran-parque",
        name: "Gran Parque",
        timezone: "Europe/Madrid",
        is_active: true,
        household_count: 500,
        facility_count: 3,
      },
      {
        id: 2,
        slug: "community-b",
        name: "Comunidad B",
        timezone: "Europe/Madrid",
        is_active: true,
        household_count: 240,
        facility_count: 1,
      },
    ],
  };
  if (options.authenticated !== false)
    await page.addInitScript(() => {
      if (!sessionStorage.getItem("test-initialized")) {
        localStorage.setItem("faircourt_token", "test-token");
        sessionStorage.setItem("test-initialized", "1");
      }
    });
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const key = path + url.search;
    if (state.networkDown) {
      await route.abort("internetdisconnected");
      return;
    }
    if (request.method() === "OPTIONS") {
      await route.fulfill({
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "*",
        },
      });
      return;
    }
    state.requests.push({
      path: key,
      method: request.method(),
      body: request.postDataJSON(),
      authorization: request.headers()["authorization"],
    });
    const delay =
      state.delays.get(key) ?? (request.method() === "POST" ? 100 : 0);
    if (delay) await new Promise((resolve) => setTimeout(resolve, delay));
    if (state.fail.has(key)) {
      await route.fulfill({
        status: state.fail.get(key),
        json: { detail: "Operación rechazada por las reglas de la comunidad." },
      });
      return;
    }
    let data: unknown;
    if (path === "/admin/auth/request-otp")
      data = { message: "Si el correo está autorizado, se ha generado un código de acceso." };
    else if (path === "/admin/auth/verify-otp")
      data = {
        access_token: "admin-verified-token",
        token_type: "bearer",
        expires_at: stamp(23),
      };
    else if (path === "/admin/me")
      data = { id: 90, email: "admin@faircourt.es", role: "platform_admin" };
    else if (path === "/admin/communities") data = state.adminCommunities;
    else if (path.match(/^\/admin\/communities\/\d+\/select$/))
      data = state.adminCommunities.find(
        (community) => community.id === Number(path.split("/")[3]),
      );
    else if (path.match(/^\/admin\/communities\/\d+\/policy$/))
      data = {
        community_id: Number(path.split("/")[3]),
        booking_window_days: 7,
        max_active_reservations_per_week: 2,
        cancellation_limit_hours: 4,
        checkin_window_minutes: 15,
        max_strikes: 2,
        suspension_days: 14,
        max_active_waitlists_per_week: 3,
        prime_time_start_hour: 18,
        prime_time_end_hour: 21,
        cooldown_days: 3,
        unlock_voting_enabled: true,
        unlock_voting_hours: 48,
        unlock_min_yes_votes: 2,
      };
    else if (path.match(/^\/admin\/communities\/\d+\/audit$/))
      data = [
        {
          id: 40,
          event: "ADMIN_COMMUNITY_SELECTED",
          user_id: 90,
          household_id: null,
          reservation_id: null,
          metadata_json: JSON.stringify({ community_slug: "gran-parque" }),
          created_at: stamp(8),
        },
      ];
    else if (path === "/auth/request-otp")
      data = { message: "Código de acceso generado." };
    else if (path === "/auth/verify-otp")
      data = {
        access_token: "verified-token",
        token_type: "bearer",
        expires_at: stamp(23),
      };
    else if (path === "/me") data = state.me;
    else if (path === "/facilities") data = facilities;
    else if (path === "/reservations/slots") {
      const date = url.searchParams.get("day")!;
      if (!state.slots.has(date)) state.slots.set(date, slotsFor(date));
      data = state.slots.get(date);
    } else if (path === "/reservations/me") data = state.reservations;
    else if (path === "/reservations" || path === "/reservations/waitlist") {
      const body = request.postDataJSON();
      const start = body.start_at;
      const date = start.slice(0, 10);
      const slot = state.slots.get(date)?.find((row) => row.start_at === start);
      if (slot) {
        if (path.endsWith("waitlist")) {
          slot.in_waitlist = true;
          slot.can_join_waitlist = false;
          slot.waitlist_count++;
          state.me.active_waitlists_count =
            (state.me.active_waitlists_count ?? 0) + 1;
        } else {
          slot.is_mine = true;
          slot.status = "OCCUPIED";
          slot.can_book = false;
          slot.can_join_waitlist = false;
        }
      }
      const selectedFacility = facilities.find((item) => item.id === body.facility_id)!;
      data = {
        id: 22,
        household_id: 1,
        facility_id: selectedFacility.id,
        facility: selectedFacility,
        start_at: start,
        end_at: stamp(new Date(start).getHours() + 1, date),
        created_at: start,
        status: "ACTIVE",
      };
    } else if (path.endsWith("/cancel")) {
      const row = state.reservations.find(
        (row) => row.id === Number(path.split("/")[2]),
      )!;
      row.status = "CANCELLED";
      row.real_status = "CANCELLED";
      data = row;
    } else if (path.endsWith("/checkin-qr"))
      data = {
        reservation_id: Number(path.split("/")[2]),
        checkin_url:
          "http://127.0.0.1:8000/reservations/checkin/scan?token=signed-test-link",
        expires_at: stamp(12),
      };
    else if (path === "/reservations/checkin/scan")
      data = { message: "Asistencia confirmada" };
    else if (path === "/notifications/me") data = state.notifications;
    else if (path.endsWith("/read")) {
      const row = state.notifications.find(
        (row) => row.id === Number(path.split("/")[2]),
      )!;
      row.is_read = true;
      data = row;
    } else if (path === "/audit/me") data = state.audit;
    else if (path === "/unlock/proposals") data = state.proposals;
    else if (path === "/unlock/proposal") {
      const row = {
        ...proposal(9, "OPEN", true),
        reason: request.postDataJSON().reason,
      };
      state.proposals.push(row);
      data = row;
    } else if (path.endsWith("/vote"))
      data = {
        id: 1,
        proposal_id: Number(path.split("/")[3]),
        voter_household_id: 1,
        vote: request.postDataJSON().vote,
        created_at: stamp(8),
      };
    else {
      await route.fulfill({
        status: 404,
        json: { detail: "Unexpected test endpoint: " + key },
      });
      return;
    }
    await route.fulfill({
      json: data,
      headers: { "Access-Control-Allow-Origin": "*" },
    });
  });
  return state;
}
export async function navigate(page: Page, name: string) {
  const mobile = (page.viewportSize()?.width ?? 1440) < 900;
  if (
    mobile &&
    ["Notificaciones", "Auditoría", "Desbloqueos", "Contacto"].includes(name)
  ) {
    await page
      .getByRole("navigation", { name: "Navegación móvil" })
      .getByRole("button", { name: "Más", exact: true })
      .click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: new RegExp(name) })
      .click();
  } else
    await page
      .getByRole("navigation", {
        name: mobile ? "Navegación móvil" : "Navegación principal",
        exact: true,
      })
      .getByRole("button", { name: new RegExp(name) })
      .click();
}
export async function start(page: Page) {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Qué bien tenerte de vuelta." }),
  ).toBeVisible();
}
