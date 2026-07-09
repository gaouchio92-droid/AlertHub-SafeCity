import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Database,
  FileCode2,
  FileText,
  Network,
  Server,
  ShieldCheck,
  TerminalSquare,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import {
  ConnectorDiagnostic,
  EventSummary,
  WeeklyDiscordReport,
  getConnectorDiagnostics,
  getEventSummary,
  getWeeklyDiscordReport,
} from '../services/api';

const cards = [
  {
    title: 'Backend API',
    description: 'FastAPI service with health checks, CORS, logging, settings, and error handling.',
    icon: Server,
    to: '/settings',
    action: 'Open API settings',
    insight: 'Health, Swagger, CORS',
  },
  {
    title: 'PostgreSQL',
    description: 'Persistent PostgreSQL 16 service prepared for Alembic-managed schema evolution.',
    icon: Database,
    to: '/events',
    action: 'Browse stored events',
    insight: 'Events and migrations',
  },
  {
    title: 'Reverse Proxy',
    description: 'Nginx routes frontend traffic and forwards API calls through a hardened edge layer.',
    icon: Network,
    to: '/settings',
    action: 'Review gateway',
    insight: 'Nginx and /api routing',
  },
  {
    title: 'Security Posture',
    description: 'Environment-driven secrets, security headers, restart policies, and isolated network.',
    icon: ShieldCheck,
    to: '/settings',
    action: 'Open security controls',
    insight: 'RBAC and secrets',
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
    to: '/settings',
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
    to: '/settings',
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
    to: '/events',
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
  const [report, setReport] = useState<WeeklyDiscordReport | null>(null);
  const [eventSummary, setEventSummary] = useState<EventSummary | null>(null);
  const [diagnostics, setDiagnostics] = useState<ConnectorDiagnostic[]>([]);
  const [isLoadingOperations, setIsLoadingOperations] = useState(true);
  const [operationsError, setOperationsError] = useState<string | null>(null);
  const selectedReadiness =
    readinessItems.find((item) => item.key === selectedReadinessKey) ?? readinessItems[0];
  const discordDiagnostic = useMemo(
    () => diagnostics.find((diagnostic) => diagnostic.source === 'discord') ?? null,
    [diagnostics],
  );

  useEffect(() => {
    async function loadOperationalSummary() {
      try {
        const [reportResponse, diagnosticsResponse, summaryResponse] = await Promise.all([
          getWeeklyDiscordReport(),
          getConnectorDiagnostics(),
          getEventSummary(),
        ]);
        setReport(reportResponse);
        setDiagnostics(diagnosticsResponse);
        setEventSummary(summaryResponse);
        setOperationsError(null);
      } catch {
        setOperationsError('Operational summary unavailable');
      } finally {
        setIsLoadingOperations(false);
      }
    }

    void loadOperationalSummary();
  }, []);

  return (
    <section className="space-y-6">
      <div className="animate-fade-slide-up">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Operations</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Safe City dashboard</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">
          Live monitoring summary from the configured Discord alert channel, with infrastructure
          readiness kept visible for operations.
        </p>
      </div>

      <section className="animate-fade-slide-up rounded-md border border-white/10 bg-white/[0.04] p-6 [animation-delay:80ms]">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-emerald-300" aria-hidden="true" />
              <h3 className="text-lg font-semibold text-white">Operational snapshot</h3>
            </div>
            <p className="mt-2 text-sm text-slate-400">
              {isLoadingOperations ? 'Loading live data' : 'Current seven-day Discord ingestion view'}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              to="/events"
              className="inline-flex items-center gap-2 rounded-md bg-cyan-400 px-3 py-2 text-sm font-semibold text-slate-950 transition hover:-translate-y-0.5 hover:bg-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-200"
            >
              <Database className="h-4 w-4" aria-hidden="true" />
              Open Events
            </Link>
            <Link
              to="/reports"
              className="inline-flex items-center gap-2 rounded-md border border-white/10 px-3 py-2 text-sm font-medium text-slate-200 transition hover:-translate-y-0.5 hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-cyan-300/50"
            >
              <FileText className="h-4 w-4" aria-hidden="true" />
              Weekly Report
            </Link>
          </div>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <OperationalMetric
            label="Stored events"
            value={eventSummary?.total_events ?? report?.total_events ?? 0}
            tone="cyan"
            to="/events"
          />
          <OperationalMetric
            label="Open problems"
            value={eventSummary?.open_events ?? report?.open_events ?? 0}
            tone={(eventSummary?.open_events ?? report?.open_events) ? 'rose' : 'emerald'}
            to="/reports"
          />
          <OperationalMetric
            label="Resolved"
            value={eventSummary?.resolved_events ?? report?.resolved_events ?? 0}
            tone="emerald"
            to="/reports"
          />
          <OperationalMetric
            label="Last event"
            value={formatEventDate(eventSummary?.last_event_at)}
            tone={eventSummary?.last_event_at ? 'cyan' : 'amber'}
            to="/events"
          />
        </div>

        <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-300">
          <span className="rounded-md border border-white/10 bg-slate-950/60 px-3 py-2">
            Unparsed events: {eventSummary?.unparsed_events ?? 0}
          </span>
          <span className="rounded-md border border-white/10 bg-slate-950/60 px-3 py-2">
            Discord connector: {discordDiagnostic?.ready ? 'Ready' : 'Needs config'}
          </span>
          <span className="rounded-md border border-white/10 bg-slate-950/60 px-3 py-2">
            Weekly window: {report?.total_events ?? 0} alerts
          </span>
        </div>

        {operationsError ? (
          <p className="mt-4 flex items-center gap-2 text-sm text-amber-200">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" />
            {operationsError}
          </p>
        ) : null}
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <Link
            key={card.title}
            to={card.to}
            className="group animate-fade-slide-up rounded-md border border-white/10 bg-white/[0.04] p-5 transition hover:-translate-y-1 hover:border-cyan-300/40 hover:bg-cyan-300/[0.06] hover:shadow-xl hover:shadow-cyan-950/20 focus:outline-none focus:ring-2 focus:ring-cyan-300/50"
          >
            <div className="flex items-start justify-between gap-4">
              <card.icon className="h-6 w-6 text-cyan-300 transition group-hover:scale-110" aria-hidden="true" />
              <ChevronRight className="h-4 w-4 text-slate-500 transition group-hover:translate-x-1 group-hover:text-cyan-200" aria-hidden="true" />
            </div>
            <h3 className="mt-4 text-base font-semibold text-white">{card.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">{card.description}</p>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="rounded-md bg-slate-900 px-2 py-1 text-xs font-medium text-cyan-100 ring-1 ring-cyan-300/20">
                {card.insight}
              </span>
              <span className="text-xs font-semibold text-cyan-300 opacity-80 transition group-hover:opacity-100">
                {card.action}
              </span>
            </div>
          </Link>
        ))}
      </div>

      <div className="animate-fade-slide-up rounded-md border border-white/10 bg-white/[0.04] p-6 [animation-delay:140ms]">
        <h3 className="text-lg font-semibold text-white">Platform readiness</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {readinessItems.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setSelectedReadinessKey(item.key)}
              className={[
                'group flex min-h-32 flex-col rounded-md border p-4 text-left transition hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-cyan-300/50',
                selectedReadinessKey === item.key
                  ? 'border-cyan-400/50 bg-cyan-400/10'
                  : 'border-white/10 bg-slate-950/60 hover:border-cyan-400/30 hover:bg-white/[0.06]',
              ].join(' ')}
              aria-pressed={selectedReadinessKey === item.key}
            >
              <div className="flex items-center justify-between gap-3">
                <item.icon className="h-5 w-5 text-cyan-300 transition group-hover:scale-110" aria-hidden="true" />
                <ChevronRight className="h-4 w-4 text-slate-500 transition group-hover:translate-x-1 group-hover:text-cyan-200" aria-hidden="true" />
              </div>
              <p className="mt-4 text-sm font-medium text-slate-100">{item.title}</p>
              <p className="mt-2 flex items-center gap-2 text-sm text-emerald-300">
                <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                {item.status}
              </p>
            </button>
          ))}
        </div>

        <div key={selectedReadiness.key} className="mt-5 animate-fade-slide-up rounded-md border border-cyan-400/20 bg-slate-950/70 p-5">
          <div className="flex items-start gap-3">
            <selectedReadiness.icon className="mt-1 h-5 w-5 text-cyan-300" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <h4 className="text-base font-semibold text-white">{selectedReadiness.title}</h4>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                {selectedReadiness.description}
              </p>
            </div>
            <Link
              to={selectedReadiness.to}
              className="hidden shrink-0 items-center gap-2 rounded-md border border-cyan-300/30 px-3 py-2 text-sm font-semibold text-cyan-100 transition hover:-translate-y-0.5 hover:bg-cyan-300/10 focus:outline-none focus:ring-2 focus:ring-cyan-300/50 sm:inline-flex"
            >
              Open content
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </Link>
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
          <Link
            to={selectedReadiness.to}
            className="mt-5 inline-flex items-center gap-2 rounded-md bg-cyan-400 px-3 py-2 text-sm font-semibold text-slate-950 transition hover:-translate-y-0.5 hover:bg-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-200 sm:hidden"
          >
            Open content
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </section>
  );
}

