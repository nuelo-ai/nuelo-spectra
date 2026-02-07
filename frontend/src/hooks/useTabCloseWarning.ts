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
      event.preventDefault();
      // Modern browsers require returnValue to be set (spec requirement)
      event.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [hasContext]);
}
