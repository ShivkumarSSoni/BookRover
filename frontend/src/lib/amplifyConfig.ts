/**
 * Amplify configuration — initialises aws-amplify with the Cognito User Pool
 * settings from build-time environment variables.
 *
 * Call configureAmplify() once at app startup (in main.tsx) before any
 * Amplify auth calls are made. In mock mode this is a no-op.
 */

import { Amplify } from 'aws-amplify';

export function configureAmplify(): void {
  if (import.meta.env.VITE_AUTH_MODE !== 'cognito') return;

  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
        userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
      },
    },
  });
}