function formatEventDate(value: string | null | undefined) {
  if (!value) {
    return 'No data';
  }

  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function OperationalMetric({
  label,
  value,
  tone,
  to,
}: {
  label: string;
  value: number | string;
  tone: 'amber' | 'cyan' | 'emerald' | 'rose';
  to: string;
}) {
  const toneClasses = {
    amber: 'border-amber-300/20 bg-amber-300/[0.06] text-amber-100',
    cyan: 'border-cyan-300/20 bg-cyan-300/[0.06] text-cyan-100',
    emerald: 'border-emerald-300/20 bg-emerald-300/[0.06] text-emerald-100',
    rose: 'border-rose-300/20 bg-rose-300/[0.06] text-rose-100',
  };

  return (
    <Link
      to={to}
      className={[
        'group block rounded-md border p-4 transition hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-cyan-300/50',
        toneClasses[tone],
      ].join(' ')}
    >
      <p className="text-sm text-slate-300">{label}</p>
      <div className="mt-2 flex items-end justify-between gap-3">
        <p className="text-3xl font-semibold text-white">{value}</p>
        <ChevronRight className="mb-1 h-4 w-4 text-slate-400 transition group-hover:translate-x-1 group-hover:text-white" aria-hidden="true" />
      </div>
      <div className="mt-3 h-1 overflow-hidden rounded-full bg-slate-950/50">
        <div className="animate-soft-pulse h-full rounded-full bg-current" />
      </div>
    </Link>
  );
}
