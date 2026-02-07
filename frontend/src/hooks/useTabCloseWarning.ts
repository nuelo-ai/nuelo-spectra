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
      // Modern browsers require returnValue to be truthy (not empty string)
      // Setting to true triggers the generic "Leave site?" dialog
      event.returnValue = true as any; // Type cast needed as spec requires string but browsers accept boolean
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [hasContext]);
}
