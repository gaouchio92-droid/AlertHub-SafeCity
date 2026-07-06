import { useEffect, useState } from 'react';
import { CalendarClock, CheckCircle2, RefreshCw, Server } from 'lucide-react';

import {
  EventSyncResult,
  WeeklyDiscordReport,
  WeeklyDiscordReportStatus,
  getWeeklyDiscordReport,
  getWeeklyDiscordReportStatus,
  syncEvents,
} from '../services/api';

export function ReportsPage() {
  const [status, setStatus] = useState<WeeklyDiscordReportStatus | null>(null);
  const [report, setReport] = useState<WeeklyDiscordReport | null>(null);
  const [syncResult, setSyncResult] = useState<EventSyncResult | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Reports</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Weekly Discord report</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">
          Rolling seven-day summary generated from normalized Discord events stored in PostgreSQL.
        </p>
      </div>

      <div className="rounded-md border border-white/10 bg-white/[0.04] p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <CalendarClock className="h-6 w-6 text-cyan-300" aria-hidden="true" />
              <h3 className="text-lg font-semibold text-white">
                {status?.feature ?? 'Weekly Discord report'}
              </h3>
            </div>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">
              {status?.reason ?? 'Loading report status.'}
            </p>
          </div>
          <span
            className={[
              'rounded-md px-3 py-1.5 text-sm font-semibold',
              status?.implemented
                ? 'bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20'
                : 'bg-amber-400/10 text-amber-300 ring-1 ring-amber-400/20',
            ].join(' ')}
          >
            {status?.implemented ? 'Implemented' : 'Not implemented'}
          </span>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-400">
            {report
              ? `${new Date(report.period_start).toLocaleString()} - ${new Date(
                  report.period_end,
                ).toLocaleString()}`
              : 'Loading report period'}
          </p>
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

        {syncResult ? (
          <p className="mt-3 text-sm text-emerald-300">
            Sync complete: {syncResult.received} received, {syncResult.created} created,{' '}
            {syncResult.updated} updated.
          </p>
        ) : null}

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {[
            ['Total events', report?.total_events ?? 0],
            ['Open events', report?.open_events ?? 0],
            ['Resolved events', report?.resolved_events ?? 0],
          ].map(([label, value]) => (
            <div key={label} className="rounded-md border border-white/10 bg-slate-950/60 p-4">
              <p className="text-sm text-slate-400">{label}</p>
              <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <MetricList title="By host" items={report?.by_host ?? []} />
          <MetricList title="By severity" items={report?.by_severity ?? []} />
        </div>

        <div className="mt-6">
          <h4 className="text-sm font-semibold text-white">Recent Discord events</h4>
          <div className="mt-3 divide-y divide-white/10 overflow-hidden rounded-md border border-white/10">
            {(report?.recent_events ?? []).map((event) => (
              <div key={event.problem_id ?? event.started_at} className="bg-slate-950/60 p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <p className="font-medium text-white">
                    {event.problem_name || event.problem_id || 'Discord event'}
                  </p>
                  <span className="text-xs uppercase tracking-wide text-cyan-300">
                    {event.status ?? 'unknown'}
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-400">
                  {event.host ?? 'Unknown host'} · {event.severity ?? 'Unknown severity'} ·{' '}
                  {event.started_at ? new Date(event.started_at).toLocaleString() : 'No timestamp'}
                </p>
              </div>
            ))}
            {report?.recent_events.length === 0 ? (
              <p className="bg-slate-950/60 p-4 text-sm text-slate-400">
                No Discord events stored for this period.
              </p>
            ) : null}
          </div>
        </div>

        {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
      </div>
    </section>
  );
}

function MetricList({
  title,
  items,
}: {
  title: string;
  items: { label: string; value: number }[];
}) {
  return (
    <div className="rounded-md border border-white/10 bg-slate-950/60 p-4">
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
