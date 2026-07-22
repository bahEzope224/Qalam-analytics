/**
 * useApi.js — Hook générique pour les appels API.
 *
 * Gère automatiquement les états : loading, data, error.
 * Se redéclenche quand les dépendances changent.
 *
 * @example
 *   const { data, loading, error } = useApi(() => fetchOverview(period), [period]);
 */

import { useState, useEffect, useCallback } from 'react';

/**
 * @param {() => Promise<any>} apiFn — fonction retournant une promesse
 * @param {any[]} deps — dépendances React (comme useEffect)
 */
export function useApi(apiFn, deps = []) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const execute = useCallback(() => {
    setLoading(true);
    setError(null);

    apiFn()
      .then((result) => {
        setData(result);
      })
      .catch((err) => {
        setError(err.message ?? 'Erreur inconnue');
      })
      .finally(() => {
        setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    execute();
  }, [execute]);

  return { data, loading, error, refetch: execute };
}
