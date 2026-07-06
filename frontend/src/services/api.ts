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
