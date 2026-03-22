/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  /** 'mock' enables the dev login form. 'cognito' uses AWS Cognito (production). */
  readonly VITE_AUTH_MODE: 'mock' | 'cognito';
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
