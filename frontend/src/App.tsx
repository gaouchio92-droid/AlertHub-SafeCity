import { Navigate, Route, Routes } from 'react-router-dom';

import { AuthProvider } from './auth/AuthProvider';
import { RequireAdmin } from './auth/RequireAdmin';
import { AppLayout } from './components/layout/AppLayout';
import { I18nProvider } from './i18n/I18nProvider';
import { ConnectorsPage } from './pages/ConnectorsPage';
import { EventsPage } from './pages/EventsPage';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

export default function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/home" replace />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/home" element={<HomePage />} />
            <Route
              path="/event-sources"
              element={(
                <RequireAdmin>
                  <ConnectorsPage />
                </RequireAdmin>
              )}
            />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route
              path="/settings"
              element={(
                <RequireAdmin>
                  <SettingsPage />
                </RequireAdmin>
              )}
            />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </I18nProvider>
  );
}
