/**
 * App — root component with React Router.
 *
 * Defines all client-side routes. Current routes:
 * - /admin → AdminPage (Admin feature)
 * - /register → RegisterPage (Seller Registration)
 * - /inventory → InventoryPage (Seller Inventory)
 * - * redirect to /admin for dev convenience
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AdminPage from './pages/AdminPage';
import RegisterPage from './pages/RegisterPage';
import InventoryPage from './pages/InventoryPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        {/* Redirect root to /admin during dev (will be replaced with /login in Phase 6) */}
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
