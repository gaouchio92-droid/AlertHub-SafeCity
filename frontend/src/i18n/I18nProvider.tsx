/* eslint-disable react-refresh/only-export-components */
import { createContext, ReactNode, useContext, useMemo, useState } from 'react';

export type Language = 'en' | 'fr';

const STORAGE_KEY = 'alerthub-language';

const translations = {
  en: {
    common: {
      language: 'Language',
      english: 'English',
      french: 'French',
      loading: 'Loading',
      noData: 'No data',
      open: 'Open',
      healthy: 'Healthy',
      interrupted: 'Interrupted',
    },
    nav: {
      home: 'Home',
      connectors: 'Connectors',
      events: 'Events',
      reports: 'Reports',
      settings: 'Settings',
      search: 'Platform search',
      infrastructureOnline: 'Infrastructure online',
      analyticsFoundation: 'Monitoring analytics foundation',
      openMenu: 'Open menu',
      closeMenu: 'Close menu',
      closeOverlay: 'Close menu overlay',
    },
    reports: {
      eyebrow: 'Reports',
      title: 'Discord weekly operations',
      subtitle:
        'A seven-day operational view of Discord events collected from the configured alert channel and stored in PostgreSQL.',
      exportPdf: 'Export PDF',
      markdown: 'Markdown',
      syncDiscord: 'Sync Discord',
      weeklyReport: 'Weekly Discord report',
      loadingStatus: 'Loading report status.',
      loadingPeriod: 'Loading period',
      noTimestamp: 'No timestamp',
      pipelineActive: 'Pipeline active',
      pipelineDescription:
        'Discord is configured, sync is available, and events are persisted locally before reporting.',
      lastSync: 'Last sync',
      read: 'read',
      new: 'new',
      refreshed: 'refreshed',
      discordMessages: 'Discord messages',
      readableAlerts: 'Readable alerts',
      stillOpen: 'Still open',
      resolved: 'Resolved',
      dailyTrend: 'Daily alert trend',
      openProblem: 'Open/problem',
      discordReachability: 'Discord reachability',
      linkHealthy: 'Link healthy',
      linkInterrupted: 'Link interrupted',
      reachabilityDescription:
        'Discord configuration is checked from the connector engine. When the link is healthy, AlertHub can synchronize the configured channel. Message parsing quality is shown below.',
      connectionActionRequired: 'Connection action required',
      connectionActionDescription:
        'Verify the bot token, channel ID, guild ID, and restart Docker Compose after updating the `.env` file.',
      noAlertTitle: 'No alert title',
      noSeverity: 'No severity',
      noHost: 'No host',
      recommendationsTitle: 'Stabilization recommendations',
      recommendations: [
        'Schedule automatic Discord synchronization to avoid manual imports.',
        'Monitor /api/v1/health and Docker healthchecks with an external alert.',
        'Back up the PostgreSQL volume before every important update.',
        'Enable backend, nginx, and Docker log rotation to protect disk space.',
        'Run Alembic in the deployment pipeline before restarting the application.',
      ],
      parsingRecommendation:
        'Finalize Discord parsing to reduce unreadable messages in reports.',
      openProblemsRecommendation:
        'Create daily tracking for open problems with an assigned owner.',
      detectedHosts: 'Detected hosts',
      detectedSeverities: 'Detected severities',
      recentEvents: 'Recent stored events',
      event: 'Event',
      host: 'Host',
      severity: 'Severity',
      status: 'Status',
      links: 'Links',
      received: 'Received',
      notDetected: 'Not detected',
      unknown: 'unknown',
      noLink: 'No link',
      rawStored:
        'Raw Discord message stored, readable alert fields not detected yet.',
      noEvents: 'No Discord events stored for this period.',
      reportUnavailable: 'Weekly report unavailable',
      syncFailed: 'Discord synchronization failed',
    },
  },
  fr: {
    common: {
      language: 'Langue',
      english: 'Anglais',
      french: 'Francais',
      loading: 'Chargement',
      noData: 'Aucune donnee',
      open: 'Ouvrir',
      healthy: 'Sain',
      interrupted: 'Interrompu',
    },
    nav: {
      home: 'Accueil',
      connectors: 'Connecteurs',
      events: 'Evenements',
      reports: 'Rapports',
      settings: 'Parametres',
      search: 'Recherche plateforme',
      infrastructureOnline: 'Infrastructure en ligne',
      analyticsFoundation: 'Fondation analytics monitoring',
      openMenu: 'Ouvrir le menu',
      closeMenu: 'Fermer le menu',
      closeOverlay: 'Fermer le menu',
    },
    reports: {
      eyebrow: 'Rapports',
      title: 'Operations Discord hebdomadaires',
      subtitle:
        "Vue operationnelle sur sept jours des evenements Discord collectes depuis le salon d'alertes configure et stockes dans PostgreSQL.",
      exportPdf: 'Exporter PDF',
      markdown: 'Markdown',
      syncDiscord: 'Synchroniser Discord',
      weeklyReport: 'Rapport Discord hebdomadaire',
      loadingStatus: 'Chargement du statut du rapport.',
      loadingPeriod: 'Chargement de la periode',
      noTimestamp: 'Pas de date',
      pipelineActive: 'Pipeline actif',
      pipelineDescription:
        'Discord est configure, la synchronisation est disponible, et les evenements sont stockes localement avant reporting.',
      lastSync: 'Derniere synchro',
      read: 'lus',
      new: 'nouveaux',
      refreshed: 'actualises',
      discordMessages: 'Messages Discord',
      readableAlerts: 'Alertes lisibles',
      stillOpen: 'Encore ouverts',
      resolved: 'Resolus',
      dailyTrend: 'Tendance quotidienne des alertes',
      openProblem: 'Ouvert/probleme',
      discordReachability: 'Disponibilite Discord',
      linkHealthy: 'Liaison saine',
      linkInterrupted: 'Liaison interrompue',
      reachabilityDescription:
        'La configuration Discord est verifiee depuis le moteur de connecteurs. Quand la liaison est saine, AlertHub peut synchroniser le salon configure. La qualite du parsing est affichee ci-dessous.',
      connectionActionRequired: 'Action de connexion requise',
      connectionActionDescription:
        'Verifiez le token du bot, le channel ID, le guild ID, puis redemarrez Docker Compose apres modification du fichier `.env`.',
      noAlertTitle: "Sans titre d'alerte",
      noSeverity: 'Sans severite',
      noHost: 'Sans host',
      recommendationsTitle: 'Recommandations de stabilisation',
      recommendations: [
        'Planifier une synchronisation Discord automatique pour eviter les imports manuels.',
        'Surveiller /api/v1/health et les healthchecks Docker avec une alerte externe.',
        'Sauvegarder le volume PostgreSQL avant chaque mise a jour importante.',
        'Activer une rotation des logs backend, nginx et Docker pour proteger le disque.',
        "Executer Alembic dans le pipeline de deploiement avant redemarrage applicatif.",
      ],
      parsingRecommendation:
        'Finaliser le parsing Discord pour reduire les messages non lisibles dans les rapports.',
      openProblemsRecommendation:
        'Mettre en place un suivi quotidien des problemes ouverts avec responsable assigne.',
      detectedHosts: 'Hosts detectes',
      detectedSeverities: 'Severites detectees',
      recentEvents: 'Evenements stockes recents',
      event: 'Evenement',
      host: 'Host',
      severity: 'Severite',
      status: 'Statut',
      links: 'Liens',
      received: 'Recu',
      notDetected: 'Non detecte',
      unknown: 'inconnu',
      noLink: 'Aucun lien',
      rawStored:
        'Message Discord brut stocke, champs lisibles non encore detectes.',
      noEvents: 'Aucun evenement Discord stocke sur cette periode.',
      reportUnavailable: 'Rapport hebdomadaire indisponible',
      syncFailed: 'Echec de la synchronisation Discord',
    },
  },
} as const;

type I18nContextValue = {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (typeof translations)[Language];
};

const I18nContext = createContext<I18nContextValue | null>(null);

function initialLanguage(): Language {
  const storedLanguage = window.localStorage.getItem(STORAGE_KEY);
  return storedLanguage === 'fr' || storedLanguage === 'en' ? storedLanguage : 'en';
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(initialLanguage);

  const value = useMemo<I18nContextValue>(() => {
    function setLanguage(nextLanguage: Language) {
      window.localStorage.setItem(STORAGE_KEY, nextLanguage);
      setLanguageState(nextLanguage);
    }

    return {
      language,
      setLanguage,
      t: translations[language],
    };
  }, [language]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}
