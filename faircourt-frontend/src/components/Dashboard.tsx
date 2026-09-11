import { useCallback, useState } from "react";
import { getMe } from "../api/me";
import { getMyNotifications } from "../api/notifications";
import { getFacilities } from "../api/facilities";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import { useReconnectSync } from "../hooks/useReconnectSync";
import { useResource } from "../hooks/useResource";
import { AppLayout } from "./AppLayout";
import type { AppView } from "./AppLayout";
import { DashboardHome } from "./DashboardHome";
import { SlotsPanel } from "./SlotsPanel";
import { MyReservationsPanel } from "./MyReservationsPanel";
import { NotificationsPanel } from "./NotificationsPanel";
import { AuditPanel } from "./AuditPanel";
import { UnlockPanel } from "./UnlockPanel";
import { Empty, Loading, Notice, ResourceError } from "./ui";
import { localDay } from "../utils/format";
export function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [activeView, setActiveView] = useState<AppView>("home");
  const [day, setDay] = useState(localDay);
  const [refresh, setRefresh] = useState(0);
  const [reconnected, setReconnected] = useState(false);
  const online = useOnlineStatus();
  const me = useResource(getMe, "me", refresh);
  const notifications = useResource(
    getMyNotifications,
    "notifications",
    refresh,
  );
  const facilities = useResource(getFacilities, "facilities", refresh);
  const changed = useCallback(() => setRefresh((value) => value + 1), []);
  const reconnect = useCallback(() => {
    changed();
    setReconnected(true);
  }, [changed]);
  useReconnectSync(online, reconnect);
  const unread =
    notifications.data?.filter((item) => !item.is_read).length ?? 0;
  return (
    <AppLayout
      activeView={activeView}
      onChangeView={setActiveView}
      onLogout={onLogout}
      me={me.data}
      unreadCount={unread}
      notifications={notifications}
    >
      {reconnected && online && !me.loading && !me.error && (
        <Notice>Conexión recuperada. Información actualizada.</Notice>
      )}
      <ResourceError error={me.error} retry={me.reload} />
      {!me.data && me.loading && <Loading />}
      {me.data && (
        <>
          {activeView === "home" && (
            <DashboardHome me={me.data} onNavigate={setActiveView} />
          )}
          {activeView === "slots" && (
            <>
              <ResourceError error={facilities.error} retry={facilities.reload} />
              {facilities.loading && !facilities.data ? (
                <Loading />
              ) : facilities.data?.length ? (
                <SlotsPanel
                  facilities={facilities.data}
                  day={day}
                  onDayChange={setDay}
                  refreshKey={refresh}
                  onChanged={changed}
                />
              ) : (
                <div className="panel">
                  <Empty title="No hay instalaciones disponibles">
                    Tu comunidad todavía no ha activado ningún espacio reservable.
                  </Empty>
                </div>
              )}
            </>
          )}
          {activeView === "reservations" && (
            <MyReservationsPanel refreshKey={refresh} onChanged={changed} />
          )}
          {activeView === "notifications" && (
            <NotificationsPanel resource={notifications} onChanged={changed} />
          )}
          {activeView === "audit" && <AuditPanel refreshKey={refresh} />}
          {activeView === "unlock" && (
            <UnlockPanel
              me={me.data}
              refreshKey={refresh}
              onChanged={changed}
            />
          )}
        </>
      )}
    </AppLayout>
  );
}
