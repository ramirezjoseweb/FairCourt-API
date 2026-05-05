from __future__ import annotations

import random
import csv
import os
import matplotlib.pyplot as plt

from dataclasses import dataclass, field
from datetime import date, timedelta
from collections import defaultdict




HOUSEHOLDS = [
    "BJ2", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8",
    "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8",
    "AT1", "AT2", "BJ1"
]

DAYS = 14
SLOTS = [18, 19, 20, 21]
PRIME_TIME_SLOTS = {18, 19, 20}

WEEKLY_CAP = 2  # Maximo de reservas por semana
COOLDOWN_DAYS = 3  # Cooldown entre reservas en prime time

POLICY_B_PRIME_TIME_QUOTA_PER_DAY = 1  # Maximo de reservas en prime time por dia
NO_SHOW_PROBABILITY = 0.08  # Probabilidad de no presentarse

CHECKIN_WINDOW_MINUTES = 15 # Ventana de check-in

RANDOM_SEED = 42  # Semilla para la aleatoriedad

# Representa una solicitud de reserva (vivienda, día, hora)
@dataclass
class Request:
    household: str
    day: date
    hour: int
    requested_hour: int 

# Guarda el resultado de una política
@dataclass
class SimulationResult:
    policy_name: str
    accepted: list[Request] = field(default_factory=list)
    rejected: list[tuple[Request, str]] = field(default_factory=list)
    no_shows: list[Request] = field(default_factory=list)
    wait_times: list[int] = field(default_factory=list)
    waitlist_promotions: int = 0 
    waitlist_entries: int = 0 


def generate_demands(start_day: date) -> list[Request]:
    """
    Genera solicitudes simulando un periodo de alta demanda:
    - más demanda en fines de semana
    - más preferencia por prime-time
    """
    requests: list[Request] = [] # Lista de solicitudes

    # Pesos de probabilidad por hora (más probabilidad en prime time)
    slot_weights = {
        18: 0.30,
        19: 0.35,
        20: 0.25,
        21: 0.10,
    }
    
    # Genera solicitudes para cada día
    for i in range(DAYS):
        current_day = start_day + timedelta(days=i)
        is_weekend = current_day.weekday() >= 5 # 5 y 6 son fin de semana

        base_probability = 0.35 # Probabilidad base de generar una solicitud
        if is_weekend:
            base_probability *= 0.65 # Mayor probabilidad de generar una solicitud los fines de semana

        # Genera solicitudes para cada vivienda
        for household in HOUSEHOLDS:
            if random.random() < base_probability:
                hour = random.choices(
                    population=list(slot_weights.keys()),
                    weights=list(slot_weights.values()),
                    k=1
                )[0]

                requested_hour = random.choice(SLOTS)

                requests.append(Request(
                    household,
                    current_day,
                    hour,
                    requested_hour
                ))
    # Ordena aleatoriamente las solicitudes (simula llegadas en distintos momentos)
    random.shuffle(requests)
    return requests

# Genera una clave única por semana (año, semana ISO)
def week_key(day: date) -> tuple[int, int]:
    iso = day.isocalendar()
    return iso.year, iso.week

def gini(values: list[int]) -> float:
    """
    Calcula el índice de Gini.
    0 = reparto totalmente igualitario.
    1 = reparto muy desigual.
    """
    if not values:
        return 0.0

    # Ordena las solicitudes de forma creciente
    sorted_values = sorted(values)
    n = len(sorted_values) # Número de solicitudes
    total = sum(sorted_values) # Suma total de solicitudes

    if total == 0: # Si no hay solicitudes
        return 0.0 # El reparto es totalmente igualitario

    # Suma ponderada de las solicitudes (cuanto mayor el índice, más desigual es el reparto)
    weighted_sum = sum((i + 1) * value for i, value in enumerate(sorted_values)) 
    
    # Índice de Gini
    return (2 * weighted_sum) / (n * total) - (n + 1) / n

# Calcula la media de una lista de números
def average(values: list[int]) -> float: 
    # Si la lista está vacía, devuelve 0.0
    if not values: 
        return 0.0
    # Devuelve la media de la lista
    return sum(values) / len(values)

