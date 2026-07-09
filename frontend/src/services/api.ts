import axios from 'axios';

export type ConnectorStatus = {
  name: string;
  enabled: boolean;
  connected: boolean;
};

export type ConnectorCatalogItem = {
  source: string;
  name: string;
  category: string;
  implemented: boolean;
  default_enabled: boolean;
  description: string;
};

export type ConnectorCatalog = {
  event_source: string;
  items: ConnectorCatalogItem[];
};

export type EventModelField = {
  name: string;
  data_type: string;
  required: boolean;
  description: string;
};

export type EventModel = {
  name: string;
  fields: EventModelField[];
};

export type ConnectorRuntime = {
  event_source: string;
  multiple_mode: boolean;
  enabled_sources: string[];
  disabled_sources: string[];
  dynamic_imports_configured: boolean;
};

export type ConnectorDiagnostic = {
  source: string;
  name: string;
  enabled: boolean;
  ready: boolean;
  missing_configuration: string[];
};

export type ConnectorConfigurationGuideItem = {
  source: string;
  name: string;
  env_vars: string[];
  env_template: string[];
  apply_commands: string[];
  restart_required: boolean;
  note: string;
};

export type WeeklyDiscordReportStatus = {
  feature: string;
  implemented: boolean;
  visible_in_ui: boolean;
  reason: string;
  required_before_available: string[];
};

export type WeeklyDiscordReportPushResult = {
  delivered: boolean;
  channel_id: string;
  message_id: string | null;
  filename: string;
};

export type WeeklyDiscordReportMetric = {
  label: string;
  value: number;
};

export type WeeklyDiscordReportEvent = {
  problem_id: string | null;
  title: string;
  host: string | null;
  severity: string | null;
  status: string | null;
  problem_name: string | null;
  started_at: string | null;
  details_available: boolean;
  operational_data: string | null;
  links: string[];
};

export type WeeklyDiscordOpenProblem = {
  problem_id: string | null;
  title: string;
  host: string | null;
  severity: string | null;
  status: string | null;
  started_at: string | null;
  age_seconds: number | null;
  age_label: string;
  operational_data: string | null;
  links: string[];
  recommended_action: string;
};

export type WeeklyDiscordReportDataQuality = {
  unnamed_events: number;
  unknown_severity_events: number;
  unknown_host_events: number;
  warnings: string[];
};

export type WeeklyDiscordReportDailyTrend = {
  date: string;
  total: number;
  problem: number;
  resolved: number;
};

export type WeeklyDiscordReport = {
  source: string;
  period_start: string;
  period_end: string;
  total_events: number;
  open_events: number;
  resolved_events: number;
  data_quality: WeeklyDiscordReportDataQuality;
  by_severity: WeeklyDiscordReportMetric[];
  by_host: WeeklyDiscordReportMetric[];
  daily_trend: WeeklyDiscordReportDailyTrend[];
  open_problems: WeeklyDiscordOpenProblem[];
  recent_events: WeeklyDiscordReportEvent[];
};

export type EventSyncResult = {
  received: number;
  created: number;
  updated: number;
};

export type EventSummaryMetric = {
  label: string;
  value: number;
};

export type EventSummary = {
  total_events: number;
  open_events: number;
  resolved_events: number;
  unparsed_events: number;
  last_event_at: string | null;
  by_source: EventSummaryMetric[];
  by_status: EventSummaryMetric[];
  by_severity: EventSummaryMetric[];
};

export type AlertEvent = {
  id: string;
  source: string;
  problem_id: string | null;
  host: string | null;
  severity: string | null;
  status: string | null;
  problem_name: string | null;
  started_at: string | null;
  resolved_at: string | null;
  duration: number | null;
  raw_payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type EventList = {
  items: AlertEvent[];
  total: number;
  limit: number;
  offset: number;
};

export type EventFilters = {
  source?: string;
  status?: string;
  severity?: string;
  q?: string;
  limit?: number;
  offset?: number;
  include_unparsed?: boolean;
};

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function getConnectorStatuses(): Promise<ConnectorStatus[]> {
  const response = await apiClient.get<ConnectorStatus[]>('/connectors');
  return response.data;
}

export async function getConnectorCatalog(): Promise<ConnectorCatalog> {
  const response = await apiClient.get<ConnectorCatalog>('/connectors/catalog');
  return response.data;
}

export async function getConnectorEventModel(): Promise<EventModel> {
  const response = await apiClient.get<EventModel>('/connectors/event-model');
  return response.data;
}

export async function getConnectorRuntime(): Promise<ConnectorRuntime> {
  const response = await apiClient.get<ConnectorRuntime>('/connectors/runtime');
  return response.data;
}

export async function getConnectorDiagnostics(): Promise<ConnectorDiagnostic[]> {
  const response = await apiClient.get<ConnectorDiagnostic[]>('/connectors/diagnostics');
  return response.data;
}

export async function getConnectorConfigurationGuide(): Promise<ConnectorConfigurationGuideItem[]> {
  const response = await apiClient.get<ConnectorConfigurationGuideItem[]>(
    '/connectors/configuration-guide',
  );
  return response.data;
}

export async function getWeeklyDiscordReportStatus(): Promise<WeeklyDiscordReportStatus> {
  const response = await apiClient.get<WeeklyDiscordReportStatus>('/reports/weekly-discord/status');
  return response.data;
}

export async function getWeeklyDiscordReport(): Promise<WeeklyDiscordReport> {
  const response = await apiClient.get<WeeklyDiscordReport>('/reports/weekly-discord');
  return response.data;
}

export async function pushWeeklyDiscordReportToDiscord(): Promise<WeeklyDiscordReportPushResult> {
  const response = await apiClient.post<WeeklyDiscordReportPushResult>(
    '/reports/weekly-discord/push-discord',
  );
  return response.data;
}

export async function syncEvents(): Promise<EventSyncResult> {
  const response = await apiClient.post<EventSyncResult>('/events/sync');
  return response.data;
}

export async function getEventSummary(): Promise<EventSummary> {
  const response = await apiClient.get<EventSummary>('/events/summary');
  return response.data;
}

export async function getEvents(filters: EventFilters = {}): Promise<EventList> {
  const response = await apiClient.get<EventList>('/events', { params: filters });
  return response.data;
}
