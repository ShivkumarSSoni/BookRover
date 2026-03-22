/**
 * App — root component with React Router and AuthProvider.
 *
 * All routes are wrapped in AuthProvider (single source of truth for identity).
 * Protected routes are wrapped in RequireRole which redirects unauthenticated
 * users to /login and users with the wrong role to the appropriate page.
 *
 * Routes:
 * - /login    → LoginPage      — public entry point
 * - /register → RegisterPage   — requires auth (new user, no role yet)
 * - /admin    → AdminPage      — requires 'admin' role
 * - /inventory → InventoryPage — requires 'seller' role
 * - /new-buyer → NewBuyerPage  — requires 'seller' role
 * - /return   → ReturnPage     — requires 'seller' role
 * - /dashboard → DashboardPage — requires 'group_leader' role
 * - *         → redirect to /login
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { SellerProvider } from './context/SellerContext';
import { GroupLeaderProvider } from './context/GroupLeaderContext';
import RequireRole from './components/RequireRole';
import LoginPage from './pages/LoginPage';
import AdminPage from './pages/AdminPage';
import RegisterPage from './pages/RegisterPage';
import InventoryPage from './pages/InventoryPage';
import NewBuyerPage from './pages/NewBuyerPage';
import ReturnPage from './pages/ReturnPage';
import DashboardPage from './pages/DashboardPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />

          {/* Registration — requires auth token (any role, including no role) */}
          <Route path="/register" element={<RegisterPage />} />

          {/* Admin */}
          <Route
            path="/admin"
            element={
              <RequireRole role="admin">
                <AdminPage />
              </RequireRole>
            }
          />

          {/* Seller pages — all share one SellerProvider */}
          <Route
            path="/inventory"
            element={
              <RequireRole role="seller">
                <SellerProvider>
                  <InventoryPage />
                </SellerProvider>
              </RequireRole>
            }
          />
          <Route
            path="/new-buyer"
            element={
              <RequireRole role="seller">
                <SellerProvider>
                  <NewBuyerPage />
                </SellerProvider>
              </RequireRole>
            }
          />
          <Route
            path="/return"
            element={
              <RequireRole role="seller">
                <SellerProvider>
                  <ReturnPage />
                </SellerProvider>
              </RequireRole>
            }
          />

          {/* Group Leader Dashboard.
              SellerProvider is required because NavBar calls useSeller() internally. */}
          <Route
            path="/dashboard"
            element={
              <RequireRole role="group_leader">
                <GroupLeaderProvider>
                  <SellerProvider>
                    <DashboardPage />
                  </SellerProvider>
                </GroupLeaderProvider>
              </RequireRole>
            }
          />

          {/* Catch-all → /login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

