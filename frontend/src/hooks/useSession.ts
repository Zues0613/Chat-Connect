import { useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { autoRefreshSession, trackUserActivity, isSessionValid, clearSession } from '../utils/cookies';

export const useSession = () => {
  const router = useRouter();

  // Track user activity on various events
  const handleUserActivity = useCallback(() => {
    trackUserActivity();
  }, []);

  // Check and refresh session periodically
  const checkSession = useCallback(() => {
    if (!autoRefreshSession()) {
      console.log('[DEBUG] Session expired, redirecting to login');
      router.replace('/login');
    }
  }, [router]);

  useEffect(() => {
    // Set up activity tracking for user interactions
    const activityEvents = [
      'mousedown',
      'mousemove',
      'keypress',
      'scroll',
      'touchstart',
      'click'
    ];

    // Add activity listeners
    activityEvents.forEach(event => {
      document.addEventListener(event, handleUserActivity, true);
    });

    // Set up periodic session check (every 5 minutes)
    const sessionCheckInterval = setInterval(checkSession, 5 * 60 * 1000);

    // Initial session check
    if (!isSessionValid()) {
      clearSession();
      router.replace('/login');
    }

    // Cleanup
    return () => {
      activityEvents.forEach(event => {
        document.removeEventListener(event, handleUserActivity, true);
      });
      clearInterval(sessionCheckInterval);
    };
  }, [handleUserActivity, checkSession, router]);

  return {
    checkSession,
    trackActivity: handleUserActivity
  };
}; 