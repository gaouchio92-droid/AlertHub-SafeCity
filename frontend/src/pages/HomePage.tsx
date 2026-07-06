import { useState } from 'react';
import {
  CheckCircle2,
  ChevronRight,
  Database,
  FileCode2,
  Network,
  Server,
  ShieldCheck,
  TerminalSquare,
} from 'lucide-react';

const cards = [
  {
    title: 'Backend API',
    description: 'FastAPI service with health checks, CORS, logging, settings, and error handling.',
    icon: Server,
  },
  {
    title: 'PostgreSQL',
    description: 'Persistent PostgreSQL 16 service prepared for Alembic-managed schema evolution.',
    icon: Database,
  },
  {
    title: 'Reverse Proxy',
    description: 'Nginx routes frontend traffic and forwards API calls through a hardened edge layer.',
    icon: Network,
  },
  {
    title: 'Security Posture',
    description: 'Environment-driven secrets, security headers, restart policies, and isolated network.',
    icon: ShieldCheck,
  },
];

const readinessItems = [
  {
    key: 'docker',
    title: 'Docker Compose',
    status: 'Configured',
    icon: TerminalSquare,
    description: 'Container orchestration for backend, frontend, PostgreSQL, and Nginx.',
    file: 'docker-compose.yml',
    command: 'docker compose up -d --build',
    details: [
      'Persistent PostgreSQL volume: postgres_data',
      'Private network: alerthub_network',
      'Healthchecks enabled for every service',
      'Restart policy: unless-stopped',
    ],
  },
  {
    key: 'gateway',
    title: 'API Gateway',
    status: 'Configured',
    icon: Network,
    description: 'Nginx reverse proxy for frontend traffic and API routing.',
    file: 'nginx/default.conf',
    command: 'docker compose up -d --force-recreate nginx',
    details: [
      'Frontend served from /',
      'Backend API proxied through /api/',
      'Connector endpoint exposed through /connectors',
      'Security headers and gzip enabled',
    ],
  },
  {
    key: 'database',
    title: 'Database Migrations',
    status: 'Configured',
    icon: Database,
    description: 'Alembic is wired for PostgreSQL schema management.',
    file: 'backend/alembic.ini',
    command: 'docker compose exec backend alembic upgrade head',
    details: [
      'PostgreSQL 16 service is healthy before backend starts',
      'SQLAlchemy connection uses DATABASE_URL',
      'No domain tables are created in Sprint 1',
      'Future migrations live under backend/alembic/versions',
    ],
  },
] as const;

export function HomePage() {
  const [selectedReadinessKey, setSelectedReadinessKey] =
    useState<(typeof readinessItems)[number]['key']>('docker');
  const selectedReadiness =
    readinessItems.find((item) => item.key === selectedReadinessKey) ?? readinessItems[0];

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Sprint 1</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Infrastructure dashboard</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">
          AlertHub Safe City is ready for independent alert ingestion and analytics work in later
          sprints. This screen intentionally contains platform status surfaces only.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <article key={card.title} className="rounded-md border border-white/10 bg-white/[0.04] p-5">
            <card.icon className="h-6 w-6 text-cyan-300" aria-hidden="true" />
            <h3 className="mt-4 text-base font-semibold text-white">{card.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">{card.description}</p>
          </article>
        ))}
      </div>

      <div className="rounded-md border border-white/10 bg-white/[0.04] p-6">
        <h3 className="text-lg font-semibold text-white">Platform readiness</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {readinessItems.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setSelectedReadinessKey(item.key)}
              className={[
                'flex min-h-32 flex-col rounded-md border p-4 text-left transition',
                selectedReadinessKey === item.key
                  ? 'border-cyan-400/50 bg-cyan-400/10'
                  : 'border-white/10 bg-slate-950/60 hover:border-cyan-400/30 hover:bg-white/[0.06]',
              ].join(' ')}
              aria-pressed={selectedReadinessKey === item.key}
            >
              <div className="flex items-center justify-between gap-3">
                <item.icon className="h-5 w-5 text-cyan-300" aria-hidden="true" />
                <ChevronRight className="h-4 w-4 text-slate-500" aria-hidden="true" />
              </div>
              <p className="mt-4 text-sm font-medium text-slate-100">{item.title}</p>
              <p className="mt-2 flex items-center gap-2 text-sm text-emerald-300">
                <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                {item.status}
              </p>
            </button>
          ))}
        </div>

        <div className="mt-5 rounded-md border border-cyan-400/20 bg-slate-950/70 p-5">
          <div className="flex items-start gap-3">
            <selectedReadiness.icon className="mt-1 h-5 w-5 text-cyan-300" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <h4 className="text-base font-semibold text-white">{selectedReadiness.title}</h4>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                {selectedReadiness.description}
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <div className="rounded-md border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                <FileCode2 className="h-4 w-4 text-cyan-300" aria-hidden="true" />
                Configuration file
              </div>
              <code className="mt-3 block overflow-x-auto rounded-md bg-slate-950 px-3 py-2 text-xs text-slate-200">
                {selectedReadiness.file}
              </code>
            </div>

            <div className="rounded-md border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                <TerminalSquare className="h-4 w-4 text-cyan-300" aria-hidden="true" />
                Apply command
              </div>
              <code className="mt-3 block overflow-x-auto rounded-md bg-slate-950 px-3 py-2 text-xs text-slate-200">
                {selectedReadiness.command}
              </code>
            </div>
          </div>

          <div className="mt-5 grid gap-2 sm:grid-cols-2">
            {selectedReadiness.details.map((detail) => (
              <div key={detail} className="flex items-start gap-2 text-sm text-slate-300">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" aria-hidden="true" />
                <span>{detail}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
