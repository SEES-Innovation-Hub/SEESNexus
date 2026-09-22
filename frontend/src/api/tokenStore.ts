const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

// Some browsers block storage entirely (strict privacy settings) and throw on
// every access. Falling back to memory keeps the app running: the session then
// lasts until the tab is closed instead of the whole app failing to render.
const memory = new Map<string, string>();

function read(key: string): string | null {
  try {
    return localStorage.getItem(key) ?? memory.get(key) ?? null;
  } catch {
    return memory.get(key) ?? null;
  }
}

function write(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    memory.set(key, value);
  }
}

function erase(key: string) {
  memory.delete(key);
  try {
    localStorage.removeItem(key);
  } catch {
    // Storage is blocked, so there was nothing stored to remove.
  }
}

// The one place that knows how the session tokens are persisted.
export const tokenStore = {
  getAccess: () => read(ACCESS_KEY),
  getRefresh: () => read(REFRESH_KEY),
  setAccess: (token: string) => write(ACCESS_KEY, token),
  setBoth: (access: string, refresh: string) => {
    write(ACCESS_KEY, access);
    write(REFRESH_KEY, refresh);
  },
  clear: () => {
    erase(ACCESS_KEY);
    erase(REFRESH_KEY);
  },
};
