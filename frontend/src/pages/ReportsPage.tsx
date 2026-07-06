import { useEffect, useState } from 'react';
import { CalendarClock, CheckCircle2, CircleDashed } from 'lucide-react';

import { WeeklyDiscordReportStatus, getWeeklyDiscordReportStatus } from '../services/api';

export function ReportsPage() {
  const [status, setStatus] = useState<WeeklyDiscordReportStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadStatus() {
      try {
        const response = await getWeeklyDiscordReportStatus();
        if (isMounted) {
          setStatus(response);
          setError(null);
        }
      } catch {
        if (isMounted) {
          setError('Weekly report status unavailable');
        }
      }
    }

    void loadStatus();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Reports</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">Weekly Discord report</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">
          The weekly report will depend on Discord ingestion, normalized event persistence, and
          weekly aggregation.
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

        <div className="mt-6">
          <h4 className="text-sm font-semibold text-white">Required before available</h4>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {(status?.required_before_available ?? []).map((item, index) => (
              <div key={item} className="flex gap-3 rounded-md border border-white/10 bg-slate-950/60 p-4">
                {index === 0 ? (
                  <CircleDashed className="mt-0.5 h-5 w-5 text-amber-300" aria-hidden="true" />
                ) : (
                  <CheckCircle2 className="mt-0.5 h-5 w-5 text-slate-500" aria-hidden="true" />
                )}
                <p className="text-sm leading-6 text-slate-300">{item}</p>
              </div>
            ))}
          </div>
        </div>

        {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
      </div>
    </section>
  );
}
