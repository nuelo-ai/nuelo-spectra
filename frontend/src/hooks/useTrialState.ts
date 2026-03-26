"use client";

import { useMemo } from "react";
import { useAuth } from "./useAuth";

export interface TrialState {
  /** User is on free_trial tier */
  isTrial: boolean;
  /** Trial period has expired (trial_expires_at is in the past) */
  isExpired: boolean;
  /** Days remaining in trial (0 if expired, null if not trial) */
  daysRemaining: number | null;
  /** Parsed trial expiration date, null if not a trial user */
  trialExpiresAt: Date | null;
}

export function useTrialState(): TrialState {
  const { user } = useAuth();

  return useMemo(() => {
    if (!user || user.user_class !== "free_trial" || !user.trial_expires_at) {
      return { isTrial: false, isExpired: false, daysRemaining: null, trialExpiresAt: null };
    }

    const expiresAt = new Date(user.trial_expires_at);
    const now = new Date();
    const diffMs = expiresAt.getTime() - now.getTime();
    const daysRemaining = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    return {
      isTrial: true,
      isExpired: daysRemaining <= 0,
      daysRemaining: Math.max(0, daysRemaining),
      trialExpiresAt: expiresAt,
    };
  }, [user]);
}
