/**
 * NavBar — top navigation bar, shown on all pages except Login and Registration.
 *
 * Renders:
 * - "BookRover" logo/wordmark on the left.
 * - Seller's full name (from SellerContext) next to the logo on seller pages.
 * - Role-appropriate nav links on the right, with active-link highlighting.
 *
 * Role is determined by the `role` prop passed from App.tsx routing:
 *   "seller"       → Inventory | New Buyer | Return
 *   "admin"        → Admin
 *   "group-leader" → Dashboard
 *
 * Active link is detected via React Router's useLocation().
 */

import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSeller } from '../context/SellerContext';

// ─── Types ────────────────────────────────────────────────────────────────────

export type NavBarRole = 'seller' | 'admin' | 'group-leader';

interface NavBarProps {
  role: NavBarRole;
}

// ─── Nav link definitions ─────────────────────────────────────────────────────

const SELLER_LINKS = [
  { label: 'Inventory', to: '/inventory' },
  { label: 'New Buyer', to: '/new-buyer' },
  { label: 'Return', to: '/return' },
];

const ADMIN_LINKS = [{ label: 'Admin', to: '/admin' }];

const GROUP_LEADER_LINKS = [{ label: 'Dashboard', to: '/dashboard' }];

// ─── Component ────────────────────────────────────────────────────────────────

export default function NavBar({ role }: NavBarProps) {
  const { logout } = useAuth();
  const { seller } = useSeller();

  let links;
  if (role === 'seller') links = SELLER_LINKS;
  else if (role === 'group-leader') links = GROUP_LEADER_LINKS;
  else links = ADMIN_LINKS;

  const sellerName =
    role === 'seller' && seller
      ? `${seller.first_name} ${seller.last_name}`
      : null;

  return (
    <nav className="fixed top-0 inset-x-0 z-20 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        {/* Left: logo + seller name */}
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-lg font-brand font-semibold text-blue-600 flex-shrink-0">BookRover</span>
          {sellerName && (
            <span className="text-sm font-medium text-gray-700 truncate">{sellerName}</span>
          )}
        </div>

        {/* Right: nav links + logout */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {links.map(({ label, to }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                [
                  'min-h-[44px] px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                ].join(' ')
              }
            >
              {label}
            </NavLink>
          ))}
          <button
            onClick={logout}
            className="min-h-[44px] px-3 py-2 rounded-lg text-sm font-medium text-gray-500 hover:bg-red-50 hover:text-red-600 transition-colors ml-1"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
