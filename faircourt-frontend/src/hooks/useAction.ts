import { useRef, useState } from "react";
import { getOnlineSnapshot } from "../utils/networkStatus";

export function useAction() {
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function run(action: () => Promise<void>, success = "") {
    if (lock.current) return false;
    setError("");
    setMessage("");
    if (!getOnlineSnapshot()) {
      setError("Esta acción requiere conexión a internet.");
      return false;
    }
    lock.current = true;
    setBusy(true);
    try {
      await action();
      setMessage(success);
      return true;
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "No se ha podido completar la acción.",
      );
      return false;
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return { busy, message, error, run };
}
