import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Database,
  ExternalLink,
  FileCode2,
  FileText,
  Network,
  RadioTower,
  Server,
  ShieldCheck,
  TerminalSquare,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import {
  AlertEvent,
  ConnectorDiagnostic,
  EventSummary,
  WeeklyDiscordReport,
  getConnectorDiagnostics,
  getEventSummary,
  getEvents,
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
  const [recentEvents, setRecentEvents] = useState<AlertEvent[]>([]);
  const [openEvents, setOpenEvents] = useState<AlertEvent[]>([]);
  const [diagnostics, setDiagnostics] = useState<ConnectorDiagnostic[]>([]);
  const [isLoadingOperations, setIsLoadingOperations] = useState(true);
  const [operationsError, setOperationsError] = useState<string | null>(null);
  const selectedReadiness =
    readinessItems.find((item) => item.key === selectedReadinessKey) ?? readinessItems[0];
  const discordDiagnostic = useMemo(
    () => diagnostics.find((diagnostic) => diagnostic.source === 'discord') ?? null,
    [diagnostics],
  );
  const zabbixDiagnostic = useMemo(
    () => diagnostics.find((diagnostic) => diagnostic.source === 'zabbix_api') ?? null,
    [diagnostics],
  );
  const topHosts = useMemo(() => {
    const counts = [...openEvents, ...recentEvents].reduce<Record<string, number>>((acc, event) => {
      const host = event.host ?? 'Not detected';
      acc[host] = (acc[host] ?? 0) + 1;
      return acc;
    }, {});

    return Object.entries(counts)
      .map(([label, value]) => ({ label, value }))
      .sort((first, second) => second.value - first.value)
      .slice(0, 6);
  }, [openEvents, recentEvents]);

  useEffect(() => {
    async function loadOperationalSummary() {
      try {
        const [
          reportResponse,
          diagnosticsResponse,
          summaryResponse,
          recentEventsResponse,
          openEventsResponse,
        ] = await Promise.all([
          getWeeklyDiscordReport(),
          getConnectorDiagnostics(),
          getEventSummary(),
          getEvents({ limit: 12, include_unparsed: true }),
          getEvents({ status: 'problem', limit: 12, include_unparsed: true }),
        ]);
        setReport(reportResponse);
        setDiagnostics(diagnosticsResponse);
        setEventSummary(summaryResponse);
        setRecentEvents(recentEventsResponse.items);
        setOpenEvents(openEventsResponse.items);
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
          Live NOC command view for Discord and Zabbix alerts, open incidents, connector health,
          escalation ownership, and platform readiness.
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
              {isLoadingOperations ? 'Loading live data' : 'Current multi-source ingestion view'}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              to="/events?source=zabbix_api&include_unparsed=true"
              className="inline-flex items-center gap-2 rounded-md bg-cyan-400 px-3 py-2 text-sm font-semibold text-slate-950 transition hover:-translate-y-0.5 hover:bg-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-200"
            >
              <Database className="h-4 w-4" aria-hidden="true" />
              Open Zabbix Events
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
            label="All stored events"
            value={eventSummary?.total_events ?? report?.total_events ?? 0}
            tone="cyan"
            to="/events"
          />
          <OperationalMetric
            label="Open problems"
            value={eventSummary?.open_events ?? report?.open_events ?? 0}
            tone={(eventSummary?.open_events ?? report?.open_events) ? 'rose' : 'emerald'}
            to="/events?status=problem"
          />
          <OperationalMetric
            label="Zabbix events"
            value={eventSummary?.by_source.find((item) => item.label === 'zabbix_api')?.value ?? 0}
            tone="amber"
            to="/events?source=zabbix_api&include_unparsed=true"
          />
          <OperationalMetric
            value={eventSummary?.resolved_events ?? report?.resolved_events ?? 0}
            label="Resolved"
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
            Zabbix API: {zabbixDiagnostic?.ready ? 'Connected' : zabbixDiagnostic?.enabled ? 'Needs config' : 'Disabled'}
          </span>
          <span className="rounded-md border border-white/10 bg-slate-950/60 px-3 py-2">
            Sources: {eventSummary?.by_source.map((item) => `${sourceLabel(item.label)} ${item.value}`).join(' / ') || 'No events'}
          </span>
        </div>

        {operationsError ? (
          <p className="mt-4 flex items-center gap-2 text-sm text-amber-200">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" />
            {operationsError}
          </p>
        ) : null}
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <StatusDonutPanel summary={eventSummary} />
        <div className="grid gap-4 lg:grid-cols-2">
          <MetricBarsPanel
            title="Events by source"
            icon={RadioTower}
            items={eventSummary?.by_source ?? []}
            colorClass="bg-cyan-300"
            hrefBuilder={(label) => `/events?source=${encodeURIComponent(label)}&include_unparsed=true`}
            labelBuilder={sourceLabel}
          />
          <MetricBarsPanel
            title="Severity pressure"
            icon={AlertTriangle}
            items={eventSummary?.by_severity ?? []}
            colorClass="bg-amber-300"
            hrefBuilder={(label) => `/events?severity=${encodeURIComponent(label)}`}
            labelBuilder={severityLabel}
          />
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
        <OpenAlertsPanel events={openEvents} />
        <div className="grid gap-4">
          <ConnectorHealthPanel diagnostics={diagnostics} />
          <MetricBarsPanel
            title="Hosts requiring attention"
            icon={Server}
            items={topHosts}
            colorClass="bg-rose-300"
            hrefBuilder={(label) => `/events?q=${encodeURIComponent(label)}&include_unparsed=true`}
            labelBuilder={(label) => label}
          />
        </div>
      </section>

      <RecentEventsTimeline events={recentEvents} />

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

function StatusDonutPanel({ summary }: { summary: EventSummary | null }) {
  const open = summary?.open_events ?? 0;
  const resolved = summary?.resolved_events ?? 0;
  const unparsed = summary?.unparsed_events ?? 0;
  const total = Math.max(summary?.total_events ?? 0, 1);
  const openPercent = Math.round((open / total) * 100);
  const resolvedPercent = Math.round((resolved / total) * 100);

  return (
    <section className="animate-fade-slide-up rounded-md border border-white/10 bg-white/[0.04] p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-cyan-300" aria-hidden="true" />
            <h3 className="text-lg font-semibold text-white">Incident status</h3>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Open, resolved, and parsing state from all enabled sources.
          </p>
        </div>
        <Link
          to="/events"
          className="rounded-md border border-cyan-300/30 px-3 py-2 text-sm font-semibold text-cyan-100 transition hover:-translate-y-0.5 hover:bg-cyan-300/10"
        >
          Explore
        </Link>
      </div>

      <div className="mt-6 grid gap-6 sm:grid-cols-[190px_1fr] sm:items-center">
        <div className="relative mx-auto h-44 w-44">
          <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120" role="img" aria-label="Incident status chart">
            <circle cx="60" cy="60" r="48" fill="none" stroke="rgba(15,23,42,0.9)" strokeWidth="14" />
            <circle
              cx="60"
              cy="60"
              r="48"
              fill="none"
              stroke="rgb(244,63,94)"
              strokeDasharray={`${openPercent * 3.01} 301`}
              strokeLinecap="round"
              strokeWidth="14"
            />
            <circle
              cx="60"
              cy="60"
              r="32"
              fill="none"
              stroke="rgb(52,211,153)"
              strokeDasharray={`${resolvedPercent * 2.01} 201`}
              strokeLinecap="round"
              strokeWidth="10"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-3xl font-semibold text-white">{summary?.total_events ?? 0}</span>
            <span className="text-xs uppercase tracking-wide text-slate-400">events</span>
          </div>
        </div>

        <div className="grid gap-3">
          <StatusPill label="Open problems" value={open} tone="rose" to="/events?status=problem" />
          <StatusPill label="Resolved" value={resolved} tone="emerald" to="/events?status=resolved" />
          <StatusPill label="Unparsed" value={unparsed} tone="amber" to="/events?include_unparsed=true" />
          <StatusPill label="Last event" value={formatEventDate(summary?.last_event_at)} tone="cyan" to="/events" />
        </div>
      </div>
    </section>
  );
}

function MetricBarsPanel({
  title,
  icon: Icon,
  items,
  colorClass,
  hrefBuilder,
  labelBuilder,
}: {
  title: string;
  icon: typeof BarChart3;
  items: { label: string; value: number }[];
  colorClass: string;
  hrefBuilder: (label: string) => string;
  labelBuilder: (label: string) => string;
}) {
  const maxValue = Math.max(...items.map((item) => item.value), 1);

  return (
    <section className="animate-fade-slide-up rounded-md border border-white/10 bg-white/[0.04] p-5">
      <div className="flex items-center gap-2">
        <Icon className="h-5 w-5 text-cyan-300" aria-hidden="true" />
        <h3 className="text-base font-semibold text-white">{title}</h3>
      </div>
      <div className="mt-5 space-y-3">
        {items.slice(0, 6).map((item) => {
          const width = Math.max((item.value / maxValue) * 100, 5);
          return (
            <Link
              key={item.label}
              to={hrefBuilder(item.label)}
              className="group block rounded-md border border-white/10 bg-slate-950/60 p-3 transition hover:-translate-y-0.5 hover:border-cyan-300/35 hover:bg-white/[0.05]"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="truncate text-sm font-semibold text-slate-100">
                  {labelBuilder(item.label)}
                </span>
                <span className="text-sm text-slate-300">{item.value}</span>
              </div>
              <div className="mt-3 h-2 rounded-full bg-slate-800">
                <div
                  className={[
                    'h-2 rounded-full transition-all duration-500 group-hover:brightness-125',
                    colorClass,
                  ].join(' ')}
                  style={{ width: `${width}%` }}
                />
              </div>
            </Link>
          );
        })}
        {items.length === 0 ? (
          <p className="rounded-md border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-400">
            No data collected yet.
          </p>
        ) : null}
      </div>
    </section>
  );
}

function OpenAlertsPanel({ events }: { events: AlertEvent[] }) {
  return (
    <section className="animate-fade-slide-up rounded-md border border-rose-300/20 bg-rose-300/[0.04] p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-rose-200" aria-hidden="true" />
            <h3 className="text-lg font-semibold text-white">Priority open alerts</h3>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Active problems requiring NOC triage, owner follow-up, and source verification.
          </p>
        </div>
        <Link
          to="/events?status=problem"
          className="inline-flex w-fit items-center gap-2 rounded-md bg-rose-300 px-3 py-2 text-sm font-semibold text-slate-950 transition hover:-translate-y-0.5 hover:bg-rose-200"
        >
          View all open
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="py-3 pr-4">Source</th>
              <th className="py-3 pr-4">Problem</th>
              <th className="py-3 pr-4">Host</th>
              <th className="py-3 pr-4">Severity</th>
              <th className="py-3 pr-4">Owner</th>
              <th className="py-3 pr-4">Started</th>
              <th className="py-3 pr-4">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {events.map((event) => (
              <tr key={event.id} className="align-top text-slate-300">
                <td className="py-3 pr-4 font-semibold text-cyan-200">{sourceLabel(event.source)}</td>
                <td className="py-3 pr-4">
                  <p className="max-w-md font-medium text-white">
                    {event.problem_name ?? event.problem_id ?? 'Unparsed alert'}
                  </p>
                  {event.operational_data ? (
                    <p className="mt-1 max-w-md text-xs leading-5 text-slate-400">
                      {event.operational_data}
                    </p>
                  ) : null}
                </td>
                <td className="py-3 pr-4">{event.host ?? 'Not detected'}</td>
                <td className="py-3 pr-4">
                  <SeverityBadge severity={event.severity} />
                </td>
                <td className="py-3 pr-4">
                  <p>{event.escalation_owner ?? 'NOC Team'}</p>
                  <p className="mt-1 text-xs text-slate-500">{event.escalation_level ?? 'Standard follow-up'}</p>
                </td>
                <td className="py-3 pr-4">{formatEventDate(event.started_at ?? event.created_at)}</td>
                <td className="py-3 pr-4">
                  <div className="flex flex-wrap gap-2">
                    <Link
                      to={eventHref(event)}
                      className="rounded-md border border-cyan-300/30 px-2 py-1 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/10"
                    >
                      Details
                    </Link>
                    {event.links.slice(0, 1).map((link) => (
                      <a
                        key={link}
                        href={link}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1 text-xs text-slate-100 transition hover:bg-white/5"
                      >
                        Source
                        <ExternalLink className="h-3 w-3" aria-hidden="true" />
                      </a>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {events.length === 0 ? (
          <div className="rounded-md border border-emerald-300/20 bg-emerald-300/[0.06] p-5 text-sm text-emerald-100">
            No open problem detected from Discord or Zabbix.
          </div>
        ) : null}
      </div>
    </section>
  );
}

function ConnectorHealthPanel({ diagnostics }: { diagnostics: ConnectorDiagnostic[] }) {
  return (
    <section className="animate-fade-slide-up rounded-md border border-white/10 bg-white/[0.04] p-5">
      <div className="flex items-center gap-2">
        <RadioTower className="h-5 w-5 text-emerald-300" aria-hidden="true" />
        <h3 className="text-base font-semibold text-white">Connector health</h3>
      </div>
      <div className="mt-5 grid gap-3">
        {diagnostics
          .filter((diagnostic) => ['discord', 'zabbix_api', 'zabbix_database'].includes(diagnostic.source))
          .map((diagnostic) => {
            const ready = diagnostic.enabled && diagnostic.ready;
            return (
              <Link
                key={diagnostic.source}
                to={`/events?source=${diagnostic.source}&include_unparsed=true`}
                className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-slate-950/60 p-3 transition hover:-translate-y-0.5 hover:border-cyan-300/35"
              >
                <div>
                  <p className="text-sm font-semibold text-white">{sourceLabel(diagnostic.source)}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    {ready
                      ? 'Connected and collecting'
                      : diagnostic.enabled
                        ? `Needs config: ${diagnostic.missing_configuration.join(', ') || 'connection failed'}`
                        : 'Disabled by environment'}
                  </p>
                </div>
                <span
                  className={[
                    'rounded-md px-2 py-1 text-xs font-semibold',
                    ready
                      ? 'bg-emerald-300/10 text-emerald-200 ring-1 ring-emerald-300/25'
                      : diagnostic.enabled
                        ? 'bg-amber-300/10 text-amber-200 ring-1 ring-amber-300/25'
                        : 'bg-slate-700/50 text-slate-300 ring-1 ring-white/10',
                  ].join(' ')}
                >
                  {ready ? 'Online' : diagnostic.enabled ? 'Check' : 'Off'}
                </span>
              </Link>
            );
          })}
      </div>
    </section>
  );
}

function RecentEventsTimeline({ events }: { events: AlertEvent[] }) {
  return (
    <section className="animate-fade-slide-up rounded-md border border-white/10 bg-white/[0.04] p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Clock3 className="h-5 w-5 text-cyan-300" aria-hidden="true" />
            <h3 className="text-lg font-semibold text-white">Latest alert stream</h3>
          </div>
          <p className="mt-2 text-sm text-slate-400">
            Last normalized events received from Discord and Zabbix.
          </p>
        </div>
        <Link
          to="/events?include_unparsed=true"
          className="inline-flex w-fit items-center gap-2 rounded-md border border-cyan-300/30 px-3 py-2 text-sm font-semibold text-cyan-100 transition hover:-translate-y-0.5 hover:bg-cyan-300/10"
        >
          Full stream
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {events.slice(0, 8).map((event) => (
          <Link
            key={event.id}
            to={eventHref(event)}
            className="group rounded-md border border-white/10 bg-slate-950/60 p-4 transition hover:-translate-y-0.5 hover:border-cyan-300/35 hover:bg-white/[0.05]"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-white">
                  {event.problem_name ?? event.problem_id ?? 'Unparsed alert'}
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  {sourceLabel(event.source)} / {event.host ?? 'Host not detected'} /{' '}
                  {formatEventDate(event.started_at ?? event.created_at)}
                </p>
              </div>
              <SeverityBadge severity={event.severity} />
            </div>
            <div className="mt-3 flex items-center justify-between gap-3">
              <span className="rounded-md bg-slate-900 px-2 py-1 text-xs text-slate-300">
                {event.status ?? 'unknown'}
              </span>
              <ChevronRight className="h-4 w-4 text-slate-500 transition group-hover:translate-x-1 group-hover:text-cyan-200" />
            </div>
          </Link>
        ))}
        {events.length === 0 ? (
          <p className="rounded-md border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-400">
            No alert has been collected yet.
          </p>
        ) : null}
      </div>
    </section>
  );
}

function StatusPill({
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
        'flex items-center justify-between gap-3 rounded-md border px-3 py-2 transition hover:-translate-y-0.5',
        toneClasses[tone],
      ].join(' ')}
    >
      <span className="text-sm text-slate-300">{label}</span>
      <span className="font-semibold text-white">{value}</span>
    </Link>
  );
}

function SeverityBadge({ severity }: { severity: string | null }) {
  const normalized = (severity ?? 'unknown').toLowerCase();
  const classes: Record<string, string> = {
    disaster: 'bg-rose-500/20 text-rose-100 ring-1 ring-rose-300/30',
    high: 'bg-orange-400/20 text-orange-100 ring-1 ring-orange-300/30',
    average: 'bg-amber-300/20 text-amber-100 ring-1 ring-amber-300/30',
    warning: 'bg-yellow-300/15 text-yellow-100 ring-1 ring-yellow-300/25',
    information: 'bg-cyan-300/15 text-cyan-100 ring-1 ring-cyan-300/25',
    unknown: 'bg-slate-700/50 text-slate-200 ring-1 ring-white/10',
  };

  return (
    <span className={['rounded-md px-2 py-1 text-xs font-semibold', classes[normalized] ?? classes.unknown].join(' ')}>
      {severityLabel(severity ?? 'unknown')}
    </span>
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

function sourceLabel(source: string) {
  const labels: Record<string, string> = {
    discord: 'Discord',
    zabbix_api: 'Zabbix API',
    zabbix_database: 'Zabbix DB',
  };
  return labels[source] ?? source;
}

function severityLabel(severity: string) {
  const labels: Record<string, string> = {
    disaster: 'Disaster',
    high: 'High',
    average: 'Average',
    warning: 'Warning',
    information: 'Information',
    unknown: 'Unknown',
  };
  return labels[severity.toLowerCase()] ?? severity;
}

function eventHref(event: AlertEvent) {
  const params = new URLSearchParams();
  params.set('include_unparsed', 'true');
  params.set('source', event.source);
  if (event.problem_id) {
    params.set('q', event.problem_id);
  } else if (event.host) {
    params.set('q', event.host);
  }
  return `/events?${params.toString()}`;
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
