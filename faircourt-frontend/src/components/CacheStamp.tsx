import { useOnlineStatus } from "../hooks/useOnlineStatus";
import { getCacheSavedAt } from "../utils/offlineCache";
import { dateTime } from "../utils/format";
export function CacheStamp({ cacheKey }: { cacheKey: string }) {
  const online = useOnlineStatus();
  if (online) return null;
  const saved = getCacheSavedAt(cacheKey);
  return (
    <p className="cache-stamp">
      {saved
        ? `Última información guardada: ${dateTime(saved)}`
        : "No hay información guardada para esta consulta."}
    </p>
  );
}
