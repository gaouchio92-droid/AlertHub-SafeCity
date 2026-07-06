import { useEffect, useState } from 'react';
import { Braces } from 'lucide-react';

import { EventModel, getConnectorEventModel } from '../../services/api';

export function EventModelPanel() {
  const [eventModel, setEventModel] = useState<EventModel | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadEventModel() {
      try {
        const response = await getConnectorEventModel();
        if (isMounted) {
          setEventModel(response);
          setError(null);
        }
      } catch {
        if (isMounted) {
          setError('Event model unavailable');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadEventModel();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Contract</p>
          <h3 className="mt-2 text-lg font-semibold text-white">Common event model</h3>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-white/10 bg-slate-950/70 px-3 py-2 text-sm text-slate-300">
          <Braces className="h-4 w-4 text-cyan-300" aria-hidden="true" />
          {eventModel?.name ?? 'ConnectorEvent'}
        </div>
      </div>

      <div className="mt-5 overflow-hidden rounded-md border border-white/10">
        <div className="grid grid-cols-[minmax(120px,1fr)_minmax(120px,1fr)_90px] bg-slate-950/80 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
          <span>Field</span>
          <span>Type</span>
          <span>Required</span>
        </div>

        {isLoading
          ? Array.from({ length: 5 }).map((_, index) => (
              <div
                key={index}
                className="h-14 animate-pulse border-t border-white/10 bg-slate-900"
              />
            ))
          : eventModel?.fields.map((field) => (
              <div
                key={field.name}
                className="grid grid-cols-[minmax(120px,1fr)_minmax(120px,1fr)_90px] border-t border-white/10 px-4 py-3 text-sm"
              >
                <div>
                  <p className="font-semibold text-white">{field.name}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{field.description}</p>
                </div>
                <span className="font-mono text-cyan-200">{field.data_type}</span>
                <span className={field.required ? 'text-emerald-300' : 'text-slate-400'}>
                  {field.required ? 'Yes' : 'No'}
                </span>
              </div>
            ))}
      </div>

      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
    </div>
  );
}
