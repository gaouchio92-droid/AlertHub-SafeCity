import { Navigate, useLocation } from 'react-router-dom';

import { useAuth } from './AuthProvider';

export function RequireAdmin({ children }: { children: JSX.Element }) {
  const { isAdmin, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="rounded-md border border-white/10 bg-white/[0.04] p-6 text-sm text-slate-300">
        Loading access policy...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!isAdmin) {
    return (
      <section className="rounded-md border border-rose-300/25 bg-rose-300/[0.06] p-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-rose-200">
          Access denied
        </p>
        <h2 className="mt-2 text-2xl font-semibold text-white">Administrator role required</h2>
        <p className="mt-3 text-sm leading-6 text-slate-300">
          Connector and settings administration are restricted to users with the admin role.
        </p>
      </section>
    );
  }

  return children;
}
