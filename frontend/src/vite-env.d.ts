/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  /** 'mock' enables the dev login form. 'cognito' uses AWS Cognito (production). */
  readonly VITE_AUTH_MODE: 'mock' | 'cognito';
  /** Cognito User Pool ID — required when VITE_AUTH_MODE=cognito. e.g. ap-south-1_XXXXXXX */
  readonly VITE_COGNITO_USER_POOL_ID: string;
  /** Cognito App Client ID — required when VITE_AUTH_MODE=cognito. */
  readonly VITE_COGNITO_CLIENT_ID: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
