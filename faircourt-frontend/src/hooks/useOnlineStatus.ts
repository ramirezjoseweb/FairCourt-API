import { useSyncExternalStore } from "react";
import { getOnlineSnapshot, subscribeConnection } from "../utils/networkStatus";

export function useOnlineStatus() {
  return useSyncExternalStore(subscribeConnection, getOnlineSnapshot);
}