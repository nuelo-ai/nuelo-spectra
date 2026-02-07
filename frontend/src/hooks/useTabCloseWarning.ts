import { useEffect } from 'react';

/**
 * Show browser-native confirmation dialog when user tries to close/refresh
 * a browser tab that has active conversation context.
 *
 * Modern browsers show a generic "Leave site?" message — custom messages
 * are not supported for security reasons.
 *
 * @param hasContext - Whether the current tab has accumulated conversation context
 */
export function useTabCloseWarning(hasContext: boolean) {
  useEffect(() => {
    if (!hasContext) return;

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      // Modern browsers (Chrome 119+, Firefox, Safari) require:
      // 1. preventDefault() to be called, OR
      // 2. returnValue to be set to a non-empty string (not boolean)
      // We do both for maximum compatibility
      event.preventDefault();
      event.returnValue = 'true'; // Must be a non-empty string (spec requires string type)
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [hasContext]);
}
