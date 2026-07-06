import { useEffect, useState } from 'react';
import { ShieldCheck, TriangleAlert } from 'lucide-react';

import { ConnectorDiagnostic, getConnectorDiagnostics } from '../../services/api';

export function ConnectorDiagnosticsPanel() {
  const [diagnostics, setDiagnostics] = useState<ConnectorDiagnostic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadDiagnostics() {
      try {
        const response = await getConnectorDiagnostics();
        if (isMounted) {
          setDiagnostics(response);
          setError(null);
        }
      } catch {
        if (isMounted) {
          setError('Configuration diagnostics unavailable');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadDiagnostics();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Diagnostics</p>
        <h3 className="mt-2 text-lg font-semibold text-white">Configuration readiness</h3>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="h-32 animate-pulse rounded-md border border-white/10 bg-slate-900"
              />
            ))
          : diagnostics.map((diagnostic) => (
              <article
                key={diagnostic.source}
                className="rounded-md border border-white/10 bg-slate-950/60 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-semibold text-white">{diagnostic.name}</h4>
                    <p className="mt-2 text-sm text-slate-400">
                      {diagnostic.enabled ? 'Enabled' : 'Disabled'}
                    </p>
                  </div>
                  <span
                    className={[
                      'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold',
                      diagnostic.ready
                        ? 'bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20'
                        : 'bg-amber-400/10 text-amber-300 ring-1 ring-amber-400/20',
                    ].join(' ')}
                  >
                    {diagnostic.ready ? (
                      <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                    ) : (
                      <TriangleAlert className="h-3.5 w-3.5" aria-hidden="true" />
                    )}
                    {diagnostic.ready ? 'Ready' : 'Needs config'}
                  </span>
                </div>

                {diagnostic.missing_configuration.length > 0 ? (
                  <div className="mt-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Missing
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {diagnostic.missing_configuration.map((field) => (
                        <span
                          key={field}
                          className="rounded-md bg-slate-800 px-2 py-1 font-mono text-xs text-slate-300"
                        >
                          {field}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
              </article>
            ))}
      </div>

      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
    </div>
  );
}
