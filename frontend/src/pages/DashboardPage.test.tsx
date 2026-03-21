/**
 * Tests for DashboardPage — Group Leader Dashboard UI behaviours.
 *
 * Mocks: useDashboard hook, GroupLeaderContext, NavBar, react-router-dom.
 * Covers: loading state, error state, redirect when no groupLeaderId,
 *         header with GL name + bookstore, summary cards, sellers table,
 *         totals row, empty state, sort toggle, bookstore Change buttons.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import DashboardPage from '../pages/DashboardPage';
import { BookRover } from '../types';

// ─── Mocks ───────────────────────────────────────────────────────────────────

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('../components/NavBar', () => ({
  default: ({ role }: { role: string }) => <nav data-testid="navbar" data-role={role} />,
}));

const mockUseGroupLeader = vi.fn();

vi.mock('../context/GroupLeaderContext', () => ({
  useGroupLeader: () => mockUseGroupLeader(),
}));

const mockUseDashboard = vi.fn();

vi.mock('../hooks/useDashboard', () => ({
  useDashboard: (...args: unknown[]) => mockUseDashboard(...args),
}));

// ─── Fixtures ─────────────────────────────────────────────────────────────────

const GL_ID = 'gl-123';

const BOOKSTORE_A: BookRover.BookStoreSummary = {
  bookstore_id: 'bs-1',
  store_name: 'Sri Lakshmi Books',
};

const BOOKSTORE_B: BookRover.BookStoreSummary = {
  bookstore_id: 'bs-2',
  store_name: 'Kavitha Stores',
};

const SELLER_ROW_A: BookRover.DashboardSellerRow = {
  seller_id: 'sel-1',
  full_name: 'Anand Raj',
  total_books_sold: 25,
  total_amount_collected: 1875.0,
};

const SELLER_ROW_B: BookRover.DashboardSellerRow = {
  seller_id: 'sel-2',
  full_name: 'Priya Kumar',
  total_books_sold: 18,
  total_amount_collected: 1350.0,
};

const DASHBOARD_DATA: BookRover.DashboardResponse = {
  group_leader: { group_leader_id: GL_ID, name: 'Ravi Kumar' },
  bookstore: { bookstore_id: 'bs-1', store_name: 'Sri Lakshmi Books' },
  sellers: [SELLER_ROW_A, SELLER_ROW_B],
  totals: { total_books_sold: 43, total_amount_collected: 3225.0 },
};

const mockToggleSort = vi.fn();
const mockSelectBookstore = vi.fn();

const DEFAULT_DASHBOARD_STATE = {
  dashboard: DASHBOARD_DATA,
  bookstores: [BOOKSTORE_A],
  selectedBookstoreId: 'bs-1',
  isLoading: false,
  error: null,
  sortBy: 'total_amount_collected' as BookRover.DashboardSortBy,
  sortOrder: 'desc' as BookRover.DashboardSortOrder,
  selectBookstore: mockSelectBookstore,
  toggleSort: mockToggleSort,
};

function renderPage() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  );
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseGroupLeader.mockReturnValue({ groupLeaderId: GL_ID });
    mockUseDashboard.mockReturnValue(DEFAULT_DASHBOARD_STATE);
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  // ── Auth guard ─────────────────────────────────────────────────────────────

  it('redirects to /register when groupLeaderId is null', () => {
    mockUseGroupLeader.mockReturnValue({ groupLeaderId: null });
    renderPage();
    expect(mockNavigate).toHaveBeenCalledWith('/register', { replace: true });
  });

  it('does not redirect when groupLeaderId is present', () => {
    renderPage();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  // ── NavBar ─────────────────────────────────────────────────────────────────

  it('renders NavBar with group-leader role', () => {
    renderPage();
    const nav = screen.getByTestId('navbar');
    expect(nav).toBeInTheDocument();
    expect(nav).toHaveAttribute('data-role', 'group-leader');
  });

  // ── Header ─────────────────────────────────────────────────────────────────

  it('shows the group leader name in the header', () => {
    renderPage();
    expect(screen.getByText('Ravi Kumar')).toBeInTheDocument();
  });

  it('shows the active bookstore name', () => {
    renderPage();
    expect(screen.getByText('Sri Lakshmi Books')).toBeInTheDocument();
  });

  it('does not show Change buttons when there is only one bookstore', () => {
    renderPage();
    // When bookstores.length === 1, only one store_name text appears in header (not as button)
    const buttons = screen.queryAllByRole('button');
    // No bookstore-switch buttons (only no other buttons should exist in this case)
    expect(buttons.filter((b) => b.textContent === 'Sri Lakshmi Books')).toHaveLength(0);
  });

  it('shows bookstore selector buttons when there are multiple bookstores', () => {
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      bookstores: [BOOKSTORE_A, BOOKSTORE_B],
    });
    renderPage();
    expect(screen.getByRole('button', { name: 'Sri Lakshmi Books' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Kavitha Stores' })).toBeInTheDocument();
  });

  it('calls selectBookstore when a bookstore button is clicked', async () => {
    const user = userEvent.setup();
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      bookstores: [BOOKSTORE_A, BOOKSTORE_B],
    });
    renderPage();
    await user.click(screen.getByRole('button', { name: 'Kavitha Stores' }));
    expect(mockSelectBookstore).toHaveBeenCalledWith('bs-2');
  });

  // ── Summary cards ──────────────────────────────────────────────────────────

  it('displays total sellers count in summary card', () => {
    renderPage();
    expect(screen.getByText('Total Sellers')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('displays total amount collected in summary card', () => {
    renderPage();
    expect(screen.getByText('Total Collected')).toBeInTheDocument();
    // ₹3225.00 appears in both the summary card and the totals row
    expect(screen.getAllByText('₹3225.00')).toHaveLength(2);
  });

  // ── Sellers table ──────────────────────────────────────────────────────────

  it('renders a row for each seller', () => {
    renderPage();
    expect(screen.getByText('Anand Raj')).toBeInTheDocument();
    expect(screen.getByText('Priya Kumar')).toBeInTheDocument();
  });

  it('displays books sold and money collected for each seller', () => {
    renderPage();
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('₹1875.00')).toBeInTheDocument();
    expect(screen.getByText('18')).toBeInTheDocument();
    expect(screen.getByText('₹1350.00')).toBeInTheDocument();
  });

  it('renders the totals row at the bottom', () => {
    renderPage();
    expect(screen.getByText('Total')).toBeInTheDocument();
    expect(screen.getByText('43')).toBeInTheDocument();
    // Total amount shown in both summary card and totals row
    expect(screen.getAllByText('₹3225.00')).toHaveLength(2);
  });

  // ── Sort header ────────────────────────────────────────────────────────────

  it('shows column headers for sorting', () => {
    renderPage();
    expect(screen.getByText(/Books Sold/i)).toBeInTheDocument();
    expect(screen.getByText(/Money Collected/i)).toBeInTheDocument();
  });

  it('calls toggleSort with total_books_sold when Books Sold header is clicked', async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByText(/Books Sold/i));
    expect(mockToggleSort).toHaveBeenCalledWith('total_books_sold');
  });

  it('calls toggleSort with total_amount_collected when Money Collected header is clicked', async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByText(/Money Collected/i));
    expect(mockToggleSort).toHaveBeenCalledWith('total_amount_collected');
  });

  it('shows ↓ indicator on the active sort column when sort order is desc', () => {
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      sortBy: 'total_amount_collected',
      sortOrder: 'desc',
    });
    renderPage();
    expect(screen.getByText(/Money Collected ↓/)).toBeInTheDocument();
  });

  it('shows ↑ indicator on the active sort column when sort order is asc', () => {
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      sortBy: 'total_books_sold',
      sortOrder: 'asc',
    });
    renderPage();
    expect(screen.getByText(/Books Sold ↑/)).toBeInTheDocument();
  });

  it('does not show sort indicator on inactive column', () => {
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      sortBy: 'total_books_sold',
      sortOrder: 'asc',
    });
    renderPage();
    // Money Collected header should not have arrow
    const moneyHeader = screen.getByText(/Money Collected/);
    expect(moneyHeader.textContent).toBe('Money Collected');
  });

  // ── Empty state ────────────────────────────────────────────────────────────

  it('shows empty state message when there are no sellers', () => {
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      dashboard: {
        ...DASHBOARD_DATA,
        sellers: [],
        totals: { total_books_sold: 0, total_amount_collected: 0 },
      },
    });
    renderPage();
    expect(screen.getByText('No sellers registered under you yet.')).toBeInTheDocument();
  });

  it('shows 0 as total sellers count in empty state', () => {
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      dashboard: {
        ...DASHBOARD_DATA,
        sellers: [],
        totals: { total_books_sold: 0, total_amount_collected: 0 },
      },
    });
    renderPage();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  // ── Loading state ──────────────────────────────────────────────────────────

  it('shows loading message while dashboard is loading', () => {
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      dashboard: null,
      isLoading: true,
    });
    renderPage();
    expect(screen.getByText('Loading dashboard…')).toBeInTheDocument();
  });

  it('does not render sellers table while loading', () => {
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      dashboard: null,
      isLoading: true,
    });
    renderPage();
    expect(screen.queryByText('Anand Raj')).not.toBeInTheDocument();
  });

  // ── Error state ────────────────────────────────────────────────────────────

  it('shows error banner when error is present', () => {
    mockUseDashboard.mockReturnValue({
      ...DEFAULT_DASHBOARD_STATE,
      error: 'Failed to load dashboard. Please try again.',
    });
    renderPage();
    expect(screen.getByText('Failed to load dashboard. Please try again.')).toBeInTheDocument();
  });
});
