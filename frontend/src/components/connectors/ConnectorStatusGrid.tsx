import { useEffect, useState } from 'react';
import { PlugZap } from 'lucide-react';

import { ConnectorStatus, getConnectorStatuses } from '../../services/api';

export function ConnectorStatusGrid() {
  const [connectors, setConnectors] = useState<ConnectorStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadConnectors() {
      try {
        const statuses = await getConnectorStatuses();
        if (isMounted) {
          setConnectors(statuses);
          setError(null);
        }
      } catch {
        if (isMounted) {
          setError('Connector status unavailable');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadConnectors();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
            Connector engine
          </p>
          <h3 className="mt-2 text-lg font-semibold text-white">Event sources</h3>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-white/10 bg-slate-950/70 px-3 py-2 text-sm text-slate-300">
          <PlugZap className="h-4 w-4 text-cyan-300" aria-hidden="true" />
          {connectors.filter((connector) => connector.enabled).length} enabled
        </div>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="h-28 animate-pulse rounded-md border border-white/10 bg-slate-900"
              />
            ))
          : connectors.map((connector) => (
              <article
                key={connector.name}
                className="rounded-md border border-white/10 bg-slate-950/60 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-semibold text-white">{connector.name}</h4>
                    <p className="mt-2 text-sm text-slate-400">
                      {connector.enabled ? 'Enabled' : 'Disabled'}
                    </p>
                  </div>
                  <span
                    className={[
                      'rounded-md px-2.5 py-1 text-xs font-semibold',
                      connector.connected
                        ? 'bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20'
                        : 'bg-slate-700/40 text-slate-300 ring-1 ring-white/10',
                    ].join(' ')}
                  >
                    {connector.connected ? 'Connected' : 'Offline'}
                  </span>
                </div>
              </article>
            ))}
      </div>

      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
    </div>
  );
}
