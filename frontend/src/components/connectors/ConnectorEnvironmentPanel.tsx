import { FormEvent, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Eye, EyeOff, Save, TerminalSquare } from 'lucide-react';

import {
  ConnectorEnvironment,
  getConnectorEnvironment,
  updateConnectorEnvironment,
} from '../../services/api';

const fieldGroups = [
  {
    title: 'Runtime',
    fields: ['EVENT_SOURCE', 'ENABLE_DISCORD', 'ENABLE_ZABBIX_API', 'ENABLE_ZABBIX_DB'],
  },
  {
    title: 'Discord',
    fields: ['DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'DISCORD_CHANNEL_ID'],
  },
  {
    title: 'Zabbix API',
    fields: ['ZABBIX_API_URL', 'ZABBIX_WEB_URL', 'ZABBIX_USERNAME', 'ZABBIX_PASSWORD'],
  },
  {
    title: 'Zabbix Database',
    fields: [
      'ZABBIX_DB_HOST',
      'ZABBIX_DB_PORT',
      'ZABBIX_DB_NAME',
      'ZABBIX_DB_USER',
      'ZABBIX_DB_PASSWORD',
    ],
  },
] as const;

const booleanFields = new Set(['ENABLE_DISCORD', 'ENABLE_ZABBIX_API', 'ENABLE_ZABBIX_DB']);
const sourceOptions = ['discord', 'zabbix_api', 'zabbix_database', 'multiple'];

export function ConnectorEnvironmentPanel() {
  const [environment, setEnvironment] = useState<ConnectorEnvironment | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const valueMeta = useMemo(() => {
    const meta = new Map<string, { secret: boolean; configured: boolean }>();
    for (const item of environment?.values ?? []) {
      meta.set(item.key, { secret: item.secret, configured: item.configured });
    }
    return meta;
  }, [environment]);

  useEffect(() => {
    async function loadEnvironment() {
      try {
        const response = await getConnectorEnvironment();
        setEnvironment(response);
        setValues(Object.fromEntries(response.values.map((item) => [item.key, item.value])));
      } catch {
        setError('Impossible de charger la configuration des connecteurs.');
      }
    }

    void loadEnvironment();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setMessage(null);
    setError(null);
    try {
      const response = await updateConnectorEnvironment(values);
      setEnvironment(response);
      setValues(Object.fromEntries(response.values.map((item) => [item.key, item.value])));
      setMessage('Configuration .env sauvegardee. Redemarre les services pour appliquer.');
    } catch {
      setError('La sauvegarde a echoue. Verifie ton role admin et les valeurs saisies.');
    } finally {
      setIsSaving(false);
    }
  }

  function updateValue(key: string, value: string) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function toggleSecret(key: string) {
    setVisibleSecrets((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  return (
    <section className="rounded-md border border-cyan-300/20 bg-cyan-300/[0.04] p-6">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Admin</p>
          <h3 className="mt-2 text-lg font-semibold text-white">Configurer les connecteurs</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
            Modifie les variables autorisees du fichier `.env` depuis l'application. Les secrets
            restent masques et les changements s'appliquent apres redemarrage Docker.
          </p>
        </div>
        {environment ? (
          <div className="rounded-md border border-white/10 bg-slate-950/70 p-3 text-sm text-slate-300">
            <div className="flex items-center gap-2 font-semibold text-cyan-100">
              <TerminalSquare className="h-4 w-4" aria-hidden="true" />
              Apply command
            </div>
            <code className="mt-2 block text-xs text-slate-200">{environment.apply_command}</code>
          </div>
        ) : null}
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        {fieldGroups.map((group) => (
          <div key={group.title} className="rounded-md border border-white/10 bg-slate-950/60 p-4">
            <h4 className="text-sm font-semibold text-white">{group.title}</h4>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              {group.fields.map((key) => {
                const meta = valueMeta.get(key);
                const isSecret = meta?.secret ?? false;
                const isVisible = visibleSecrets.has(key);
                return (
                  <label key={key} className="block">
                    <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                      {key}
                      {meta?.configured ? (
                        <span className="rounded bg-emerald-300/10 px-1.5 py-0.5 text-[10px] text-emerald-200">
                          set
                        </span>
                      ) : null}
                    </span>
                    {key === 'EVENT_SOURCE' ? (
                      <select
                        value={values[key] ?? ''}
                        onChange={(event) => updateValue(key, event.target.value)}
                        className="mt-2 w-full rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white outline-none transition focus:border-cyan-300"
                      >
                        {sourceOptions.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    ) : booleanFields.has(key) ? (
                      <select
                        value={values[key] ?? 'false'}
                        onChange={(event) => updateValue(key, event.target.value)}
                        className="mt-2 w-full rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white outline-none transition focus:border-cyan-300"
                      >
                        <option value="true">true</option>
                        <option value="false">false</option>
                      </select>
                    ) : (
                      <div className="mt-2 flex rounded-md border border-white/10 bg-slate-950 focus-within:border-cyan-300">
                        <input
                          value={values[key] ?? ''}
                          onChange={(event) => updateValue(key, event.target.value)}
                          type={isSecret && !isVisible ? 'password' : 'text'}
                          className="min-w-0 flex-1 rounded-l-md bg-transparent px-3 py-2 text-sm text-white outline-none"
                          autoComplete="off"
                        />
                        {isSecret ? (
                          <button
                            type="button"
                            onClick={() => toggleSecret(key)}
                            className="flex w-10 items-center justify-center text-slate-400 transition hover:text-white"
                            aria-label={isVisible ? 'Hide secret' : 'Show secret'}
                          >
                            {isVisible ? (
                              <EyeOff className="h-4 w-4" aria-hidden="true" />
                            ) : (
                              <Eye className="h-4 w-4" aria-hidden="true" />
                            )}
                          </button>
                        ) : null}
                      </div>
                    )}
                  </label>
                );
              })}
            </div>
          </div>
        ))}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-2 text-sm text-amber-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>
              Les changements sont sauvegardes dans `.env`; redemarre backend, scheduler et nginx.
            </span>
          </div>
          <button
            type="submit"
            disabled={isSaving}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Save className="h-4 w-4" aria-hidden="true" />
            {isSaving ? 'Sauvegarde...' : 'Sauvegarder .env'}
          </button>
        </div>
      </form>

      {message ? (
        <p className="mt-4 rounded-md border border-emerald-300/20 bg-emerald-300/[0.08] p-3 text-sm text-emerald-100">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="mt-4 rounded-md border border-rose-300/20 bg-rose-300/[0.08] p-3 text-sm text-rose-100">
          {error}
        </p>
      ) : null}
    </section>
  );
}
