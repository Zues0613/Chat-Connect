// Cookie utility functions for client-side cookie management
// Safe for SSR - checks if document is available

export const getCookie = (name: string): string | null => {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
  return null;
};

export const setCookie = (name: string, value: string, days: number = 7): void => {
  if (typeof document === 'undefined') return;
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;secure;samesite=strict`;
};

export const deleteCookie = (name: string): void => {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
};

// Session management functions
const SESSION_DURATION_DAYS = 2; // 2 days session duration
const ACTIVITY_CHECK_INTERVAL = 5 * 60 * 1000; // Check activity every 5 minutes
const ACTIVITY_REFRESH_THRESHOLD = 30 * 60 * 1000; // Refresh if last activity > 30 minutes

// Get last activity timestamp
export const getLastActivity = (): number => {
  const timestamp = getCookie('lastActivity');
  return timestamp ? parseInt(timestamp) : 0;
};

// Update last activity timestamp
export const updateLastActivity = (): void => {
  const now = Date.now();
  setCookie('lastActivity', now.toString(), SESSION_DURATION_DAYS);
};

// Check if session is still valid based on activity
export const isSessionValid = (): boolean => {
  const token = getCookie('token');
  const lastActivity = getLastActivity();
  
  if (!token || !lastActivity) {
    return false;
  }
  
  const now = Date.now();
  const timeSinceActivity = now - lastActivity;
  const maxInactivity = SESSION_DURATION_DAYS * 24 * 60 * 60 * 1000; // 2 days in milliseconds
  
  return timeSinceActivity < maxInactivity;
};

// Refresh session if needed (extends expiry based on recent activity)
export const refreshSessionIfNeeded = (): boolean => {
  if (!isSessionValid()) {
    clearSession();
    return false;
  }
  
  const lastActivity = getLastActivity();
  const now = Date.now();
  const timeSinceActivity = now - lastActivity;
  
  // If last activity was more than 30 minutes ago, refresh the session
  if (timeSinceActivity > ACTIVITY_REFRESH_THRESHOLD) {
    const token = getCookie('token');
    if (token) {
      // Re-set the token cookie with fresh expiry
      setCookie('token', token, SESSION_DURATION_DAYS);
      updateLastActivity();
      console.log('[DEBUG] Session refreshed due to activity');
      return true;
    }
  }
  
  // Update activity regardless
  updateLastActivity();
  return true;
};

// Clear entire session
export const clearSession = (): void => {
  deleteCookie('token');
  deleteCookie('lastActivity');
  console.log('[DEBUG] Session cleared');
};

// Auth-specific helpers with session management
export const getAuthToken = (): string | null => {
  if (!isSessionValid()) {
    clearSession();
    return null;
  }
  return getCookie('token');
};

export const setAuthToken = (token: string): void => {
  setCookie('token', token, SESSION_DURATION_DAYS);
  updateLastActivity();
  console.log('[DEBUG] New session started');
};

export const clearAuthToken = (): void => clearSession();

// Activity tracker - call this on user interactions
export const trackUserActivity = (): void => {
  if (getCookie('token')) {
    updateLastActivity();
  }
};

// Auto-refresh session - call this periodically in your app
export const autoRefreshSession = (): boolean => {
  return refreshSessionIfNeeded();
}; 