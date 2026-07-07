import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Database,
  FileDown,
  RefreshCw,
  Server,
} from 'lucide-react';

import {
  EventSyncResult,
  WeeklyDiscordReport,
  WeeklyDiscordReportDailyTrend,
  WeeklyDiscordReportMetric,
  WeeklyDiscordReportStatus,
  getWeeklyDiscordReport,
  getWeeklyDiscordReportStatus,
  syncEvents,
} from '../services/api';

function formatDateTime(value: string | null) {
  if (!value) {
    return 'No timestamp';
  }
  return new Date(value).toLocaleString();
}

function formatPeriod(report: WeeklyDiscordReport | null) {
  if (!report) {
    return 'Loading period';
  }
  return `${formatDateTime(report.period_start)} to ${formatDateTime(report.period_end)}`;
}

export function ReportsPage() {
  const [status, setStatus] = useState<WeeklyDiscordReportStatus | null>(null);
  const [report, setReport] = useState<WeeklyDiscordReport | null>(null);
  const [syncResult, setSyncResult] = useState<EventSyncResult | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const readableEvents = useMemo(() => {
    if (!report || report.total_events === 0) {
      return 0;
    }
    return report.total_events - report.data_quality.unnamed_events;
  }, [report]);

  async function loadReport() {
    try {
      const [statusResponse, reportResponse] = await Promise.all([
        getWeeklyDiscordReportStatus(),
        getWeeklyDiscordReport(),
      ]);
      setStatus(statusResponse);
      setReport(reportResponse);
      setError(null);
    } catch {
      setError('Weekly report unavailable');
    }
  }

  useEffect(() => {
    void loadReport();
  }, []);

  async function handleSync() {
    setIsSyncing(true);
    try {
      const response = await syncEvents();
      setSyncResult(response);
      await loadReport();
    } catch {
      setError('Discord synchronization failed');
    } finally {
      setIsSyncing(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Reports</p>
          <h2 className="mt-2 text-3xl font-semibold text-white">Discord weekly operations</h2>
          <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">
            A seven-day operational view of Discord events collected from the configured alert
            channel and stored in PostgreSQL.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <a
            href="/api/v1/reports/weekly-discord/export"
            download="alerthub-weekly-discord-report.md"
            className="inline-flex items-center justify-center gap-2 rounded-md border border-white/10 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/5"
          >
            <FileDown className="h-4 w-4" aria-hidden="true" />
            Export report
          </a>
          <button
            type="button"
            onClick={handleSync}
            disabled={isSyncing}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw className={['h-4 w-4', isSyncing ? 'animate-spin' : ''].join(' ')} />
            Sync Discord
          </button>
        </div>
      </div>

      <section className="rounded-md border border-white/10 bg-white/[0.04] p-6">
        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <div>
            <div className="flex items-center gap-3">
              <CalendarClock className="h-6 w-6 text-cyan-300" aria-hidden="true" />
              <h3 className="text-lg font-semibold text-white">
                {status?.feature ?? 'Weekly Discord report'}
              </h3>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {status?.reason ?? 'Loading report status.'}
            </p>
            <p className="mt-3 text-sm text-slate-400">{formatPeriod(report)}</p>
          </div>

          <div className="rounded-md border border-emerald-400/20 bg-emerald-400/[0.06] p-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-300" aria-hidden="true" />
              <p className="text-sm font-semibold text-emerald-200">Pipeline active</p>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Discord is configured, sync is available, and events are persisted locally before
              reporting.
            </p>
            {syncResult ? (
              <p className="mt-3 text-sm text-emerald-200">
                Last sync: {syncResult.received} read, {syncResult.created} new,{' '}
                {syncResult.updated} refreshed.
              </p>
            ) : null}
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Discord messages" value={report?.total_events ?? 0} />
          <MetricCard label="Readable alerts" value={readableEvents} />
          <MetricCard label="Still open" value={report?.open_events ?? 0} />
          <MetricCard label="Resolved" value={report?.resolved_events ?? 0} />
        </div>
      </section>

      <DailyTrendPanel items={report?.daily_trend ?? []} />

      <StabilizationRecommendationsPanel report={report} />

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <DataQualityPanel report={report} />
        <div className="grid gap-4 md:grid-cols-2">
          <MetricList title="Detected hosts" items={report?.by_host ?? []} />
          <MetricList title="Detected severities" items={report?.by_severity ?? []} />
        </div>
      </section>

      <section className="rounded-md border border-white/10 bg-white/[0.04] p-6">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-cyan-300" aria-hidden="true" />
          <h3 className="text-lg font-semibold text-white">Recent stored events</h3>
        </div>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="py-3 pr-4">Event</th>
                <th className="py-3 pr-4">Host</th>
                <th className="py-3 pr-4">Severity</th>
                <th className="py-3 pr-4">Status</th>
                <th className="py-3 pr-4">Links</th>
                <th className="py-3 pr-4">Received</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {(report?.recent_events ?? []).map((event) => (
                <tr key={event.problem_id ?? event.started_at} className="text-slate-300">
                  <td className="py-3 pr-4">
                    <p className="font-medium text-white">{event.title}</p>
                    {!event.details_available ? (
                      <p className="mt-1 text-xs text-amber-300">
                        Raw Discord message stored, readable alert fields not detected yet.
                      </p>
                    ) : null}
                    {event.operational_data ? (
                      <p className="mt-1 text-xs text-slate-400">{event.operational_data}</p>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4">{event.host ?? 'Not detected'}</td>
                  <td className="py-3 pr-4">{event.severity ?? 'Not detected'}</td>
                  <td className="py-3 pr-4">{event.status ?? 'unknown'}</td>
                  <td className="py-3 pr-4">
                    {event.links.length > 0 ? (
                      <a
                        href={event.links[0]}
                        target="_blank"
                        rel="noreferrer"
                        className="text-cyan-300 underline-offset-4 hover:underline"
                      >
                        Open
                      </a>
                    ) : (
                      'No link'
                    )}
                  </td>
                  <td className="py-3 pr-4">{formatDateTime(event.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {report?.recent_events.length === 0 ? (
            <p className="rounded-md border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-400">
              No Discord events stored for this period.
            </p>
          ) : null}
        </div>
      </section>

      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}

function StabilizationRecommendationsPanel({ report }: { report: WeeklyDiscordReport | null }) {
  const recommendations = [
    'Planifier une synchronisation automatique Discord pour eviter les imports manuels.',
    'Surveiller /api/v1/health et les healthchecks Docker avec une alerte externe.',
    'Sauvegarder le volume PostgreSQL avant chaque mise a jour importante.',
    'Activer une rotation des logs backend, nginx et Docker pour proteger le disque.',
    'Executer Alembic dans le pipeline de deploiement avant redemarrage applicatif.',
  ];

  if ((report?.data_quality.unnamed_events ?? 0) > 0) {
    recommendations.push(
      'Finaliser le parsing Discord pour reduire les messages non lisibles dans les rapports.',
    );
  }

  if ((report?.open_events ?? 0) > 0) {
    recommendations.push(
      'Mettre en place un suivi quotidien des problemes ouverts avec responsable assigne.',
    );
  }

  return (
    <section className="rounded-md border border-cyan-300/20 bg-cyan-300/[0.05] p-6">
      <div className="flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-cyan-200" aria-hidden="true" />
        <h3 className="text-lg font-semibold text-white">Recommandations de stabilisation</h3>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {recommendations.map((recommendation) => (
          <div
            key={recommendation}
            className="rounded-md border border-white/10 bg-slate-950/60 p-4 text-sm leading-6 text-slate-300"
          >
            {recommendation}
          </div>
        ))}
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-white/10 bg-slate-950/60 p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}

function DataQualityPanel({ report }: { report: WeeklyDiscordReport | null }) {
  const warnings = report?.data_quality.warnings ?? [];
  return (
    <div className="rounded-md border border-amber-300/20 bg-amber-300/[0.06] p-5">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-5 w-5 text-amber-200" aria-hidden="true" />
        <h3 className="text-base font-semibold text-white">Data readability</h3>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-300">
        The report can count every stored Discord message. Alert names, severities, and resolved
        states become recognizable once the exact Zabbix message format is present in the payload.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <MetricCard label="No alert title" value={report?.data_quality.unnamed_events ?? 0} />
        <MetricCard
          label="No severity"
          value={report?.data_quality.unknown_severity_events ?? 0}
        />
        <MetricCard label="No host" value={report?.data_quality.unknown_host_events ?? 0} />
      </div>
      <div className="mt-4 space-y-2">
        {warnings.map((warning) => (
          <p key={warning} className="text-sm text-amber-100">
            {warning}
          </p>
        ))}
      </div>
    </div>
  );
}

function DailyTrendPanel({ items }: { items: WeeklyDiscordReportDailyTrend[] }) {
  const maxValue = Math.max(...items.map((item) => item.total), 1);

  return (
    <section className="rounded-md border border-white/10 bg-white/[0.04] p-6">
      <div className="flex items-center gap-2">
        <CalendarClock className="h-5 w-5 text-cyan-300" aria-hidden="true" />
        <h3 className="text-lg font-semibold text-white">Daily alert trend</h3>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
        {items.map((item) => {
          const barHeight = Math.max((item.total / maxValue) * 100, item.total > 0 ? 12 : 4);
          return (
            <div key={item.date} className="rounded-md border border-white/10 bg-slate-950/60 p-3">
              <div className="flex h-28 items-end gap-1">
                <div
                  className="w-1/2 rounded-t bg-rose-300/80"
                  style={{ height: `${Math.max((item.problem / maxValue) * 100, item.problem > 0 ? 10 : 3)}%` }}
                />
                <div
                  className="w-1/2 rounded-t bg-emerald-300/80"
                  style={{ height: `${Math.max((item.resolved / maxValue) * 100, item.resolved > 0 ? 10 : 3)}%` }}
                />
              </div>
              <p className="mt-3 text-xs font-medium text-white">
                {new Date(`${item.date}T00:00:00`).toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric',
                })}
              </p>
              <p className="mt-1 text-xs text-slate-400">{item.total} total</p>
              <div className="mt-2 h-1 rounded-full bg-slate-800">
                <div
                  className="h-1 rounded-full bg-cyan-300"
                  style={{ width: `${barHeight}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-400">
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-sm bg-rose-300" />
          Open/problem
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-sm bg-emerald-300" />
          Resolved
        </span>
      </div>
    </section>
  );
}

function MetricList({ title, items }: { title: string; items: WeeklyDiscordReportMetric[] }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-5">
      <div className="flex items-center gap-2">
        <Server className="h-4 w-4 text-cyan-300" aria-hidden="true" />
        <h4 className="text-sm font-semibold text-white">{title}</h4>
      </div>
      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div key={item.label} className="flex items-center justify-between gap-3 text-sm">
            <span className="text-slate-300">{item.label}</span>
            <span className="font-semibold text-white">{item.value}</span>
          </div>
        ))}
        {items.length === 0 ? <p className="text-sm text-slate-500">No data</p> : null}
      </div>
    </div>
  );
}
