/**
 * Tests for GroupLeadersTab — render, add, delete interactions.
 *
 * All API calls are mocked through the useGroupLeaders hook mock.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import GroupLeadersTab from '../pages/GroupLeadersTab';
import { BookRover } from '../types';

const MOCK_BOOKSTORE: BookRover.BookStore = {
  bookstore_id: 'bs-001',
  store_name: 'Sri Lakshmi Books',
  owner_name: 'Lakshmi Devi',
  address: '12 MG Road',
  phone_number: '+91',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const MOCK_GROUP_LEADER: BookRover.GroupLeader = {
  group_leader_id: 'gl-001',
  name: 'Ravi Kumar',
  email: 'ravi@gmail.com',
  bookstore_ids: ['bs-001'],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockAddGroupLeader = vi.fn();
const mockRemoveGroupLeader = vi.fn();
const mockEditGroupLeader = vi.fn();

vi.mock('../hooks/useGroupLeaders', () => ({
  useGroupLeaders: () => ({
    groupLeaders: [MOCK_GROUP_LEADER],
    isLoading: false,
    error: null,
    clearError: vi.fn(),
    addGroupLeader: mockAddGroupLeader,
    editGroupLeader: mockEditGroupLeader,
    removeGroupLeader: mockRemoveGroupLeader,
    refresh: vi.fn(),
  }),
}));

describe('GroupLeadersTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the group leader card', () => {
    render(<GroupLeadersTab bookstores={[MOCK_BOOKSTORE]} />);
    expect(screen.getByText('Ravi Kumar')).toBeInTheDocument();
    expect(screen.getByText('ravi@gmail.com')).toBeInTheDocument();
    expect(screen.getByText(/Sri Lakshmi Books/i)).toBeInTheDocument();
  });

  it('shows add form when "+ Add Group Leader" is clicked', async () => {
    const user = userEvent.setup();
    render(<GroupLeadersTab bookstores={[MOCK_BOOKSTORE]} />);

    await user.click(screen.getByText('+ Add Group Leader'));

    expect(screen.getByText('New Group Leader')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ravi Kumar')).toBeInTheDocument();
  });

  it('shows bookstore checkboxes in add form', async () => {
    const user = userEvent.setup();
    render(<GroupLeadersTab bookstores={[MOCK_BOOKSTORE]} />);

    await user.click(screen.getByText('+ Add Group Leader'));

    expect(screen.getByLabelText('Sri Lakshmi Books')).toBeInTheDocument();
  });

  it('Save button is disabled when no bookstore is selected', async () => {
    const user = userEvent.setup();
    render(<GroupLeadersTab bookstores={[MOCK_BOOKSTORE]} />);

    await user.click(screen.getByText('+ Add Group Leader'));
    await user.type(screen.getByPlaceholderText('Ravi Kumar'), 'Test Leader');
    await user.type(screen.getByPlaceholderText('ravi@gmail.com'), 'test@gmail.com');
    // do NOT check any bookstore

    expect(screen.getByRole('button', { name: /^save$/i })).toBeDisabled();
  });

  it('calls addGroupLeader with correct payload', async () => {
    const user = userEvent.setup();
    mockAddGroupLeader.mockResolvedValue(undefined);
    render(<GroupLeadersTab bookstores={[MOCK_BOOKSTORE]} />);

    await user.click(screen.getByText('+ Add Group Leader'));
    await user.type(screen.getByPlaceholderText('Ravi Kumar'), 'New Leader');
    await user.type(screen.getByPlaceholderText('ravi@gmail.com'), 'new@gmail.com');
    await user.click(screen.getByLabelText('Sri Lakshmi Books'));
    await user.click(screen.getByRole('button', { name: /^save$/i }));

    await waitFor(() => {
      expect(mockAddGroupLeader).toHaveBeenCalledWith({
        name: 'New Leader',
        email: 'new@gmail.com',
        bookstore_ids: ['bs-001'],
      });
    });
  });

  it('shows confirm dialog when Delete is clicked', async () => {
    const user = userEvent.setup();
    render(<GroupLeadersTab bookstores={[MOCK_BOOKSTORE]} />);

    await user.click(screen.getByRole('button', { name: /delete/i }));

    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('calls removeGroupLeader when deletion is confirmed', async () => {
    const user = userEvent.setup();
    mockRemoveGroupLeader.mockResolvedValue(undefined);
    render(<GroupLeadersTab bookstores={[MOCK_BOOKSTORE]} />);

    await user.click(screen.getByRole('button', { name: /delete/i }));
    await user.click(screen.getByRole('button', { name: /confirm/i }));

    await waitFor(() => {
      expect(mockRemoveGroupLeader).toHaveBeenCalledWith('gl-001');
    });
  });
});
