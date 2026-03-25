/**
 * Unit tests for Cognito auth functions in authService.
 *
 * cognitoSignIn():
 *   - Calls signUp() first for a new user email.
 *   - Falls back to signIn() with EMAIL_OTP when UsernameExistsException is thrown.
 *   - Propagates unexpected errors from signUp() without calling signIn().
 *
 * cognitoConfirmSignIn():
 *   - Calls confirmSignUp() + autoSignIn() when completing a new user sign-up.
 *   - Calls confirmSignIn() when completing a returning user sign-in.
 *
 * aws-amplify/auth is fully mocked — no real Cognito calls are made.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock aws-amplify/auth before importing authService so the module uses the mock.
vi.mock('aws-amplify/auth', () => ({
  signIn: vi.fn(),
  signUp: vi.fn(),
  confirmSignIn: vi.fn(),
  confirmSignUp: vi.fn(),
  autoSignIn: vi.fn(),
  signOut: vi.fn(),
}));

// Mock apiClient to prevent axios instance creation warnings in test output.
vi.mock('./apiClient', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

import { cognitoSignIn, cognitoConfirmSignIn } from './authService';
import { signIn, signUp, confirmSignIn, confirmSignUp, autoSignIn } from 'aws-amplify/auth';

const mockSignIn = vi.mocked(signIn);
const mockSignUp = vi.mocked(signUp);
const mockConfirmSignIn = vi.mocked(confirmSignIn);
const mockConfirmSignUp = vi.mocked(confirmSignUp);
const mockAutoSignIn = vi.mocked(autoSignIn);

// ─── Helpers ─────────────────────────────────────────────────────────────────

function usernameExistsError(): Error {
  return Object.assign(new Error('User already exists'), { name: 'UsernameExistsException' });
}

const SIGN_UP_SUCCESS = {
  isSignUpComplete: false,
  nextStep: { signUpStep: 'CONFIRM_SIGN_UP' as const, codeDeliveryDetails: {} as never },
  userId: 'uid-001',
};

const CONFIRM_SIGN_UP_SUCCESS = {
  isSignUpComplete: true,
  nextStep: { signUpStep: 'COMPLETE_AUTO_SIGN_IN' as const },
};

const AUTO_SIGN_IN_SUCCESS = {
  isSignedIn: true,
  nextStep: { signInStep: 'DONE' as const },
};

const SIGN_IN_OTP_PENDING = {
  isSignedIn: false,
  nextStep: { signInStep: 'CONFIRM_SIGN_IN_WITH_EMAIL_CODE' as const, codeDeliveryDetails: {} as never },
};

const CONFIRM_SIGN_IN_SUCCESS = {
  isSignedIn: true,
  nextStep: { signInStep: 'DONE' as const },
};

// ─── cognitoSignIn ────────────────────────────────────────────────────────────

describe('cognitoSignIn', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls signUp with the email address for a new user', async () => {
    mockSignUp.mockResolvedValue(SIGN_UP_SUCCESS as never);
    await cognitoSignIn('new@example.com');
    expect(mockSignUp).toHaveBeenCalledWith(
      expect.objectContaining({ username: 'new@example.com' }),
    );
    expect(mockSignIn).not.toHaveBeenCalled();
  });

  it('includes autoSignIn:true in signUp options', async () => {
    mockSignUp.mockResolvedValue(SIGN_UP_SUCCESS as never);
    await cognitoSignIn('new@example.com');
    expect(mockSignUp).toHaveBeenCalledWith(
      expect.objectContaining({ options: expect.objectContaining({ autoSignIn: true }) }),
    );
  });

  it('includes email as a user attribute in signUp', async () => {
    mockSignUp.mockResolvedValue(SIGN_UP_SUCCESS as never);
    await cognitoSignIn('new@example.com');
    expect(mockSignUp).toHaveBeenCalledWith(
      expect.objectContaining({
        options: expect.objectContaining({
          userAttributes: expect.objectContaining({ email: 'new@example.com' }),
        }),
      }),
    );
  });

  it('does not expose a predictable password in signUp', async () => {
    mockSignUp.mockResolvedValue(SIGN_UP_SUCCESS as never);
    await cognitoSignIn('new@example.com');
    const call = mockSignUp.mock.calls[0][0] as { password: string };
    expect(call.password).toBeTruthy();
    expect(call.password.length).toBeGreaterThanOrEqual(8);
  });

  it('falls back to signIn with EMAIL_OTP when the user already exists', async () => {
    mockSignUp.mockRejectedValue(usernameExistsError());
    mockSignIn.mockResolvedValue(SIGN_IN_OTP_PENDING as never);

    await cognitoSignIn('existing@example.com');

    expect(mockSignIn).toHaveBeenCalledWith(
      expect.objectContaining({
        username: 'existing@example.com',
        options: expect.objectContaining({
          authFlowType: 'USER_AUTH',
          preferredChallenge: 'EMAIL_OTP',
        }),
      }),
    );
  });

  it('does not call signIn when signUp succeeds (new user)', async () => {
    mockSignUp.mockResolvedValue(SIGN_UP_SUCCESS as never);
    await cognitoSignIn('new@example.com');
    expect(mockSignIn).not.toHaveBeenCalled();
  });

  it('propagates unexpected errors from signUp without calling signIn', async () => {
    const networkError = Object.assign(new Error('Network failure'), { name: 'NetworkError' });
    mockSignUp.mockRejectedValue(networkError);

    await expect(cognitoSignIn('bad@example.com')).rejects.toThrow('Network failure');
    expect(mockSignIn).not.toHaveBeenCalled();
  });
});

// ─── cognitoConfirmSignIn — new user (sign-up) path ──────────────────────────

describe('cognitoConfirmSignIn — new user path', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    // Set up the sign-up path by calling cognitoSignIn first.
    mockSignUp.mockResolvedValue(SIGN_UP_SUCCESS as never);
    await cognitoSignIn('new@example.com');
    vi.clearAllMocks(); // clear signUp call count so assertions are clean
  });

  it('calls confirmSignUp with the username and OTP code', async () => {
    mockConfirmSignUp.mockResolvedValue(CONFIRM_SIGN_UP_SUCCESS as never);
    mockAutoSignIn.mockResolvedValue(AUTO_SIGN_IN_SUCCESS as never);

    await cognitoConfirmSignIn('12345678');

    expect(mockConfirmSignUp).toHaveBeenCalledWith({
      username: 'new@example.com',
      confirmationCode: '12345678',
    });
  });

  it('calls autoSignIn after confirmSignUp succeeds', async () => {
    mockConfirmSignUp.mockResolvedValue(CONFIRM_SIGN_UP_SUCCESS as never);
    mockAutoSignIn.mockResolvedValue(AUTO_SIGN_IN_SUCCESS as never);

    await cognitoConfirmSignIn('12345678');

    expect(mockAutoSignIn).toHaveBeenCalled();
  });

  it('does not call confirmSignIn on the new user path', async () => {
    mockConfirmSignUp.mockResolvedValue(CONFIRM_SIGN_UP_SUCCESS as never);
    mockAutoSignIn.mockResolvedValue(AUTO_SIGN_IN_SUCCESS as never);

    await cognitoConfirmSignIn('12345678');

    expect(mockConfirmSignIn).not.toHaveBeenCalled();
  });

  it('propagates errors from confirmSignUp', async () => {
    mockConfirmSignUp.mockRejectedValue(new Error('CodeMismatchException'));

    await expect(cognitoConfirmSignIn('00000000')).rejects.toThrow('CodeMismatchException');
    expect(mockAutoSignIn).not.toHaveBeenCalled();
  });
});

// ─── cognitoConfirmSignIn — returning user (sign-in) path ────────────────────

describe('cognitoConfirmSignIn — returning user path', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    // Set up the sign-in path by calling cognitoSignIn with an existing user.
    mockSignUp.mockRejectedValue(usernameExistsError());
    mockSignIn.mockResolvedValue(SIGN_IN_OTP_PENDING as never);
    await cognitoSignIn('existing@example.com');
    vi.clearAllMocks(); // clear call counts so assertions are clean
  });

  it('calls confirmSignIn with the OTP code', async () => {
    mockConfirmSignIn.mockResolvedValue(CONFIRM_SIGN_IN_SUCCESS as never);

    await cognitoConfirmSignIn('87654321');

    expect(mockConfirmSignIn).toHaveBeenCalledWith({ challengeResponse: '87654321' });
  });

  it('does not call confirmSignUp or autoSignIn on the returning user path', async () => {
    mockConfirmSignIn.mockResolvedValue(CONFIRM_SIGN_IN_SUCCESS as never);

    await cognitoConfirmSignIn('87654321');

    expect(mockConfirmSignUp).not.toHaveBeenCalled();
    expect(mockAutoSignIn).not.toHaveBeenCalled();
  });

  it('propagates errors from confirmSignIn', async () => {
    mockConfirmSignIn.mockRejectedValue(new Error('CodeMismatchException'));

    await expect(cognitoConfirmSignIn('00000000')).rejects.toThrow('CodeMismatchException');
  });
});
