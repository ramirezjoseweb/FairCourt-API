// Browser connectivity and API reachability are separate signals.
// A reachable server returning an HTTP error is still online.
let reachable = true;
const listeners = new Set<() => void>();
const notify = () => listeners.forEach(listener => listener());
export const getOnlineSnapshot = () => navigator.onLine && reachable;
export function reportReachability(value: boolean) {
  if (reachable === value) return;
  reachable = value;
  notify();
}
export function retryConnection() {
  reachable = true;
  notify();
}
function onOffline() { notify(); }
function onOnline() { retryConnection(); }
export function subscribeConnection(listener: () => void) {
  if (!listeners.size) {
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
  }
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
    if (!listeners.size) {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    }
  };
}
