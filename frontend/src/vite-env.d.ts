/// <reference types="vite/client" />

interface ImportMetaEnv {
  // The backend's origin for production builds (see src/api/client.ts).
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
