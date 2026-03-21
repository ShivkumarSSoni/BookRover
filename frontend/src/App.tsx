/**
 * App — root component with React Router.
 *
 * Defines all client-side routes. Current routes:
 * - /admin → AdminPage (Admin feature)
 * - /register → RegisterPage (Seller Registration)
 * - /inventory → InventoryPage (Seller Inventory)
 * - * → redirect to /register (new users start here)
 *
 * Seller routes are wrapped in SellerProvider so all seller pages
 * share one fetched seller profile without repeated API calls.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SellerProvider } from './context/SellerContext';
import AdminPage from './pages/AdminPage';
import RegisterPage from './pages/RegisterPage';
import InventoryPage from './pages/InventoryPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Admin — no SellerContext needed */}
        <Route path="/admin" element={<AdminPage />} />

        {/* Registration — no SellerContext yet (seller doesn't exist) */}
        <Route path="/register" element={<RegisterPage />} />

        {/* Seller pages — all share one SellerProvider */}
        <Route
          path="/inventory"
          element={
            <SellerProvider>
              <InventoryPage />
            </SellerProvider>
          }
        />

        {/* Redirect root and unknown paths to /register */}
        <Route path="*" element={<Navigate to="/register" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
