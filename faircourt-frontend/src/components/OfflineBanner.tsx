import { Button, Icon } from "./ui";
export function OfflineBanner({ isOnline }: { isOnline: boolean }) {
  if (isOnline) return null;
  return (
    <div className="offline-banner" role="status">
      <Icon name="wifi" />
      <span>
        <strong>Estás sin conexión.</strong> Puedes consultar la información
        guardada. Las acciones estarán disponibles cuando vuelvas a conectarte.
      </span>
    </div>
  );
}