def simulate_policy_a(requests: list[Request]) -> SimulationResult:
    """
    Política A:
    - cupo semanal máximo por vivienda
    - cooldown por franja prime-time
    - waitlist cuando el slot está ocupado
    - promoción por no-show
    """
    # Crea un resultado para la política A
    result = SimulationResult(policy_name="A_weekly_cap_cooldown")
    # Conjunto de franjas ocupadas
    occupied_slots: dict[tuple[date, int], Request] = {}
    # Cola de espera por franja
    waitlists: dict[tuple[date, int], list[Request]] = defaultdict(list)
    # Contador de reservas por semana
    weekly_count = defaultdict(int)
    # Último día que se usó una franja prime-time por vivienda
    last_prime_slot_use = {}
    # Solicitudes pendientes de no-show
    pending_no_shows = []

    # Itera sobre las solicitudes ordenadas por día y hora
    for req in sorted(requests, key=lambda r: (r.day, r.hour)):
        # Genera una clave por franja
        slot_key = (req.day, req.hour)
        # Genera una clave por semana
        household_week = (req.household, week_key(req.day))

        # Si la vivienda ha alcanzado el cupo semanal
        if weekly_count[household_week] >= WEEKLY_CAP:
            result.rejected.append((req, "WEEKLY_CAP_REACHED"))
            continue

        if req.hour in PRIME_TIME_SLOTS:
            # Genera una clave por vivienda y franja
            cooldown_key = (req.household, req.hour)
            last_day = last_prime_slot_use.get(cooldown_key)

            # Si la vivienda tiene en cooldown la franja
            if last_day is not None and (req.day - last_day).days < COOLDOWN_DAYS:
                result.rejected.append((req, "COOLDOWN_ACTIVE"))
                continue
        # Si la franja está ocupada
        if slot_key in occupied_slots:
            waitlists[slot_key].append(req)
            result.waitlist_entries += 1
            continue
        # Asignación de la franja
        occupied_slots[slot_key] = req
        # Incrementa el contador de reservas de la vivienda
        weekly_count[household_week] += 1

        # Actualiza el último día que se usó la franja prime-time
        if req.hour in PRIME_TIME_SLOTS:
            last_prime_slot_use[(req.household, req.hour)] = req.day
        # Probabilidad de no presentarse
        if random.random() < NO_SHOW_PROBABILITY:
            pending_no_shows.append((slot_key, req))
        else:
            result.accepted.append(req)

    for slot_key, req in pending_no_shows:
        result.no_shows.append(req)
        promoted = promote_from_waitlist_policy_a(
            slot_key=slot_key,
            waitlists=waitlists,
            occupied_slots=occupied_slots,
            weekly_count=weekly_count,
            last_prime_slot_use=last_prime_slot_use,
            promotion_day=req.day,
            result=result,
        )

        if not promoted:
            occupied_slots.pop(slot_key, None)

    return result

def promote_from_waitlist_policy_a(
    slot_key: tuple[date, int],
    waitlists: dict[tuple[date, int], list[Request]],
    occupied_slots: dict[tuple[date, int], Request],
    weekly_count,
    last_prime_slot_use,
    promotion_day: date,
    result: SimulationResult,
) -> bool:
    """
    Promociona una solicitud desde la lista de espera a la franja ocupada.
    
    Args:
        slot_key: Clave de la franja.
        waitlists: Diccionario con las listas de espera por franja.
        occupied_slots: Diccionario con las franjas ocupadas.
        weekly_count: Contador de reservas por semana.
        last_prime_slot_use: Último día que se usó una franja prime-time por vivienda.
        promotion_day: Día de la promoción.
        result: Resultado de la simulación.

    Returns:
        bool: True si se promocionó una solicitud, False en caso contrario.
    """
    # Obtiene la lista de espera para la franja
    waiting = waitlists.get(slot_key, [])

    # Itera sobre las solicitudes en la lista de espera
    while waiting:
        candidate = waiting.pop(0)
        # Genera una clave por semana
        household_week = (candidate.household, week_key(candidate.day))

        # Si la vivienda ha alcanzado el cupo semanal
        if weekly_count[household_week] >= WEEKLY_CAP:
            result.rejected.append((candidate, "WAITLIST_WEEKLY_CAP_REACHED"))
            continue

        # Si la vivienda tiene en cooldown la franja
        if candidate.hour in PRIME_TIME_SLOTS:
            cooldown_key = (candidate.household, candidate.hour)
            last_day = last_prime_slot_use.get(cooldown_key)

            # Si la vivienda tiene en cooldown la franja
            if last_day is not None and (candidate.day - last_day).days < COOLDOWN_DAYS:
                result.rejected.append((candidate, "WAITLIST_COOLDOWN_ACTIVE"))
                continue

            last_prime_slot_use[cooldown_key] = candidate.day
        # Asignación de la franja
        occupied_slots[slot_key] = candidate
        # Incrementa el contador de reservas de la vivienda
        weekly_count[household_week] += 1
        # Añade la solicitud aceptada
        result.accepted.append(candidate)
        # Incrementa el contador de promociones
        result.waitlist_promotions += 1
        # Calcula el tiempo de espera en horas
        wait_hours = slot_key[1] - candidate.requested_hour
        wait_hours = max(0, wait_hours)
        result.wait_times.append(wait_hours)

    return False


