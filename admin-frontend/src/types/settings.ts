/**
 * TypeScript types for admin platform settings.
 * Mirrors backend schemas: platform_settings.py
 */

export interface PlatformSettings {
  allow_public_signup: boolean;
  default_user_class: string;
  invite_expiry_days: number;
  credit_reset_policy: string;
  default_credit_cost: number;
  max_pending_invites: number;
}

export type PlatformSettingsUpdate = Partial<PlatformSettings>;
