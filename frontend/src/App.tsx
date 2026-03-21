/**
 * App — root component with React Router.
 *
 * Defines all client-side routes. The dev placeholder routes:
 * - /admin → AdminPage (Admin feature — Phase 2/3 current focus)
 * - * redirect to /admin for dev convenience
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AdminPage from './pages/AdminPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/admin" element={<AdminPage />} />
        {/* Redirect root to /admin during dev (will be replaced with /login in Phase 6) */}
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