def simulate_policy_b(requests: list[Request], start_day: date) -> SimulationResult:
    """
    Política B:
    - cuota prime-time por vivienda y día
    - ventana de apertura diaria modelada procesando día a día
    - waitlist cuando el slot está ocupado
    - promoción por no-show
    """
    # Crea un resultado para la política B
    result = SimulationResult(policy_name="B_prime_quota_daily_window")

    # Conjunto de franjas ocupadas
    occupied_slots: dict[tuple[date, int], Request] = {}
    # Cola de espera por franja
    waitlists: dict[tuple[date, int], list[Request]] = defaultdict(list)

    # Contador de reservas prime-time por vivienda y día
    daily_prime_count = defaultdict(int)
    
    # Solicitudes pendientes de no-show
    pending_no_shows = []

    # Itera sobre las solicitudes ordenadas por día y hora
    for req in sorted(requests, key=lambda r: (r.day, r.hour)):
        # Genera una clave por franja
        slot_key = (req.day, req.hour)
        # Genera una clave por vivienda y día
        household_day = (req.household, req.day)

        # Si la franja es prime-time
        if req.hour in PRIME_TIME_SLOTS:
            # Si la vivienda ha alcanzado el cupo de prime-time por día
            if daily_prime_count[household_day] >= POLICY_B_PRIME_TIME_QUOTA_PER_DAY:
                result.rejected.append((req, "PRIME_TIME_DAILY_QUOTA_REACHED"))
                continue

        # Si la franja está ocupada
        if slot_key in occupied_slots:
            waitlists[slot_key].append(req)
            result.waitlist_entries += 1
            continue

        # Asignación de la franja
        occupied_slots[slot_key] = req

        # Actualiza el contador de reservas prime-time por vivienda y día
        if req.hour in PRIME_TIME_SLOTS:
            daily_prime_count[household_day] += 1

        # Probabilidad de no presentarse
        if random.random() < NO_SHOW_PROBABILITY:
            pending_no_shows.append((slot_key, req))
        else:
            result.accepted.append(req)
            
    # Intenta promocionar desde la lista de espera
    for slot_key, req in pending_no_shows:
        result.no_shows.append(req)
        promoted = promote_from_waitlist_policy_b(
            slot_key=slot_key,
            waitlists=waitlists,
            occupied_slots=occupied_slots,
            daily_prime_count=daily_prime_count,
            promotion_day=req.day,
            result=result,
        )

        if not promoted:
            occupied_slots.pop(slot_key, None)

    return result   

def promote_from_waitlist_policy_b(
    slot_key: tuple[date, int],
    waitlists: dict[tuple[date, int], list[Request]],
    occupied_slots: dict[tuple[date, int], Request],
    daily_prime_count: dict[tuple[str, date], int],
    promotion_day: date,
    result: SimulationResult,
) -> bool:
    """
    Promociona una solicitud desde la lista de espera a la franja ocupada.
    
    Args:
        slot_key: Clave de la franja.
        waitlists: Diccionario con las listas de espera por franja.
        occupied_slots: Diccionario con las franjas ocupadas.
        daily_prime_count: Contador de reservas prime-time por vivienda y día.
        promotion_day: Día de la promoción.
        result: Resultado de la simulación.

    Returns:
        bool: True si se promocionó una solicitud, False en caso contrario.
    """
    # Obtiene la lista de espera para la franja
    waiting = waitlists.get(slot_key, [])

    # Itera sobre las solicitudes en la lista de espera
    while waiting:
        candidate = waiting.pop(0)
        # Genera una clave por vivienda y día
        household_day = (candidate.household, candidate.day)

        # Si la franja es prime-time
        if candidate.hour in PRIME_TIME_SLOTS:
            # Si la vivienda ha alcanzado el cupo de prime-time por día
            if daily_prime_count[household_day] >= POLICY_B_PRIME_TIME_QUOTA_PER_DAY:
                result.rejected.append((candidate, "WAITLIST_PRIME_TIME_DAILY_QUOTA_REACHED"))
                continue
            # Actualiza el contador de reservas prime-time por vivienda y día
            daily_prime_count[household_day] += 1

        # Asignación de la franja
        occupied_slots[slot_key] = candidate
        # Añade la solicitud aceptada
        result.accepted.append(candidate)
        # Incrementa el contador de promociones
        result.waitlist_promotions += 1

        # Tiempo de espera en horas
        wait_hours = slot_key[1] - candidate.requested_hour
        wait_hours = max(0, wait_hours)
        result.wait_times.append(wait_hours)
        

    return False


