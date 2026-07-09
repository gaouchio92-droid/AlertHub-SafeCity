import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Database,
  FileDown,
  RefreshCw,
  Send,
  Server,
} from 'lucide-react';

import {
  ConnectorDiagnostic,
  EventSyncResult,
  WeeklyDiscordReport,
  WeeklyDiscordReportDailyTrend,
  WeeklyDiscordReportMetric,
  WeeklyDiscordOpenProblem,
  WeeklyDiscordReportStatus,
  WeeklyDiscordSecurityAdvisory,
  getConnectorDiagnostics,
  getWeeklyDiscordReport,
  getWeeklyDiscordReportStatus,
  pushWeeklyDiscordReportToDiscord,
  syncEvents,
} from '../services/api';
import { useI18n } from '../i18n/I18nProvider';

function formatDateTime(value: string | null, fallback: string) {
  if (!value) {
    return fallback;
  }
  return new Date(value).toLocaleString();
}

function formatPeriod(report: WeeklyDiscordReport | null, loadingLabel: string, fallback: string) {
  if (!report) {
    return loadingLabel;
  }
  return `${formatDateTime(report.period_start, fallback)} - ${formatDateTime(
    report.period_end,
    fallback,
  )}`;
}

export function ReportsPage() {
  const { t } = useI18n();
  const [status, setStatus] = useState<WeeklyDiscordReportStatus | null>(null);
  const [report, setReport] = useState<WeeklyDiscordReport | null>(null);
  const [discordDiagnostic, setDiscordDiagnostic] = useState<ConnectorDiagnostic | null>(null);
  const [syncResult, setSyncResult] = useState<EventSyncResult | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isPushingReport, setIsPushingReport] = useState(false);
  const [pushMessage, setPushMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const readableEvents = useMemo(() => {
    if (!report || report.total_events === 0) {
      return 0;
    }
    return report.total_events - report.data_quality.unnamed_events;
  }, [report]);

  const loadReport = useCallback(async () => {
    try {
      const [statusResponse, reportResponse, diagnosticsResponse] = await Promise.all([
        getWeeklyDiscordReportStatus(),
        getWeeklyDiscordReport(),
        getConnectorDiagnostics(),
      ]);
      setStatus(statusResponse);
      setReport(reportResponse);
      setDiscordDiagnostic(
        diagnosticsResponse.find((diagnostic) => diagnostic.source === 'discord') ?? null,
      );
      setError(null);
    } catch {
      setError(t.reports.reportUnavailable);
    }
  }, [t.reports.reportUnavailable]);

  useEffect(() => {
    void loadReport();
  }, [loadReport]);

  async function handleSync() {
    setIsSyncing(true);
    setPushMessage(null);
    try {
      const response = await syncEvents();
      setSyncResult(response);
      await loadReport();
    } catch {
      setError(t.reports.syncFailed);
    } finally {
      setIsSyncing(false);
    }
  }

  async function handlePushReportToDiscord() {
    setIsPushingReport(true);
    setPushMessage(null);
    setError(null);
    try {
      const response = await pushWeeklyDiscordReportToDiscord();
      setPushMessage(
        `${t.reports.pushDiscordSuccess} (${response.filename}, channel ${response.channel_id})`,
      );
    } catch {
      setError(t.reports.pushDiscordFailed);
    } finally {
      setIsPushingReport(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
            {t.reports.eyebrow}
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-white">{t.reports.title}</h2>
          <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">
            {t.reports.subtitle}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <a
            href="/api/v1/reports/weekly-discord/export.pdf"
            download="alerthub-weekly-discord-report.pdf"
            className="inline-flex items-center justify-center gap-2 rounded-md bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
          >
            <FileDown className="h-4 w-4" aria-hidden="true" />
            {t.reports.exportPdf}
          </a>
          <button
            type="button"
            onClick={handlePushReportToDiscord}
            disabled={isPushingReport}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Send className={['h-4 w-4', isPushingReport ? 'animate-pulse' : ''].join(' ')} />
            {isPushingReport ? t.reports.pushingDiscord : t.reports.pushDiscord}
          </button>
          <a
            href="/api/v1/reports/weekly-discord/export"
            download="alerthub-weekly-discord-report.md"
            className="inline-flex items-center justify-center gap-2 rounded-md border border-white/10 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/5"
          >
            {t.reports.markdown}
          </a>
          <button
            type="button"
            onClick={handleSync}
            disabled={isSyncing}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw className={['h-4 w-4', isSyncing ? 'animate-spin' : ''].join(' ')} />
            {t.reports.syncDiscord}
          </button>
        </div>
      </div>

      <section className="rounded-md border border-white/10 bg-white/[0.04] p-6">
        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <div>
            <div className="flex items-center gap-3">
              <CalendarClock className="h-6 w-6 text-cyan-300" aria-hidden="true" />
              <h3 className="text-lg font-semibold text-white">
                {status?.feature ?? t.reports.weeklyReport}
              </h3>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {status?.reason ?? t.reports.loadingStatus}
            </p>
            <p className="mt-3 text-sm text-slate-400">
              {formatPeriod(report, t.reports.loadingPeriod, t.reports.noTimestamp)}
            </p>
          </div>

          <div className="rounded-md border border-emerald-400/20 bg-emerald-400/[0.06] p-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-300" aria-hidden="true" />
              <p className="text-sm font-semibold text-emerald-200">{t.reports.pipelineActive}</p>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {t.reports.pipelineDescription}
            </p>
            {syncResult ? (
              <p className="mt-3 text-sm text-emerald-200">
                {t.reports.lastSync}: {syncResult.received} {t.reports.read},{' '}
                {syncResult.created} {t.reports.new}, {syncResult.updated}{' '}
                {t.reports.refreshed}.
              </p>
            ) : null}
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label={t.reports.discordMessages} value={report?.total_events ?? 0} />
          <MetricCard label={t.reports.readableAlerts} value={readableEvents} />
          <MetricCard label={t.reports.stillOpen} value={report?.open_events ?? 0} />
          <MetricCard label={t.reports.resolved} value={report?.resolved_events ?? 0} />
        </div>
      </section>

      <DailyTrendPanel items={report?.daily_trend ?? []} />

      <StabilizationRecommendationsPanel report={report} />

      <SecurityAdvisoriesPanel items={report?.security_advisories ?? []} />

      <OpenProblemsPanel items={report?.open_problems ?? []} />

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <DiscordReachabilityPanel report={report} diagnostic={discordDiagnostic} />
        <div className="grid gap-4 md:grid-cols-2">
          <MetricList title={t.reports.detectedHosts} items={report?.by_host ?? []} />
          <MetricList title={t.reports.detectedSeverities} items={report?.by_severity ?? []} />
        </div>
      </section>

      <section className="rounded-md border border-white/10 bg-white/[0.04] p-6">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-cyan-300" aria-hidden="true" />
          <h3 className="text-lg font-semibold text-white">{t.reports.recentEvents}</h3>
        </div>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="py-3 pr-4">{t.reports.event}</th>
                <th className="py-3 pr-4">{t.reports.host}</th>
                <th className="py-3 pr-4">{t.reports.severity}</th>
                <th className="py-3 pr-4">{t.reports.status}</th>
                <th className="py-3 pr-4">{t.reports.links}</th>
                <th className="py-3 pr-4">{t.reports.received}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {(report?.recent_events ?? []).map((event) => (
                <tr key={event.problem_id ?? event.started_at} className="text-slate-300">
                  <td className="py-3 pr-4">
                    <p className="font-medium text-white">{event.title}</p>
                    {!event.details_available ? (
                      <p className="mt-1 text-xs text-amber-300">
                        {t.reports.rawStored}
                      </p>
                    ) : null}
                    {event.operational_data ? (
                      <p className="mt-1 text-xs text-slate-400">{event.operational_data}</p>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4">{event.host ?? t.reports.notDetected}</td>
                  <td className="py-3 pr-4">{event.severity ?? t.reports.notDetected}</td>
                  <td className="py-3 pr-4">{event.status ?? t.reports.unknown}</td>
                  <td className="py-3 pr-4">
                    {event.links.length > 0 ? (
                      <a
                        href={event.links[0]}
                        target="_blank"
                        rel="noreferrer"
                        className="text-cyan-300 underline-offset-4 hover:underline"
                      >
                        {t.common.open}
                      </a>
                    ) : (
                      t.reports.noLink
                    )}
                  </td>
                  <td className="py-3 pr-4">
                    {formatDateTime(event.started_at, t.reports.noTimestamp)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {report?.recent_events.length === 0 ? (
            <p className="rounded-md border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-400">
              {t.reports.noEvents}
            </p>
          ) : null}
        </div>
      </section>

      {pushMessage ? (
        <p className="rounded-md border border-emerald-300/20 bg-emerald-300/[0.08] p-4 text-sm text-emerald-100">
          {pushMessage}
        </p>
      ) : null}

      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}

function StabilizationRecommendationsPanel({ report }: { report: WeeklyDiscordReport | null }) {
  const { t } = useI18n();
  const recommendations: string[] = [...t.reports.recommendations];

  if ((report?.data_quality.unnamed_events ?? 0) > 0) {
    recommendations.push(t.reports.parsingRecommendation);
  }

  if ((report?.open_events ?? 0) > 0) {
    recommendations.push(t.reports.openProblemsRecommendation);
  }

  return (
    <section className="rounded-md border border-cyan-300/20 bg-cyan-300/[0.05] p-6">
      <div className="flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-cyan-200" aria-hidden="true" />
        <h3 className="text-lg font-semibold text-white">{t.reports.recommendationsTitle}</h3>
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

function SecurityAdvisoriesPanel({ items }: { items: WeeklyDiscordSecurityAdvisory[] }) {
  const { t } = useI18n();

  return (
    <section className="rounded-md border border-amber-300/25 bg-amber-300/[0.06] p-6">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-5 w-5 text-amber-200" aria-hidden="true" />
        <div>
          <h3 className="text-lg font-semibold text-white">{t.reports.securityWatchTitle}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            {t.reports.securityWatchSubtitle}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        {items.map((item) => (
          <article
            key={`${item.component}-${item.reference}`}
            className="rounded-md border border-white/10 bg-slate-950/70 p-4"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-white">{item.component}</p>
                <p className="mt-1 text-xs text-slate-500">{item.current_version}</p>
              </div>
              <span className="inline-flex w-fit rounded-md bg-amber-400/10 px-2.5 py-1 text-xs font-semibold text-amber-100 ring-1 ring-amber-300/20">
                {item.severity}
              </span>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <ProblemDetail label={t.reports.status} value={item.status} />
              <ProblemDetail label={t.reports.reference} value={item.reference} />
            </div>

            <div className="mt-4 rounded-md border border-white/10 bg-white/[0.03] p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {t.reports.exposure}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-300">{item.finding}</p>
            </div>

            <div className="mt-4 rounded-md border border-emerald-300/15 bg-emerald-300/[0.04] p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-200">
                {t.reports.recommendation}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-200">{item.recommendation}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function OpenProblemsPanel({ items }: { items: WeeklyDiscordOpenProblem[] }) {
  const { t } = useI18n();

  return (
    <section className="rounded-md border border-rose-300/25 bg-rose-300/[0.06] p-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-rose-200" aria-hidden="true" />
            <h3 className="text-lg font-semibold text-white">{t.reports.unresolvedTitle}</h3>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            {t.reports.unresolvedSubtitle}
          </p>
        </div>
        <span className="inline-flex w-fit rounded-md bg-rose-400/10 px-3 py-1.5 text-sm font-semibold text-rose-100 ring-1 ring-rose-300/25">
          {items.length}
        </span>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        {items.map((problem) => (
          <article
            key={`${problem.problem_id ?? problem.title}-${problem.started_at ?? 'unknown'}`}
            className="rounded-md border border-white/10 bg-slate-950/70 p-4"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white">{problem.title}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {problem.problem_id ? `ID ${problem.problem_id}` : t.reports.unknown}
                </p>
              </div>
              <span className="inline-flex w-fit rounded-md bg-amber-400/10 px-2.5 py-1 text-xs font-semibold text-amber-100 ring-1 ring-amber-300/20">
                {problem.severity ?? t.reports.notDetected}
              </span>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <ProblemDetail label={t.reports.host} value={problem.host ?? t.reports.notDetected} />
              <ProblemDetail label={t.reports.age} value={problem.age_label} />
              <ProblemDetail label={t.reports.status} value={problem.status ?? t.reports.unknown} />
            </div>

            {problem.operational_data ? (
              <div className="mt-4 rounded-md border border-white/10 bg-white/[0.03] p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {t.reports.operationalData}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {problem.operational_data}
                </p>
              </div>
            ) : null}

            <div className="mt-4 rounded-md border border-white/10 bg-white/[0.03] p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {t.reports.action}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-200">
                {problem.recommended_action}
              </p>
            </div>

            {problem.links.length > 0 ? (
              <a
                href={problem.links[0]}
                target="_blank"
                rel="noreferrer"
                className="mt-4 inline-flex items-center rounded-md bg-cyan-400 px-3 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
              >
                {t.reports.viewProblem}
              </a>
            ) : null}
          </article>
        ))}
      </div>

      {items.length === 0 ? (
        <p className="mt-4 rounded-md border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-300">
          {t.reports.noUnresolved}
        </p>
      ) : null}
    </section>
  );
}

function ProblemDetail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.03] p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 break-words text-sm font-medium text-white">{value}</p>
    </div>
  );
}

function DiscordReachabilityPanel({
  report,
  diagnostic,
}: {
  report: WeeklyDiscordReport | null;
  diagnostic: ConnectorDiagnostic | null;
}) {
  const { t } = useI18n();
  const warnings = report?.data_quality.warnings ?? [];
  const isReachable = diagnostic?.ready ?? false;
  const missingConfiguration = diagnostic?.missing_configuration ?? [];
  const panelTone = isReachable
    ? 'border-emerald-300/25 bg-emerald-300/[0.07]'
    : 'border-rose-300/25 bg-rose-300/[0.07]';
  const statusTone = isReachable
    ? 'bg-emerald-400/10 text-emerald-200 ring-1 ring-emerald-300/25'
    : 'bg-rose-400/10 text-rose-200 ring-1 ring-rose-300/25';
  const Icon = isReachable ? CheckCircle2 : AlertTriangle;

  return (
    <div className={['rounded-md border p-5', panelTone].join(' ')}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-2">
          <Icon
            className={['h-5 w-5', isReachable ? 'text-emerald-200' : 'text-rose-200'].join(' ')}
            aria-hidden="true"
          />
          <h3 className="text-base font-semibold text-white">{t.reports.discordReachability}</h3>
        </div>
        <span
          className={[
            'inline-flex w-fit items-center rounded-md px-2.5 py-1 text-xs font-semibold',
            statusTone,
          ].join(' ')}
        >
          {isReachable ? t.reports.linkHealthy : t.reports.linkInterrupted}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-300">
        {t.reports.reachabilityDescription}
      </p>
      {!isReachable ? (
        <div className="mt-4 rounded-md border border-rose-300/20 bg-slate-950/60 p-3">
          <p className="text-sm font-semibold text-rose-100">
            {t.reports.connectionActionRequired}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            {t.reports.connectionActionDescription}
          </p>
          {missingConfiguration.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {missingConfiguration.map((field) => (
                <span
                  key={field}
                  className="rounded-md bg-rose-400/10 px-2 py-1 font-mono text-xs text-rose-100"
                >
                  {field}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
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
  const { t } = useI18n();
  const maxValue = Math.max(...items.map((item) => item.total), 1);

  return (
    <section className="rounded-md border border-white/10 bg-white/[0.04] p-6">
      <div className="flex items-center gap-2">
        <CalendarClock className="h-5 w-5 text-cyan-300" aria-hidden="true" />
        <h3 className="text-lg font-semibold text-white">{t.reports.dailyTrend}</h3>
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
          {t.reports.openProblem}
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-sm bg-emerald-300" />
          {t.reports.resolved}
        </span>
      </div>
    </section>
  );
}

function MetricList({ title, items }: { title: string; items: WeeklyDiscordReportMetric[] }) {
  const { t } = useI18n();

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
        {items.length === 0 ? <p className="text-sm text-slate-500">{t.common.noData}</p> : null}
      </div>
    </div>
  );
}
