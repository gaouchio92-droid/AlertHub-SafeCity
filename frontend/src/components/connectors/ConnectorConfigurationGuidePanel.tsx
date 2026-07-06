import { useEffect, useState } from 'react';
import { FileCog } from 'lucide-react';

import {
  ConnectorConfigurationGuideItem,
  getConnectorConfigurationGuide,
} from '../../services/api';

export function ConnectorConfigurationGuidePanel() {
  const [items, setItems] = useState<ConnectorConfigurationGuideItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadGuide() {
      try {
        const response = await getConnectorConfigurationGuide();
        if (isMounted) {
          setItems(response);
          setError(null);
        }
      } catch {
        if (isMounted) {
          setError('Configuration guide unavailable');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadGuide();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Configuration</p>
        <h3 className="mt-2 text-lg font-semibold text-white">How connectors are configured</h3>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
          Connectors are enabled through environment variables in `.env`, then applied by restarting
          Docker Compose.
        </p>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="h-40 animate-pulse rounded-md border border-white/10 bg-slate-900"
              />
            ))
          : items.map((item) => (
              <article
                key={item.source}
                className="rounded-md border border-white/10 bg-slate-950/60 p-4"
              >
                <div className="flex items-center gap-3">
                  <FileCog className="h-5 w-5 text-cyan-300" aria-hidden="true" />
                  <h4 className="text-sm font-semibold text-white">{item.name}</h4>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {item.env_vars.map((envVar) => (
                    <span
                      key={envVar}
                      className="rounded-md bg-slate-800 px-2 py-1 font-mono text-xs text-slate-300"
                    >
                      {envVar}
                    </span>
                  ))}
                </div>
                <p className="mt-4 text-sm leading-6 text-slate-400">{item.note}</p>
              </article>
            ))}
      </div>

      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
    </div>
  );
}
