import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft, ArrowRight, ExternalLink, Filter, RefreshCw } from 'lucide-react';

import { AlertEvent, EventList, EventSyncResult, getEvents, syncEvents } from '../services/api';

const PAGE_SIZE = 20;

type EventFilterState = {
  status: string;
  severity: string;
  includeUnparsed: boolean;
};

function formatDateTime(value: string | null) {
  if (!value) {
    return 'No timestamp';
  }
  return new Date(value).toLocaleString();
}

function formatDuration(seconds: number | null) {
  if (!seconds) {
    return 'Open';
  }
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  return [
    hours ? `${hours}h` : '',
    minutes ? `${minutes}m` : '',
    remainingSeconds ? `${remainingSeconds}s` : '',
  ]
    .filter(Boolean)
    .join(' ');
}

function normalizedLinks(event: AlertEvent) {
  const normalized = event.raw_payload.normalized;
  if (!normalized || typeof normalized !== 'object' || !('links' in normalized)) {
    return [];
  }
  const links = (normalized as { links?: unknown }).links;
  if (!Array.isArray(links)) {
    return [];
  }
  return links.filter((link): link is string => typeof link === 'string' && link.length > 0);
}

function eventTitle(event: AlertEvent) {
  if (event.problem_name) {
    return event.problem_name;
  }
  if (event.problem_id) {
    return `Discord message ${event.problem_id.slice(-6)}`;
  }
  return 'Unparsed event';
}

function statusClassName(status: string | null) {
  if (status === 'resolved') {
    return 'border-emerald-300/30 bg-emerald-300/10 text-emerald-200';
  }
  if (status === 'problem') {
    return 'border-rose-300/30 bg-rose-300/10 text-rose-200';
  }
  return 'border-slate-300/20 bg-slate-300/10 text-slate-200';
}

export function EventsPage() {
  const [events, setEvents] = useState<EventList | null>(null);
  const [filters, setFilters] = useState<EventFilterState>({
    status: '',
    severity: '',
    includeUnparsed: false,
  });
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<EventSyncResult | null>(null);

  const pageNumber = useMemo(() => Math.floor(offset / PAGE_SIZE) + 1, [offset]);
  const canGoBack = offset > 0;
  const canGoForward = Boolean(events && offset + events.limit < events.total);

  const loadEvents = useCallback(async (nextOffset: number) => {
    setIsLoading(true);
    try {
      const response = await getEvents({
        source: 'discord',
        status: filters.status || undefined,
        severity: filters.severity || undefined,
        include_unparsed: filters.includeUnparsed,
        limit: PAGE_SIZE,
        offset: nextOffset,
      });
      setEvents(response);
      setOffset(nextOffset);
      setError(null);
    } catch {
      setError('Events are unavailable');
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void loadEvents(0);
  }, [loadEvents]);

  async function handleSync() {
    setIsSyncing(true);
    try {
      const response = await syncEvents();
      setSyncResult(response);
      await loadEvents(0);
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
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Events</p>
          <h2 className="mt-2 text-3xl font-semibold text-white">Alert event explorer</h2>
          <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">
            Triage normalized Discord alerts with host, severity, status, timestamps, and source
            links.
          </p>
        </div>
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

      <section className="rounded-md border border-white/10 bg-white/[0.04] p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-5 w-5 text-cyan-300" aria-hidden="true" />
            <h3 className="text-base font-semibold text-white">Filters</h3>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:min-w-[760px]">
            <label className="space-y-2 text-sm text-slate-300">
              <span>Status</span>
              <select
                value={filters.status}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, status: event.target.value }))
                }
                className="w-full rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-white outline-none transition focus:border-cyan-300"
              >
                <option value="">All statuses</option>
                <option value="problem">Problem</option>
                <option value="resolved">Resolved</option>
              </select>
            </label>

            <label className="space-y-2 text-sm text-slate-300">
              <span>Severity</span>
              <select
                value={filters.severity}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, severity: event.target.value }))
                }
                className="w-full rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-white outline-none transition focus:border-cyan-300"
              >
                <option value="">All severities</option>
                <option value="Average">Average</option>
                <option value="Warning">Warning</option>
                <option value="High">High</option>
                <option value="Disaster">Disaster</option>
              </select>
            </label>

            <label className="flex items-end gap-3 rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={filters.includeUnparsed}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    includeUnparsed: event.target.checked,
                  }))
                }
                className="mb-1 h-4 w-4 accent-cyan-300"
              />
              Include raw unparsed events
            </label>
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-2 text-sm text-slate-400 sm:flex-row sm:items-center sm:justify-between">
          <span>
            {events ? `${events.total} matching events` : 'Loading events'}
            {syncResult
              ? `, last sync ${syncResult.received} read / ${syncResult.updated} refreshed`
              : ''}
          </span>
          {isLoading ? <span className="text-cyan-200">Refreshing table</span> : null}
        </div>
      </section>

      <section className="rounded-md border border-white/10 bg-white/[0.04] p-5">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1040px] text-left text-sm">
            <thead className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="py-3 pr-4">Problem</th>
                <th className="py-3 pr-4">Host</th>
                <th className="py-3 pr-4">Severity</th>
                <th className="py-3 pr-4">Status</th>
                <th className="py-3 pr-4">Duration</th>
                <th className="py-3 pr-4">Started</th>
                <th className="py-3 pr-4">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {(events?.items ?? []).map((event) => {
                const links = normalizedLinks(event);
                return (
                  <tr key={event.id} className="align-top text-slate-300">
                    <td className="py-3 pr-4">
                      <p className="font-medium text-white">{eventTitle(event)}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {event.problem_id ? `ID ${event.problem_id}` : 'No problem id'}
                      </p>
                    </td>
                    <td className="py-3 pr-4">{event.host ?? 'Not detected'}</td>
                    <td className="py-3 pr-4">{event.severity ?? 'Not detected'}</td>
                    <td className="py-3 pr-4">
                      <span
                        className={[
                          'inline-flex rounded-md border px-2 py-1 text-xs font-medium',
                          statusClassName(event.status),
                        ].join(' ')}
                      >
                        {event.status ?? 'unknown'}
                      </span>
                    </td>
                    <td className="py-3 pr-4">{formatDuration(event.duration)}</td>
                    <td className="py-3 pr-4">{formatDateTime(event.started_at)}</td>
                    <td className="py-3 pr-4">
                      {links.length > 0 ? (
                        <a
                          href={links[0]}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-cyan-300 underline-offset-4 hover:underline"
                        >
                          Open
                          <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                        </a>
                      ) : (
                        <span className="text-slate-500">No link</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {events?.items.length === 0 ? (
            <p className="rounded-md border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-400">
              No events match the selected filters.
            </p>
          ) : null}
        </div>

        <div className="mt-5 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => void loadEvents(Math.max(offset - PAGE_SIZE, 0))}
            disabled={!canGoBack}
            className="inline-flex items-center gap-2 rounded-md border border-white/10 px-3 py-2 text-sm text-slate-200 transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Previous
          </button>
          <span className="text-sm text-slate-400">Page {pageNumber}</span>
          <button
            type="button"
            onClick={() => void loadEvents(offset + PAGE_SIZE)}
            disabled={!canGoForward}
            className="inline-flex items-center gap-2 rounded-md border border-white/10 px-3 py-2 text-sm text-slate-200 transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </section>

      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}
