export const dateTime = (value: string) =>
  new Date(value).toLocaleString("es-ES", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
export const time = (value: string) =>
  new Date(value).toLocaleTimeString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
  });
export function localDay(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}
export function offsetDay(day: string, offset: number) {
  const date = new Date(`${day}T12:00:00`);
  date.setDate(date.getDate() + offset);
  return localDay(date);
}
export const longDay = (day: string) =>
  new Date(`${day}T12:00:00`).toLocaleDateString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
export const labels: Record<string, string> = {
  ACTIVE: "Activa",
  CANCELLED: "Cancelada",
  NO_SHOW: "Ausencia",
  FINISHED: "Finalizada",
  OPEN: "Abierta",
  APPROVED: "Aprobada",
  REJECTED: "Rechazada",
  EXPIRED: "Expirada",
  FREE: "Disponible",
  OCCUPIED: "Ocupada",
  BOOKED: "Ocupada",
  RESERVED: "Ocupada",
  RESERVATION_CREATED: "Reserva confirmada",
  RESERVATION_CANCELLED: "Reserva cancelada",
  RESERVATION_NO_SHOW: "Ausencia registrada",
  WAITLIST_JOINED: "Entrada en lista de espera",
  WAITLIST_LEFT: "Salida de lista de espera",
  WAITLIST_PROMOTED: "Tu turno ha llegado",
  WAITLIST_DROPPED: "Lista de espera finalizada",
  CHECKIN_COMPLETED: "Asistencia confirmada",
  STRIKE_ADDED: "Penalización registrada",
  HOUSEHOLD_SUSPENDED: "Vivienda suspendida",
  OTP_REQUESTED: "Código de acceso solicitado",
  OTP_VERIFIED: "Acceso verificado",
  UNLOCK_VOTE_CREATED: "Propuesta de desbloqueo",
  UNLOCK_VOTE_CAST: "Voto registrado",
  UNLOCK_APPROVED: "Desbloqueo aprobado",
  UNLOCK_REJECTED: "Desbloqueo rechazado",
};
export const label = (value: string) => labels[value] || value;
export function tone(value: string): "green" | "amber" | "red" | "neutral" {
  if (
    [
      "ACTIVE",
      "FREE",
      "APPROVED",
      "RESERVATION_CREATED",
      "CHECKIN_COMPLETED",
      "WAITLIST_PROMOTED",
      "UNLOCK_APPROVED",
    ].includes(value)
  )
    return "green";
  if (
    [
      "NO_SHOW",
      "RESERVATION_NO_SHOW",
      "HOUSEHOLD_SUSPENDED",
      "STRIKE_ADDED",
      "REJECTED",
      "UNLOCK_REJECTED",
    ].includes(value)
  )
    return "red";
  if (["OPEN", "WAITLIST_JOINED", "EXPIRED"].includes(value)) return "amber";
  return "neutral";
}