def summarize(result: SimulationResult) -> dict:
    """
    Resumen de la simulación.
    """
    # Diccionario de reservas por vivienda
    reservations_by_household = {h: 0 for h in HOUSEHOLDS}

    # Itera sobre las solicitudes aceptadas y cuenta las reservas por vivienda
    for req in result.accepted:
        reservations_by_household[req.household] += 1

    # Diccionario de motivos de rechazo
    rejected_by_reason = defaultdict(int)
    for _, reason in result.rejected:
        rejected_by_reason[reason] += 1

    # Número de reservas en franjas prime-time
    prime_time_accepted = sum(1 for r in result.accepted if r.hour in PRIME_TIME_SLOTS)

    # Devuelve el resumen
    return {
        "policy": result.policy_name,
        "accepted_total": len(result.accepted),
        "rejected_total": len(result.rejected),
        "no_shows_total": len(result.no_shows),
        "prime_time_accepted": prime_time_accepted,
        "waitlist_entries": result.waitlist_entries,
        "waitlist_promotions": result.waitlist_promotions,
        "avg_wait_time_hours": round(average(result.wait_times), 2),
        "gini_usage": round(gini(list(reservations_by_household.values())), 4),
        "rejected_by_reason": dict(rejected_by_reason),
        "reservations_by_household": reservations_by_household,
    }

# Exporta el resumen a un archivo CSV
def export_summary_csv(summaries: list[dict], path: str) -> None:
    # Abre el archivo CSV en modo escritura
    with open(path, "w", newline="", encoding="utf-8") as f:
        # Crea un objeto writer
        writer = csv.writer(f)

        # Escribe los encabezados
        writer.writerow([
            "policy",
            "accepted_total",
            "rejected_total",
            "no_shows_total",
            "prime_time_accepted",
            "waitlist_entries",
            "waitlist_promotions",
            "gini_usage",
        ])

        # Escribe las filas
        for s in summaries:
            writer.writerow([
                s["policy"],
                s["accepted_total"],
                s["rejected_total"],
                s["no_shows_total"],
                s["prime_time_accepted"],
                s["waitlist_entries"],
                s["waitlist_promotions"],
                s["gini_usage"],
            ])


# Exporta el uso por vivienda a un archivo CSV
def export_household_usage_csv(summaries: list[dict], path: str) -> None:
    # Abre el archivo CSV en modo escritura
    with open(path, "w", newline="", encoding="utf-8") as f:
        # Crea un objeto writer
        writer = csv.writer(f)
        # Escribe los encabezados
        writer.writerow(["policy", "household", "reservations"])

        # Itera sobre los resúmenes
        for s in summaries:
            # Itera sobre las reservas de cada vivienda
            for household, count in s["reservations_by_household"].items():
                # Escribe la fila con la política, la vivienda y el número de reservas
                writer.writerow([s["policy"], household, count])

def ensure_results_dir() -> str:
    """
    Crea la carpeta de resultados si no existe.
    """
    output_dir = "simulation_results"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def plot_policy_comparison(summaries: list[dict], output_dir: str) -> None:
    """
    Genera una gráfica comparativa de métricas principales entre políticas.
    """
    # Obtiene los nombres de las políticas
    policies = [s["policy"] for s in summaries]

    # Obtiene las métricas de cada política
    accepted = [s["accepted_total"] for s in summaries]
    rejected = [s["rejected_total"] for s in summaries]
    no_shows = [s["no_shows_total"] for s in summaries]
    waitlist_promotions = [s["waitlist_promotions"] for s in summaries]

    # Crea un gráfico para cada métrica
    # Define las posiciones de las barras
    x = range(len(policies))
    width = 0.2

    # Crea la gráfica
    plt.figure(figsize=(10, 6))
    # Añade las barras para cada métrica
    plt.bar([i - width * 1.5 for i in x], accepted, width, label="Reservas aceptadas")
    plt.bar([i - width * 0.5 for i in x], rejected, width, label="Reservas rechazadas")
    plt.bar([i + width * 0.5 for i in x], no_shows, width, label="No-shows")
    plt.bar([i + width * 1.5 for i in x], waitlist_promotions, width, label="Promociones waitlist")

    # Añade los títulos y etiquetas
    plt.xticks(list(x), policies, rotation=10)
    plt.ylabel("Cantidad")
    plt.title("Comparativa general de políticas")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "policy_comparison.png"))
    plt.close()

