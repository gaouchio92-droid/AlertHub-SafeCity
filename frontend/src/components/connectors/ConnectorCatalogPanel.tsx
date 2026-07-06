import { useEffect, useMemo, useState } from 'react';
import { Boxes } from 'lucide-react';

import { ConnectorCatalog, ConnectorCatalogItem, getConnectorCatalog } from '../../services/api';

const categoryStyles: Record<string, string> = {
  default: 'bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20',
  optional: 'bg-cyan-400/10 text-cyan-300 ring-1 ring-cyan-400/20',
  future: 'bg-slate-700/40 text-slate-300 ring-1 ring-white/10',
};

function groupCatalogItems(items: ConnectorCatalogItem[]) {
  return items.reduce<Record<string, ConnectorCatalogItem[]>>((groups, item) => {
    groups[item.category] = [...(groups[item.category] ?? []), item];
    return groups;
  }, {});
}

export function ConnectorCatalogPanel() {
  const [catalog, setCatalog] = useState<ConnectorCatalog | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadCatalog() {
      try {
        const response = await getConnectorCatalog();
        if (isMounted) {
          setCatalog(response);
          setError(null);
        }
      } catch {
        if (isMounted) {
          setError('Connector catalog unavailable');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadCatalog();

    return () => {
      isMounted = false;
    };
  }, []);

  const groupedItems = useMemo(
    () => groupCatalogItems(catalog?.items ?? []),
    [catalog?.items],
  );

  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Catalog</p>
          <h3 className="mt-2 text-lg font-semibold text-white">Available source types</h3>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-white/10 bg-slate-950/70 px-3 py-2 text-sm text-slate-300">
          <Boxes className="h-4 w-4 text-cyan-300" aria-hidden="true" />
          Source: {catalog?.event_source ?? 'loading'}
        </div>
      </div>

      <div className="mt-5 space-y-5">
        {isLoading
          ? Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="h-24 animate-pulse rounded-md border border-white/10 bg-slate-900"
              />
            ))
          : ['default', 'optional', 'future'].map((category) => (
              <div key={category}>
                <h4 className="text-sm font-semibold capitalize text-slate-200">{category}</h4>
                <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {(groupedItems[category] ?? []).map((item) => (
                    <article
                      key={item.source}
                      className="rounded-md border border-white/10 bg-slate-950/60 p-4"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h5 className="text-sm font-semibold text-white">{item.name}</h5>
                          <p className="mt-2 text-sm leading-6 text-slate-400">{item.description}</p>
                        </div>
                        <span
                          className={[
                            'rounded-md px-2.5 py-1 text-xs font-semibold capitalize',
                            categoryStyles[item.category] ?? categoryStyles.future,
                          ].join(' ')}
                        >
                          {item.implemented ? item.category : 'future'}
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            ))}
      </div>

      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
    </div>
  );
}
