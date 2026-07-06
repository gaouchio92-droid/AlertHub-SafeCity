import { useEffect, useState } from 'react';
import { GitBranch, Layers3, LockKeyhole, ToggleLeft } from 'lucide-react';

import { ConnectorRuntime, getConnectorRuntime } from '../../services/api';

const metricItems = [
  {
    label: 'Event source',
    key: 'event_source',
    icon: GitBranch,
  },
  {
    label: 'Mode',
    key: 'mode',
    icon: Layers3,
  },
  {
    label: 'Dynamic imports',
    key: 'dynamic_imports',
    icon: LockKeyhole,
  },
  {
    label: 'Enabled sources',
    key: 'enabled_sources',
    icon: ToggleLeft,
  },
] as const;

function valueForMetric(runtime: ConnectorRuntime | null, key: (typeof metricItems)[number]['key']) {
  if (!runtime) {
    return 'loading';
  }

  if (key === 'event_source') {
    return runtime.event_source;
  }
  if (key === 'mode') {
    return runtime.multiple_mode ? 'multiple' : 'single';
  }
  if (key === 'dynamic_imports') {
    return runtime.dynamic_imports_configured ? 'configured' : 'not configured';
  }
  return runtime.enabled_sources.length > 0 ? runtime.enabled_sources.join(', ') : 'none';
}

export function ConnectorRuntimePanel() {
  const [runtime, setRuntime] = useState<ConnectorRuntime | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadRuntime() {
      try {
        const response = await getConnectorRuntime();
        if (isMounted) {
          setRuntime(response);
          setError(null);
        }
      } catch {
        if (isMounted) {
          setError('Runtime configuration unavailable');
        }
      }
    }

    void loadRuntime();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {metricItems.map((item) => (
        <article key={item.key} className="rounded-md border border-white/10 bg-white/[0.04] p-5">
          <item.icon className="h-6 w-6 text-cyan-300" aria-hidden="true" />
          <h3 className="mt-4 text-sm font-semibold text-white">{item.label}</h3>
          <p className="mt-2 break-words text-sm leading-6 text-slate-300">
            {valueForMetric(runtime, item.key)}
          </p>
        </article>
      ))}
      {error ? <p className="text-sm text-rose-300 md:col-span-2 xl:col-span-4">{error}</p> : null}
    </div>
  );
}
