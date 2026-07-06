import { BarChart3, FileText, Home, PlugZap, Settings, ShieldAlert } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const navigation = [
  { name: 'Home', href: '/home', icon: Home },
  { name: 'Connectors', href: '/event-sources', icon: PlugZap },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-white/10 bg-slate-950/95 px-5 py-6 lg:block">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-md bg-cyan-500/15 text-cyan-300 ring-1 ring-cyan-400/30">
          <ShieldAlert className="h-6 w-6" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">AlertHub</p>
          <h1 className="text-lg font-semibold text-white">Safe City</h1>
        </div>
      </div>

      <nav className="mt-10 space-y-1" aria-label="Primary navigation">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition',
                isActive
                  ? 'bg-cyan-500/15 text-cyan-100 ring-1 ring-cyan-400/20'
                  : 'text-slate-300 hover:bg-white/5 hover:text-white',
              ].join(' ')
            }
          >
            <item.icon className="h-5 w-5" aria-hidden="true" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="absolute bottom-6 left-5 right-5 rounded-md border border-white/10 bg-white/[0.03] p-4">
        <div className="flex items-center gap-3 text-slate-300">
          <BarChart3 className="h-5 w-5 text-emerald-300" aria-hidden="true" />
          <span className="text-sm font-medium">Monitoring analytics foundation</span>
        </div>
      </div>
    </aside>
  );
}
