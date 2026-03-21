/**
 * App — root component with React Router.
 *
 * Defines all client-side routes. Current routes:
 * - /admin → AdminPage (Admin feature)
 * - /register → RegisterPage (Seller Registration)
 * - /inventory → InventoryPage (Seller Inventory)
 * - /new-buyer → NewBuyerPage (Record a Sale)
 * - /dashboard → DashboardPage (Group Leader Dashboard)
 * - * → redirect to /register (new users start here)
 *
 * Seller routes are wrapped in SellerProvider so all seller pages
 * share one fetched seller profile without repeated API calls.
 *
 * The /dashboard route is wrapped in GroupLeaderProvider (reads GL identity
 * from localStorage) and SellerProvider (NavBar internally calls useSeller()).
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SellerProvider } from './context/SellerContext';
import { GroupLeaderProvider } from './context/GroupLeaderContext';
import AdminPage from './pages/AdminPage';
import RegisterPage from './pages/RegisterPage';
import InventoryPage from './pages/InventoryPage';
import NewBuyerPage from './pages/NewBuyerPage';
import DashboardPage from './pages/DashboardPage';

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
        <Route
          path="/new-buyer"
          element={
            <SellerProvider>
              <NewBuyerPage />
            </SellerProvider>
          }
        />

        {/* Group Leader Dashboard — GroupLeaderProvider reads GL identity from localStorage.
            SellerProvider is required because NavBar calls useSeller() internally. */}
        <Route
          path="/dashboard"
          element={
            <GroupLeaderProvider>
              <SellerProvider>
                <DashboardPage />
              </SellerProvider>
            </GroupLeaderProvider>
          }
        />

        {/* Redirect root and unknown paths to /register */}
        <Route path="*" element={<Navigate to="/register" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
