import { useState } from "react";
import type { MeResponse } from "../api/me";
import {
  castUnlockVote,
  createUnlockProposal,
  getUnlockProposals,
} from "../api/unlock";
import type { UnlockProposal } from "../api/unlock";
import { useResource } from "../hooks/useResource";
import { useAction } from "../hooks/useAction";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import { dateTime, label, tone } from "../utils/format";
import {
  Badge,
  Button,
  Empty,
  Feedback,
  Icon,
  Loading,
  PageHeader,
  RefreshButton,
  ResourceError,
} from "./ui";
import { CacheStamp } from "./CacheStamp";
export function UnlockPanel({
  me,
  refreshKey,
  onChanged,
}: {
  me: MeResponse;
  refreshKey: number;
  onChanged: () => void;
}) {
  const resource = useResource(getUnlockProposals, "unlock", refreshKey);
  const action = useAction();
  const online = useOnlineStatus();
  const [reason, setReason] = useState("");
  const rows = [...(resource.data ?? [])].sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  );
  async function create(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    await action.run(async () => {
      if (!reason.trim())
        throw new Error("Indica un motivo para solicitar el desbloqueo.");
      await createUnlockProposal({ reason: reason.trim() });
      setReason("");
      onChanged();
    }, "Tu propuesta de desbloqueo se ha creado correctamente.");
  }
  async function vote(row: UnlockProposal, value: "YES" | "NO") {
    await action.run(
      async () => {
        await castUnlockVote(row.id, { vote: value });
        onChanged();
      },
      `Tu voto ${value === "YES" ? "a favor" : "en contra"} se ha registrado.`,
    );
  }
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="DECIDIMOS EN COMUNIDAD"
        title="Volver al juego."
        description="Solicita o vota un desbloqueo excepcional. Tu comunidad tiene la palabra."
        action={
          <RefreshButton loading={resource.loading} onClick={resource.reload} />
        }
      />
      <Feedback error={action.error} message={action.message} />
      <ResourceError error={resource.error} retry={resource.reload} />
      <CacheStamp cacheKey="faircourt_cache_unlock_proposals" />
      <section
        className={`panel unlock-intro ${me.suspended_until ? "suspended" : ""}`}
      >
        <span className="empty-icon">
          <Icon name={me.suspended_until ? "unlock" : "shield"} />
        </span>
        <div>
          <h2>
            {me.suspended_until
              ? "Solicita una nueva oportunidad."
              : "Tu vivienda está activa."}
          </h2>
          <p className="muted">
            {me.suspended_until
              ? `Suspensión hasta el ${dateTime(me.suspended_until)}. Puedes proponer un desbloqueo excepcional.`
              : "No necesitas solicitar un desbloqueo. Puedes participar en las propuestas de otros vecinos."}
          </p>
          {me.suspended_until && (
            <form onSubmit={create} className="proposal-form">
              <label htmlFor="unlock-reason">Motivo de la solicitud</label>
              <textarea
                id="unlock-reason"
                rows={4}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Cuéntale a tu comunidad por qué solicitas el desbloqueo…"
                required
              />
              <Button type="submit" disabled={!online || action.busy}>
                {action.busy ? "Enviando…" : "Crear propuesta"}
                <Icon name="arrow" />
              </Button>
            </form>
          )}
        </div>
      </section>
      <section>
        <div className="section-heading">
          <h2>
            Propuestas de la comunidad{" "}
            <span className="section-count">{rows.length}</span>
          </h2>
        </div>
        {resource.loading && !resource.data ? (
          <Loading />
        ) : !rows.length && !resource.error ? (
          <div className="panel">
            <Empty icon="users" title="Sin propuestas por ahora">
              Las solicitudes de desbloqueo de la comunidad aparecerán aquí.
            </Empty>
          </div>
        ) : (
          <div className="proposals-grid">
            {rows.map((row) => {
              const own = row.target_household_id === me.household_id;
              return (
                <article
                  className="panel proposal-card"
                  key={row.id}
                  aria-label={`Propuesta #${row.id}`}
                >
                  <div className="section-heading">
                    <Badge tone={tone(row.status)}>{label(row.status)}</Badge>
                    {own && (
                      <span className="small own-proposal">Tu propuesta</span>
                    )}
                  </div>
                  <div className="proposal-house">
                    <span className="avatar">{row.target_household_code}</span>
                    <div>
                      <h3>Vivienda {row.target_household_code}</h3>
                      <span className="small muted">
                        Solicitud de desbloqueo
                      </span>
                    </div>
                  </div>
                  <p className="proposal-reason">{row.reason}</p>
                  <dl className="proposal-dates">
                    <div>
                      <dt>Creada</dt>
                      <dd>{dateTime(row.created_at)}</dd>
                    </div>
                    <div>
                      <dt>Cierre</dt>
                      <dd>{dateTime(row.closes_at)}</dd>
                    </div>
                    {row.resolved_at && (
                      <div>
                        <dt>Resuelta</dt>
                        <dd>{dateTime(row.resolved_at)}</dd>
                      </div>
                    )}
                  </dl>
                  <div className="vote-actions">
                    <Button
                      disabled={
                        !online || own || row.status !== "OPEN" || action.busy
                      }
                      onClick={() => vote(row, "YES")}
                    >
                      <Icon name="check" />A favor
                    </Button>
                    <Button
                      variant="secondary"
                      disabled={
                        !online || own || row.status !== "OPEN" || action.busy
                      }
                      onClick={() => vote(row, "NO")}
                    >
                      <Icon name="close" />
                      En contra
                    </Button>
                  </div>
                  {own && row.status === "OPEN" && (
                    <p className="small muted">
                      No puedes votar tu propia propuesta.
                    </p>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
