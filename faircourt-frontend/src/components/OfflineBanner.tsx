import { Button, Icon } from "./ui";
import { retryConnection } from "../utils/networkStatus";
export function OfflineBanner({ isOnline }: { isOnline: boolean }) {
  if (isOnline) return null;
  return (
    <div className="offline-banner" role="status">
      <Icon name="wifi" />
      <span>
        <strong>Estás sin conexión.</strong> Puedes consultar la información
        guardada. Las acciones estarán disponibles cuando vuelvas a conectarte.
      </span>
      {navigator.onLine && (
        <Button variant="secondary" onClick={retryConnection}>
          Reintentar conexión
        </Button>
      )}
    </div>
  );
}
