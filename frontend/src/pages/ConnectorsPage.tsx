import { DatabaseZap, Globe2, RadioTower, ShieldCheck } from 'lucide-react';

import { ConnectorCatalogPanel } from '../components/connectors/ConnectorCatalogPanel';
import { ConnectorConfigurationGuidePanel } from '../components/connectors/ConnectorConfigurationGuidePanel';
import { ConnectorDiagnosticsPanel } from '../components/connectors/ConnectorDiagnosticsPanel';
import { ConnectorRuntimePanel } from '../components/connectors/ConnectorRuntimePanel';
import { ConnectorStatusGrid } from '../components/connectors/ConnectorStatusGrid';
import { EventModelPanel } from '../components/connectors/EventModelPanel';

const connectorCapabilities = [
  {
    name: 'Default source',
    value: 'Discord',
    icon: ShieldCheck,
  },
  {
    name: 'Optional sources',
    value: 'Zabbix API and Database',
    icon: DatabaseZap,
  },
  {
    name: 'Future channels',
    value: 'REST, Syslog, Wazuh, Grafana, Cacti',
    icon: RadioTower,
  },
  {
    name: 'Runtime selection',
    value: 'Environment based',
    icon: Globe2,
  },
];

export function ConnectorsPage() {
  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Sources</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Connectors</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">
          Event sources are isolated behind a shared connector interface and normalized into one
          common event model for downstream analytics.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {connectorCapabilities.map((item) => (
          <article key={item.name} className="rounded-md border border-white/10 bg-white/[0.04] p-5">
            <item.icon className="h-6 w-6 text-cyan-300" aria-hidden="true" />
            <h3 className="mt-4 text-sm font-semibold text-white">{item.name}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">{item.value}</p>
          </article>
        ))}
      </div>

      <ConnectorRuntimePanel />
      <ConnectorStatusGrid />
      <ConnectorDiagnosticsPanel />
      <ConnectorConfigurationGuidePanel />
      <EventModelPanel />
      <ConnectorCatalogPanel />
    </section>
  );
}
