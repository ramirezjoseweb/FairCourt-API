import { useState } from "react";
import type { ReactNode } from "react";
import type { MeResponse } from "../api/me";
import type { Notification } from "../api/notifications";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import { Brand, Button, Dialog, Icon, ThemeToggle } from "./ui";
import type { IconName } from "./ui";
import { OfflineBanner } from "./OfflineBanner";
import { NotificationPopover } from "./NotificationPopover";
export type AppView =
  "home" | "slots" | "reservations" | "notifications" | "audit" | "unlock";
const navigation: { id: AppView; label: string; icon: IconName }[] = [
  { id: "home", label: "Inicio", icon: "home" },
  { id: "slots", label: "Disponibilidad", icon: "calendar" },
  { id: "reservations", label: "Mis reservas", icon: "ticket" },
  { id: "notifications", label: "Notificaciones", icon: "bell" },
  { id: "audit", label: "Auditoría", icon: "history" },
  { id: "unlock", label: "Desbloqueos", icon: "unlock" },
];
export function AppLayout({
  activeView,
  onChangeView,
  onLogout,
  children,
  me,
  unreadCount,
  notifications,
  theme,
  onToggleTheme,
}: {
  activeView: AppView;
  onChangeView: (view: AppView) => void;
  onLogout: () => void;
  children: ReactNode;
  me?: MeResponse;
  unreadCount: number;
  notifications: {
    data?: Notification[];
    loading: boolean;
    error?: string;
  };
  theme: "light" | "dark";
  onToggleTheme: () => void;
}) {
  const online = useOnlineStatus();
  const [more, setMore] = useState(false);
  const current = navigation.find((item) => item.id === activeView)!;
  function navigate(view: AppView) {
    onChangeView(view);
    setMore(false);
    window.scrollTo({ top: 0 });
  }
  function navItem(item: (typeof navigation)[number]) {
    return (
      <button
        key={item.id}
        className={`nav-item ${activeView === item.id ? "nav-active" : ""}`}
        aria-current={activeView === item.id ? "page" : undefined}
        onClick={() => navigate(item.id)}
      >
        <Icon name={item.icon} />
        <span>{item.label}</span>
        {item.id === "notifications" && unreadCount > 0 && (
          <span className="count">{unreadCount}</span>
        )}
      </button>
    );
  }
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Saltar al contenido
      </a>
      <aside className="sidebar">
        <Brand />
        <p className="sidebar-label">TU ESPACIO DEPORTIVO</p>
        <nav aria-label="Navegación principal">
          {navigation.slice(0, 3).map(navItem)}
          <p className="sidebar-label community-label">COMUNIDAD</p>
          {navigation.slice(3).map(navItem)}
        </nav>
        <div className="sidebar-bottom">
          <div className="fair-play">
            <Icon name="court" />
            <p>La pista es de todos.</p>
            <span>Disfrutémosla con juego limpio.</span>
          </div>
          <div className="household-mini">
            <span className="avatar">{me?.household_code || "FC"}</span>
            <div>
              <strong>
                {me
                  ? `Vivienda ${me.household_code ?? me.household_id}`
                  : "Tu vivienda"}
              </strong>
              <span>Miembro de la comunidad</span>
            </div>
          </div>
          <Button variant="ghost" onClick={onLogout}>
            <Icon name="logout" />
            Cerrar sesión
          </Button>
        </div>
      </aside>
      <div className="app-body">
        <header className="topbar">
          <div className="desktop-breadcrumb">
            Mi comunidad <Icon name="chevron" />
            <strong>{current.label}</strong>
          </div>
          <div className="mobile-brand">
            <Brand />
          </div>
          <div className="topbar-actions">
            <span className={`connection ${online ? "" : "disconnected"}`}>
              <span className="status-dot" />
              {online ? "En línea" : "Sin conexión"}
            </span>
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
            <NotificationPopover
              notifications={notifications.data}
              loading={notifications.loading}
              error={notifications.error}
              unreadCount={unreadCount}
              onViewAll={() => navigate("notifications")}
            />
            <span className="top-avatar">{me?.household_code || "FC"}</span>
          </div>
        </header>
        <OfflineBanner isOnline={online} />
        <main id="main-content" className="main-content" tabIndex={-1}>
          {children}
          <footer className="page-footer">
            <span>FAIRCOURT / COMUNIDAD EN JUEGO</span>
            <span>Un turno para cada uno. Una pista para todos.</span>
          </footer>
        </main>
      </div>
      <nav className="mobile-nav" aria-label="Navegación móvil">
        {navigation.slice(0, 3).map(navItem)}
        <button
          aria-label="Más"
          className={`nav-item ${navigation.slice(3).some((item) => item.id === activeView) || more ? "nav-active" : ""}`}
          onClick={() => setMore(true)}
          aria-haspopup="dialog"
        >
          <Icon name="more" />
          <span>Más</span>
          {unreadCount > 0 && (
            <span className="mobile-count">{unreadCount}</span>
          )}
        </button>
      </nav>
      {more && (
        <Dialog title="Tu comunidad" onClose={() => setMore(false)}>
          <nav className="more-nav" aria-label="Más secciones">
            {navigation.slice(3).map(navItem)}
          </nav>
          <Button variant="ghost" onClick={onLogout}>
            <Icon name="logout" />
            Cerrar sesión
          </Button>
        </Dialog>
      )}
    </div>
  );
}