def plot_gini_comparison(summaries: list[dict], output_dir: str) -> None:
    """
    Genera una gráfica comparativa del índice de Gini.
    """
    # Obtiene los nombres de las políticas
    policies = [s["policy"] for s in summaries]
    # Obtiene el índice de Gini de cada política
    gini_values = [s["gini_usage"] for s in summaries]

    # Crea la gráfica
    plt.figure(figsize=(8, 5))
    # Añade las barras
    plt.bar(policies, gini_values)
    # Añade los títulos y etiquetas
    plt.ylabel("Índice de Gini")
    plt.title("Comparación de equidad entre políticas")
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "gini_comparison.png"))
    plt.close()

def plot_household_usage(summaries: list[dict], output_dir: str) -> None:
    """
    Genera una gráfica de reservas por vivienda para cada política.
    """
    # Obtiene los nombres de las viviendas
    households = list(summaries[0]["reservations_by_household"].keys())

    # Crea una gráfica para cada política
    for summary in summaries:
        # Obtiene el número de reservas por vivienda
        values = [summary["reservations_by_household"][h] for h in households]

        # Crea la gráfica
        plt.figure(figsize=(12, 6))
        # Añade las barras
        plt.bar(households, values)
        # Añade los títulos y etiquetas
        plt.ylabel("Reservas aceptadas")
        plt.xlabel("Vivienda")
        plt.title(f"Distribución de reservas por vivienda - {summary['policy']}")
        plt.xticks(rotation=45)
        plt.tight_layout()

        filename = f"household_usage_{summary['policy']}.png"
        plt.savefig(os.path.join(output_dir, filename))
        plt.close()

def main() -> None:
    # Fija la semilla para que la simulación sea reproducible
    random.seed(RANDOM_SEED)

    # Periodo simulado: agosto, con picos de demanda y fines de semana.
    start_day = date(2026, 8, 1)

    # Genera solicitudes
    requests = generate_demands(start_day)

    # Simula las políticas
    result_a = simulate_policy_a(requests)
    result_b = simulate_policy_b(requests, start_day)

    # Genera los resúmenes
    summaries = [summarize(result_a), summarize(result_b)]

    # Muestra los resúmenes
    for summary in summaries:
        print("\n================================")
        print(f"Política: {summary['policy']}")
        print("================================")
        print(f"Reservas aceptadas: {summary['accepted_total']}")
        print(f"Reservas rechazadas: {summary['rejected_total']}")
        print(f"No-shows: {summary['no_shows_total']}") 
        print(f"Prime-time aceptadas: {summary['prime_time_accepted']}")
        print(f"Entradas en waitlist: {summary['waitlist_entries']}")
        print(f"Promociones desde waitlist: {summary['waitlist_promotions']}")
        print(f"Tiempo medio de espera (horas): {summary['avg_wait_time_hours']}")        
        print(f"Gini de uso: {summary['gini_usage']}")
        print(f"Rechazos por motivo: {summary['rejected_by_reason']}")
        print(f"Reservas por vivienda: {summary['reservations_by_household']}")

    # Exporta los resúmenes
    export_summary_csv(summaries, "fairness_summary.csv")
    export_household_usage_csv(summaries, "fairness_household_usage.csv")

    # Crea la carpeta de resultados
    output_dir = ensure_results_dir() 

    # Genera gráficas de políticas
    plot_policy_comparison(summaries, output_dir)

    # Genera gráficas del índice de Gini
    plot_gini_comparison(summaries, output_dir)

    # Genera gráficas por vivienda
    plot_household_usage(summaries, output_dir)

    # Muestra las gráficas generadas
    print("\nGráficas generadas:")
    print("- simulation_results/policy_comparison.png")
    print("- simulation_results/gini_comparison.png")
    print("- simulation_results/household_usage_A_weekly_cap_cooldown.png")
    print("- simulation_results/household_usage_B_prime_quota_daily_window.png")

    # Muestra los CSV generados
    print("\nCSV generados:")
    print("- fairness_summary.csv")
    print("- fairness_household_usage.csv")


if __name__ == "__main__":
    main()