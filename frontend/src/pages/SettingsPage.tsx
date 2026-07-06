import { Link } from 'react-router-dom';
import { KeyRound, PlugZap, ServerCog, SlidersHorizontal } from 'lucide-react';

const settings = [
  {
    name: 'Environment',
    value: 'Managed through .env',
    icon: SlidersHorizontal,
  },
  {
    name: 'Secrets',
    value: 'Injected at runtime',
    icon: KeyRound,
  },
  {
    name: 'Services',
    value: 'Docker Compose orchestration',
    icon: ServerCog,
  },
];

export function SettingsPage() {
  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Configuration</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Settings</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">
          Runtime configuration is centralized through environment variables and container service
          definitions.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {settings.map((item) => (
          <article key={item.name} className="rounded-md border border-white/10 bg-white/[0.04] p-5">
            <item.icon className="h-6 w-6 text-cyan-300" aria-hidden="true" />
            <h3 className="mt-4 text-base font-semibold text-white">{item.name}</h3>
            <p className="mt-2 text-sm text-slate-300">{item.value}</p>
          </article>
        ))}
      </div>

      <Link
        to="/event-sources"
        className="flex items-center justify-between gap-4 rounded-md border border-white/10 bg-white/[0.04] p-5 transition hover:border-cyan-400/30 hover:bg-cyan-400/5"
      >
        <div className="flex items-center gap-3">
          <PlugZap className="h-5 w-5 text-cyan-300" aria-hidden="true" />
          <div>
            <h3 className="text-base font-semibold text-white">Connector engine</h3>
            <p className="mt-1 text-sm text-slate-300">
              View enabled sources, connection state, and runtime source selection.
            </p>
          </div>
        </div>
        <span className="text-sm font-semibold text-cyan-300">Open</span>
      </Link>
    </section>
  );
}
