/**
 * Tests for NavBar component.
 *
 * Verifies: logo render, seller name display, nav links per role,
 * active link highlighting, and no seller name for admin role.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import NavBar from '../components/NavBar';
import { BookRover } from '../types';

// ─── Mocks ────────────────────────────────────────────────────────────────────

const mockUseSeller = vi.fn();
const mockLogout = vi.fn();

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ logout: mockLogout }),
}));

vi.mock('../context/SellerContext', () => ({
  useSeller: () => mockUseSeller(),
}));

const SELLER: BookRover.Seller = {
  seller_id: 'seller-1',
  first_name: 'Anand',
  last_name: 'Raj',
  email: 'anand@example.com',
  group_leader_id: 'gl-1',
  bookstore_id: 'bs-1',
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

function renderNavBar(role: 'seller' | 'admin', initialPath = '/inventory') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <NavBar role={role} />
    </MemoryRouter>,
  );
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('NavBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSeller.mockReturnValue({ seller: SELLER, isLoading: false });
  });

  it('renders the BookRover logo', () => {
    renderNavBar('seller');
    expect(screen.getByText('BookRover')).toBeInTheDocument();
  });

  it('shows seller full name when role is seller and seller is loaded', () => {
    renderNavBar('seller');
    expect(screen.getByText('Anand Raj')).toBeInTheDocument();
  });

  it('does not show seller name when seller is not yet loaded', () => {
    mockUseSeller.mockReturnValue({ seller: null, isLoading: true });
    renderNavBar('seller');
    expect(screen.queryByText('Anand Raj')).not.toBeInTheDocument();
  });

  it('renders seller nav links: Inventory, New Buyer, Return', () => {
    renderNavBar('seller');
    expect(screen.getByRole('link', { name: 'Inventory' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'New Buyer' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Return' })).toBeInTheDocument();
  });

  it('renders only the Admin link for admin role', () => {
    renderNavBar('admin', '/admin');
    expect(screen.getByRole('link', { name: 'Admin' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Inventory' })).not.toBeInTheDocument();
  });

  it('does not show seller name for admin role', () => {
    renderNavBar('admin', '/admin');
    expect(screen.queryByText('Anand Raj')).not.toBeInTheDocument();
  });

  it('applies active style to the current route link', () => {
    renderNavBar('seller', '/inventory');
    const inventoryLink = screen.getByRole('link', { name: 'Inventory' });
    expect(inventoryLink.className).toMatch(/bg-blue-50/);
    expect(inventoryLink.className).toMatch(/text-blue-700/);
  });

  it('does not apply active style to non-current route links', () => {
    renderNavBar('seller', '/inventory');
    const newBuyerLink = screen.getByRole('link', { name: 'New Buyer' });
    expect(newBuyerLink.className).not.toMatch(/bg-blue-50/);
  });

  it('renders a Logout button', () => {
    renderNavBar('seller');
    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  it('calls logout when the Logout button is clicked', async () => {
    const user = userEvent.setup();
    renderNavBar('seller');
    await user.click(screen.getByRole('button', { name: /logout/i }));
    expect(mockLogout).toHaveBeenCalledOnce();
  });
});
