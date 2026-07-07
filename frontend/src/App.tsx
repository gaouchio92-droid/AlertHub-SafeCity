import { Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from './components/layout/AppLayout';
import { I18nProvider } from './i18n/I18nProvider';
import { ConnectorsPage } from './pages/ConnectorsPage';
import { EventsPage } from './pages/EventsPage';
import { HomePage } from './pages/HomePage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

export default function App() {
  return (
    <I18nProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/event-sources" element={<ConnectorsPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </I18nProvider>
  );
}
