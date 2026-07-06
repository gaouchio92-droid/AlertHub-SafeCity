import { Link } from 'react-router-dom';
import {
  AlertCircle,
  KeyRound,
  PlugZap,
  ServerCog,
  SlidersHorizontal,
  Terminal,
} from 'lucide-react';

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
  const envExample = [
    'EVENT_SOURCE=discord',
    'ENABLE_DISCORD=true',
    'DISCORD_TOKEN=your-discord-bot-token',
    'DISCORD_CHANNEL_ID=your-discord-channel-id',
  ];

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

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-md border border-white/10 bg-white/[0.04] p-5">
          <div className="flex items-center gap-3">
            <Terminal className="h-5 w-5 text-cyan-300" aria-hidden="true" />
            <h3 className="text-base font-semibold text-white">Apply environment changes</h3>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            Connector settings are changed in the project `.env` file. After editing it, recreate the
            backend and Nginx services so the new values are loaded.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-md border border-white/10 bg-slate-950 p-4 text-sm text-slate-200">
            <code>{'.\\scripts\\apply-env.ps1'}</code>
          </pre>
        </section>

        <section className="rounded-md border border-amber-300/20 bg-amber-300/[0.06] p-5">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-amber-200" aria-hidden="true" />
            <h3 className="text-base font-semibold text-white">Required for Discord</h3>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            Discord stays disabled at runtime until the token and channel ID are present.
          </p>
          <div className="mt-4 grid gap-2">
            {envExample.map((line) => (
              <code
                key={line}
                className="rounded-md bg-slate-950 px-3 py-2 text-xs text-slate-200"
              >
                {line}
              </code>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}
