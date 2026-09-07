import { useCallback, useEffect, useState } from "react";

/** Each request owns its result. Replaced or unmounted requests cannot update the view. */
export function useResource<T>(
  loader: () => Promise<T>,
  identity = "",
  refresh = 0,
) {
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState<{
    identity: string;
    data?: T;
    loading: boolean;
    error?: string;
  }>({ identity, loading: true });
  useEffect(() => {
    let current = true;
    Promise.resolve().then(async () => {
      if (!current) return;
      setState((previous) => ({
        identity,
        data: previous.identity === identity ? previous.data : undefined,
        loading: true,
      }));
      try {
        const data = await loader();
        if (current) setState({ identity, data, loading: false });
      } catch (error) {
        if (current)
          setState((previous) => ({
            ...previous,
            loading: false,
            error:
              error instanceof Error
                ? error.message
                : "No se han podido cargar los datos.",
          }));
      }
    });
    return () => {
      current = false;
    };
  }, [loader, identity, refresh, revision]);
  const reload = useCallback(() => setRevision((value) => value + 1), []);
  return {
    ...(state.identity === identity
      ? state
      : { identity, data: undefined, error: undefined, loading: true }),
    reload,
  };
}
