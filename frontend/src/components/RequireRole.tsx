/**
 * RequireRole — route guard that enforces a BookRover role.
 *
 * Behaviour:
 * - While auth is loading: render nothing (avoid flash).
 * - Not authenticated (no me): redirect to /login.
 * - Authenticated but wrong role:
 *     roles is empty → redirect to /register (new user, needs to sign up).
 *     roles is non-empty but doesn't include required role → redirect to /login
 *       (user is logged in but accessing a page they are not authorized for).
 * - Authenticated with correct role: render children.
 *
 * Usage:
 *   <RequireRole role="seller">
 *     <InventoryPage />
 *   </RequireRole>
 */

import { useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookRover } from '../types';

interface RequireRoleProps {
  role: BookRover.Role;
  children: ReactNode;
}

export default function RequireRole({ role, children }: RequireRoleProps) {
  const { me, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isLoading) return;
    if (!me) {
      navigate('/login', { replace: true });
      return;
    }
    if (!me.roles.includes(role)) {
      const destination = me.roles.length === 0 ? '/register' : '/login';
      navigate(destination, { replace: true });
    }
  }, [me, isLoading, role, navigate]);

  if (isLoading) return null;
  if (!me || !me.roles.includes(role)) return null;

  return <>{children}</>;
}
