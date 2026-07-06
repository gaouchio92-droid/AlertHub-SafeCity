import { Database, Network, Server, ShieldCheck } from 'lucide-react';

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

export function HomePage() {
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
          {['Docker Compose', 'API Gateway', 'Database Migrations'].map((item) => (
            <div key={item} className="rounded-md border border-white/10 bg-slate-950/60 p-4">
              <p className="text-sm font-medium text-slate-200">{item}</p>
              <p className="mt-2 text-sm text-emerald-300">Configured</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
