import type { MeResponse } from "../api/me";

type DashboardHomeProps = {
    me: MeResponse;
};

/**
 * Vista de inicio del usuario autenticado.
 *
 * Muestra información resumida de la vivienda:
 * - email asociado,
 * - identificador de vivienda,
 * - strikes,
 * - suspensión activa,
 * - waitlists activas.
 */
export function DashboardHome({ me }: DashboardHomeProps) {
    return (
        <section className="space-y-6">
            <header className="rounded-2xl bg-white p-6 shadow">
                <h2 className="text-3xl font-bold text-slate-900">Panel principal</h2>
                <p className="mt-2 text-slate-600">
                    Resumen del estado actual de tu vivienda dentro del sistema.
                </p>
            </header>

            <div className="grid gap-6 md:grid-cols-3">
                <article className="rounded-2xl bg-white p-6 shadow">
                    <p className="text-sm font-medium text-slate-500">Email</p>
                    <p className="mt-2 text-xl font-bold text-slate-900">{me.email}</p>
                </article>

                <article className="rounded-2xl bg-white p-6 shadow">
                    <p className="text-sm font-medium text-slate-500">Vivienda</p>
                    <p className="mt-2 text-xl font-bold text-slate-900">
                        ID {me.household_id}
                    </p>
                </article>

                <article className="rounded-2xl bg-white p-6 shadow">
                    <p className="text-sm font-medium text-slate-500">Strikes</p>
                    <p className="mt-2 text-xl font-bold text-slate-900">
                        {me.strikes ?? 0}
                    </p>
                </article>

                <article className="rounded-2xl bg-white p-6 shadow md:col-span-2">
                    <p className="text-sm font-medium text-slate-500">
                        Estado de suspensión
                    </p>
                    <p className="mt-2 text-lg font-semibold text-slate-900">
                        {me.suspended_until
                            ? `Suspendida hasta ${new Date(
                                me.suspended_until
                            ).toLocaleString("es-ES")}`
                            : "Sin suspensión activa"}
                    </p>
                </article>

                <article className="rounded-2xl bg-white p-6 shadow">
                    <p className="text-sm font-medium text-slate-500">
                        Waitlists activas
                    </p>
                    <p className="mt-2 text-xl font-bold text-slate-900">
                        {me.active_waitlists_count ?? 0}
                    </p>
                </article>
            </div>
        </section>
    );
}