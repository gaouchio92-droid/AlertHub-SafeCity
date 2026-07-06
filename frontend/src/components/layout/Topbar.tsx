import { Activity, Menu, Search } from 'lucide-react';
import { NavLink } from 'react-router-dom';

type TopbarProps = {
  onOpenMenu: () => void;
};

export function Topbar({ onOpenMenu }: TopbarProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/85 backdrop-blur">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3 lg:hidden">
          <button
            type="button"
            onClick={onOpenMenu}
            className="flex h-10 w-10 items-center justify-center rounded-md text-slate-300 transition hover:bg-white/5 hover:text-white"
            aria-label="Open menu"
            aria-controls="mobile-navigation"
          >
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
          <span className="text-base font-semibold text-white">AlertHub Safe City</span>
        </div>

        <div className="hidden min-w-0 flex-1 items-center gap-3 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-slate-400 lg:flex">
          <Search className="h-4 w-4" aria-hidden="true" />
          <span className="text-sm">Platform search</span>
        </div>

        <nav className="flex items-center gap-2 lg:hidden" aria-label="Mobile navigation">
          <NavLink className="rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-white/5" to="/home">
            Home
          </NavLink>
          <NavLink
            className="rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-white/5"
            to="/event-sources"
          >
            Connectors
          </NavLink>
          <NavLink className="rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-white/5" to="/reports">
            Reports
          </NavLink>
          <NavLink className="rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-white/5" to="/settings">
            Settings
          </NavLink>
        </nav>

        <div className="hidden items-center gap-2 rounded-md border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-sm font-medium text-emerald-200 sm:flex">
          <Activity className="h-4 w-4" aria-hidden="true" />
          Infrastructure online
        </div>
      </div>
    </header>
  );
}
