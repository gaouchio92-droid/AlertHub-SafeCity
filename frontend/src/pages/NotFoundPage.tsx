import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="flex min-h-[60vh] items-center justify-center">
      <div className="max-w-xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">404</p>
        <h2 className="mt-3 text-3xl font-semibold text-white">Page not found</h2>
        <p className="mt-3 text-base leading-7 text-slate-300">
          The requested route is not part of the AlertHub Safe City infrastructure shell.
        </p>
        <Link
          to="/home"
          className="mt-6 inline-flex items-center rounded-md bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
        >
          Return home
        </Link>
      </div>
    </section>
  );
}
