"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Pencil, Check, X, AlertTriangle } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  useBillingSettings,
  useUpdateBillingSettings,
  useAdminCreditPackages,
  useUpdateCreditPackage,
  useResetSubscriptionPricing,
  useResetCreditPackages,
  type BillingSettings,
  type AdminCreditPackage,
} from "@/hooks/useBilling";
import { PasswordConfirmDialog } from "@/components/shared/PasswordConfirmDialog";

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function centsToDisplay(cents: number): string {
  return (cents / 100).toFixed(2);
}

function displayToCents(display: string): number {
  const parsed = parseFloat(display);
  if (isNaN(parsed) || parsed < 0) return 0;
  return Math.round(parsed * 100);
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ConfirmActionType =
  | "edit-subscription"
  | "edit-package"
  | "reset-subscriptions"
  | "reset-packages";

interface ConfirmAction {
  type: ConfirmActionType;
  payload: Record<string, unknown>;
}

// Known subscription tier keys derived from BillingSettings price fields
const TIER_KEYS = ["standard", "premium"] as const;

function tierDisplayName(key: string): string {
  return key.charAt(0).toUpperCase() + key.slice(1);
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function BillingSettingsPage() {
  // --- Data hooks ---
  const { data, isLoading, error } = useBillingSettings();
  const {
    data: creditPackages,
    isLoading: packagesLoading,
    error: packagesError,
  } = useAdminCreditPackages();

  const updateBillingSettings = useUpdateBillingSettings();
  const updateCreditPackage = useUpdateCreditPackage();
  const resetSubscriptionPricing = useResetSubscriptionPricing();
  const resetCreditPackages = useResetCreditPackages();

  // --- Subscription edit modal state ---
  const [editingTier, setEditingTier] = useState<string | null>(null);
  const [editPrice, setEditPrice] = useState("");

  // --- Credit package edit modal state ---
  const [editingPackage, setEditingPackage] =
    useState<AdminCreditPackage | null>(null);
  const [editName, setEditName] = useState("");
  const [editPkgPrice, setEditPkgPrice] = useState("");
  const [editCredits, setEditCredits] = useState("");
  const [editDisplayOrder, setEditDisplayOrder] = useState("");
  const [editActive, setEditActive] = useState(false);

  // --- Password confirmation dialog state ---
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(
    null
  );
  const [confirmError, setConfirmError] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  async function handleMonetizationToggle(enabled: boolean) {
    try {
      await updateBillingSettings.mutateAsync({
        monetization_enabled: enabled,
      });
      toast.success(
        enabled ? "Monetization enabled" : "Monetization disabled"
      );
    } catch (e: unknown) {
      const err = e as Error;
      toast.error(err.message);
    }
  }

  function openEditSubscription(tierKey: string, currentCents: number) {
    setEditingTier(tierKey);
    setEditPrice(centsToDisplay(currentCents));
  }

  function openEditPackage(pkg: AdminCreditPackage) {
    setEditingPackage(pkg);
    setEditName(pkg.name);
    setEditPkgPrice(centsToDisplay(pkg.price_cents));
    setEditCredits(String(pkg.credit_amount));
    setEditDisplayOrder(String(pkg.display_order));
    setEditActive(pkg.is_active);
  }

  function handleSaveSubscription() {
    if (!editingTier) return;
    const priceCents = displayToCents(editPrice);
    if (priceCents <= 0) {
      toast.error("Please enter a valid price greater than zero");
      return;
    }
    setConfirmAction({
      type: "edit-subscription",
      payload: { tier: editingTier, priceCents },
    });
  }

  function handleSavePackage() {
    if (!editingPackage) return;
    const priceCents = displayToCents(editPkgPrice);
    const creditAmount = parseInt(editCredits, 10);
    const displayOrder = parseInt(editDisplayOrder, 10);
    if (priceCents <= 0 || isNaN(creditAmount) || isNaN(displayOrder)) {
      toast.error("Please fill in all fields with valid numbers");
      return;
    }
    setConfirmAction({
      type: "edit-package",
      payload: {
        packageId: editingPackage.id,
        name: editName,
        priceCents,
        creditAmount,
        displayOrder,
        isActive: editActive,
      },
    });
  }

  function handleResetSubscriptions() {
    setConfirmAction({ type: "reset-subscriptions", payload: {} });
  }

  function handleResetPackages() {
    setConfirmAction({ type: "reset-packages", payload: {} });
  }

  async function handleConfirm(password: string) {
    if (!confirmAction) return;
    setConfirmError(null);
    try {
      if (confirmAction.type === "edit-subscription") {
        const { tier, priceCents } = confirmAction.payload as {
          tier: string;
          priceCents: number;
        };
        await updateBillingSettings.mutateAsync({
          [`price_${tier}_monthly_cents`]: priceCents,
          password,
        });
        toast.success("Pricing updated successfully");
        setEditingTier(null);
      } else if (confirmAction.type === "edit-package") {
        const { packageId, name, priceCents, creditAmount, displayOrder, isActive } =
          confirmAction.payload as {
            packageId: string;
            name: string;
            priceCents: number;
            creditAmount: number;
            displayOrder: number;
            isActive: boolean;
          };
        await updateCreditPackage.mutateAsync({
          packageId,
          name,
          price_cents: priceCents,
          credit_amount: creditAmount,
          display_order: displayOrder,
          is_active: isActive,
          password,
        });
        toast.success("Pricing updated successfully");
        setEditingPackage(null);
      } else if (confirmAction.type === "reset-subscriptions") {
        await resetSubscriptionPricing.mutateAsync({ password });
        toast.success("Subscription pricing reset to defaults");
      } else if (confirmAction.type === "reset-packages") {
        await resetCreditPackages.mutateAsync({ password });
        toast.success("Credit packages reset to defaults");
      }
      setConfirmAction(null);
    } catch (e: unknown) {
      const err = e as Error;
      if (err.message === "Incorrect password") {
        setConfirmError("Incorrect password. Please try again.");
      } else {
        toast.error(err.message || "Failed to save changes. Please try again.");
        setConfirmAction(null);
      }
    }
  }

  // Determine which mutation is pending for the password dialog
  function getConfirmPending(): boolean {
    if (!confirmAction) return false;
    switch (confirmAction.type) {
      case "edit-subscription":
        return updateBillingSettings.isPending;
      case "edit-package":
        return updateCreditPackage.isPending;
      case "reset-subscriptions":
        return resetSubscriptionPricing.isPending;
      case "reset-packages":
        return resetCreditPackages.isPending;
      default:
        return false;
    }
  }

  function getConfirmTitle(): string {
    if (!confirmAction) return "";
    switch (confirmAction.type) {
      case "edit-subscription":
        return "Confirm Changes";
      case "edit-package":
        return "Confirm Changes";
      case "reset-subscriptions":
        return "Confirm Reset";
      case "reset-packages":
        return "Confirm Reset";
      default:
        return "Confirm";
    }
  }

  function getConfirmImpactText(): string {
    if (!confirmAction) return "";
    switch (confirmAction.type) {
      case "edit-subscription": {
        const tier = confirmAction.payload.tier as string;
        return `This will update the subscription price for ${tierDisplayName(tier)}. A new Stripe Price will be created automatically. Existing subscribers will keep their current price.`;
      }
      case "edit-package": {
        const name = confirmAction.payload.name as string;
        return `This will update the ${name} credit package. Changes take effect immediately for new purchases.`;
      }
      case "reset-subscriptions":
        return "This will reset all subscription prices to their config-file defaults. New Stripe Prices will be created if needed. Existing subscribers keep their current price.";
      case "reset-packages":
        return "This will reset all credit packages to config-file defaults. Names, prices, credits, and display order will be restored. Existing purchase history is preserved.";
      default:
        return "";
    }
  }

  function getConfirmLabel(): string {
    if (!confirmAction) return "";
    if (
      confirmAction.type === "reset-subscriptions" ||
      confirmAction.type === "reset-packages"
    ) {
      return "Confirm Reset";
    }
    return "Confirm Changes";
  }

  function getConfirmVariant(): "default" | "destructive" {
    if (!confirmAction) return "default";
    if (
      confirmAction.type === "reset-subscriptions" ||
      confirmAction.type === "reset-packages"
    ) {
      return "destructive";
    }
    return "default";
  }

  // ---------------------------------------------------------------------------
  // Render: Error state
  // ---------------------------------------------------------------------------

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-destructive">
          Failed to load settings: {error.message}
        </p>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render: Page
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Billing Settings</h1>
        <p className="text-muted-foreground">
          Configure monetization and pricing settings
        </p>
      </div>

      <div className="max-w-2xl mx-auto space-y-6">
        {/* ----------------------------------------------------------------- */}
        {/* Section 1: Monetization Card                                      */}
        {/* ----------------------------------------------------------------- */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Monetization</CardTitle>
            <CardDescription>Master switch for billing features</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading || !data ? (
              <Skeleton className="h-10 w-full" />
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <Label htmlFor="monetization-switch">
                    Enable Monetization
                  </Label>
                  <Switch
                    id="monetization-switch"
                    checked={data.monetization_enabled}
                    onCheckedChange={handleMonetizationToggle}
                    disabled={
                      !data.stripe_readiness.ready &&
                      !data.monetization_enabled
                    }
                  />
                </div>
                <p className="text-sm text-muted-foreground">
                  When disabled, all billing UI is hidden from users. Existing
                  subscribers keep their plan and can still cancel. New users
                  receive Free Trial as default.
                </p>
                <div className="space-y-2 pt-2">
                  {data.stripe_readiness.ready ? (
                    <>
                      <div className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-green-500 shrink-0" />
                        <span className="text-sm font-medium text-green-500">
                          Stripe configuration complete
                        </span>
                      </div>
                      <div className="space-y-1 pl-6">
                        {data.stripe_price_standard_monthly && (
                          <div className="flex items-center gap-2">
                            <Check className="h-3 w-3 text-green-500 shrink-0" />
                            <span className="text-sm text-muted-foreground">Standard subscription price</span>
                          </div>
                        )}
                        {data.stripe_price_premium_monthly && (
                          <div className="flex items-center gap-2">
                            <Check className="h-3 w-3 text-green-500 shrink-0" />
                            <span className="text-sm text-muted-foreground">Premium subscription price</span>
                          </div>
                        )}
                        <div className="flex items-center gap-2">
                          <Check className="h-3 w-3 text-green-500 shrink-0" />
                          <span className="text-sm text-muted-foreground">Stripe API key configured</span>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                        <span className="text-sm font-medium">
                          Stripe configuration incomplete:
                        </span>
                      </div>
                      <div className="space-y-1 pl-6">
                        {data.stripe_readiness.missing.map((item) => (
                          <div
                            key={item}
                            className="flex items-center gap-2"
                          >
                            <X className="h-3 w-3 text-destructive shrink-0" />
                            <span className="text-sm">{item}</span>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-muted-foreground pl-6">
                        Toggle will be enabled when all items are configured.
                      </p>
                    </>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* ----------------------------------------------------------------- */}
        {/* Section 2: Subscription Pricing Card                              */}
        {/* ----------------------------------------------------------------- */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Subscription Pricing</CardTitle>
            <CardDescription>
              Changing prices creates new Stripe Price objects. Existing
              subscribers keep their current price.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading || !data ? (
              <div className="space-y-4">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : (
              <div className="space-y-4">
                {TIER_KEYS.map((tierKey, idx) => {
                      const priceKey =
                        `price_${tierKey}_monthly_cents` as keyof BillingSettings;
                      const currentCents =
                        (data[priceKey] as number) ?? 0;
                      const defaultCents =
                        data.config_defaults?.[
                          `price_${tierKey}_monthly_cents`
                        ] ?? null;
                      const stripePriceId =
                        data[`stripe_price_${tierKey}_monthly` as keyof BillingSettings] as string;

                      return (
                        <div key={tierKey}>
                          {idx > 0 && <Separator className="mb-4" />}
                          <div className="flex items-start justify-between">
                            <div className="space-y-1">
                              <p className="text-sm">
                                {tierDisplayName(tierKey)}
                              </p>
                              <p className="text-base font-semibold">
                                ${centsToDisplay(currentCents)} / month
                              </p>
                              {defaultCents !== null && (
                                <p className="text-xs text-muted-foreground">
                                  Default: ${centsToDisplay(defaultCents)}
                                </p>
                              )}
                              <p className="text-xs font-mono text-muted-foreground">
                                Stripe: {stripePriceId || "Not set"}
                              </p>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                openEditSubscription(
                                  tierKey,
                                  currentCents
                                )
                              }
                            >
                              <Pencil className="h-4 w-4 mr-1" />
                              Edit Pricing
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                <Separator />
                <Button
                  variant="outline"
                  className="text-destructive"
                  onClick={handleResetSubscriptions}
                >
                  Reset to Defaults
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ----------------------------------------------------------------- */}
        {/* Section 3: Credit Packages Card                                   */}
        {/* ----------------------------------------------------------------- */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Credit Packages</CardTitle>
            <CardDescription>
              Configure credit package pricing and availability.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {packagesLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </div>
            ) : packagesError ? (
              <p className="text-sm text-destructive">
                Failed to load credit packages: {packagesError.message}
              </p>
            ) : !creditPackages || creditPackages.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No credit packages found. Run startup sync or check
                configuration.
              </p>
            ) : (
              <div className="space-y-4">
                {creditPackages.map((pkg, idx) => (
                  <div key={pkg.id}>
                    {idx > 0 && <Separator className="mb-4" />}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm">{pkg.name}</p>
                        <Badge
                          variant={
                            pkg.is_active ? "default" : "secondary"
                          }
                        >
                          {pkg.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </div>
                      <p className="text-sm">
                        ${centsToDisplay(pkg.price_cents)} &middot;{" "}
                        {pkg.credit_amount} credits
                      </p>
                      {pkg.config_defaults && (
                        <p className="text-xs text-muted-foreground">
                          Default: $
                          {centsToDisplay(pkg.config_defaults.price_cents)}{" "}
                          &middot; {pkg.config_defaults.credit_amount} credits
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        Display order: {pkg.display_order}
                      </p>
                      <p className="text-xs font-mono text-muted-foreground">
                        Stripe: {pkg.stripe_price_id || "Not set"}
                      </p>
                      <div className="flex justify-end pt-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openEditPackage(pkg)}
                        >
                          <Pencil className="h-4 w-4 mr-1" />
                          Edit Package
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
                <Separator />
                <Button
                  variant="outline"
                  className="text-destructive"
                  onClick={handleResetPackages}
                >
                  Reset to Defaults
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* Edit Subscription Modal                                             */}
      {/* ------------------------------------------------------------------- */}
      <Dialog
        open={editingTier !== null}
        onOpenChange={(open) => {
          if (!open) setEditingTier(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Subscription Pricing</DialogTitle>
            <DialogDescription>
              {editingTier
                ? `Update the monthly price for the ${tierDisplayName(editingTier)} tier.`
                : ""}
            </DialogDescription>
          </DialogHeader>
          {editingTier && data && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-sub-price">Monthly Price ($)</Label>
                <Input
                  id="edit-sub-price"
                  type="number"
                  min={0}
                  step="0.01"
                  value={editPrice}
                  onChange={(e) => setEditPrice(e.target.value)}
                  className="mt-2"
                />
                {data.config_defaults?.[
                  `price_${editingTier}_monthly_cents`
                ] != null && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Default: $
                    {centsToDisplay(
                      data.config_defaults[
                        `price_${editingTier}_monthly_cents`
                      ]
                    )}
                  </p>
                )}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditingTier(null)}
            >
              Discard Changes
            </Button>
            <Button onClick={handleSaveSubscription}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ------------------------------------------------------------------- */}
      {/* Edit Credit Package Modal                                           */}
      {/* ------------------------------------------------------------------- */}
      <Dialog
        open={editingPackage !== null}
        onOpenChange={(open) => {
          if (!open) setEditingPackage(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Credit Package</DialogTitle>
            <DialogDescription>
              {editingPackage
                ? `Update the ${editingPackage.name} credit package.`
                : ""}
            </DialogDescription>
          </DialogHeader>
          {editingPackage && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-pkg-name">Package Name</Label>
                <Input
                  id="edit-pkg-name"
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="mt-2"
                />
                {editingPackage.config_defaults?.name && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Default: {editingPackage.config_defaults.name}
                  </p>
                )}
              </div>
              <div>
                <Label htmlFor="edit-pkg-price">Price ($)</Label>
                <Input
                  id="edit-pkg-price"
                  type="number"
                  min={0}
                  step="0.01"
                  value={editPkgPrice}
                  onChange={(e) => setEditPkgPrice(e.target.value)}
                  className="mt-2"
                />
                {editingPackage.config_defaults?.price_cents != null && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Default: $
                    {centsToDisplay(
                      editingPackage.config_defaults.price_cents
                    )}
                  </p>
                )}
              </div>
              <div>
                <Label htmlFor="edit-pkg-credits">Credits</Label>
                <Input
                  id="edit-pkg-credits"
                  type="number"
                  min={0}
                  value={editCredits}
                  onChange={(e) => setEditCredits(e.target.value)}
                  className="mt-2"
                />
                {editingPackage.config_defaults?.credit_amount != null && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Default: {editingPackage.config_defaults.credit_amount}
                  </p>
                )}
              </div>
              <div>
                <Label htmlFor="edit-pkg-order">Display Order</Label>
                <Input
                  id="edit-pkg-order"
                  type="number"
                  min={0}
                  value={editDisplayOrder}
                  onChange={(e) => setEditDisplayOrder(e.target.value)}
                  className="mt-2"
                />
                {editingPackage.config_defaults?.display_order != null && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Default: {editingPackage.config_defaults.display_order}
                  </p>
                )}
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="edit-pkg-active">Active</Label>
                <Switch
                  id="edit-pkg-active"
                  checked={editActive}
                  onCheckedChange={setEditActive}
                />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">
                  Stripe Price ID
                </Label>
                <p className="text-xs font-mono text-muted-foreground mt-1">
                  {editingPackage.stripe_price_id || "Not set"}
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditingPackage(null)}
            >
              Discard Changes
            </Button>
            <Button onClick={handleSavePackage}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ------------------------------------------------------------------- */}
      {/* Password Confirmation Dialog (shared)                               */}
      {/* ------------------------------------------------------------------- */}
      <PasswordConfirmDialog
        open={confirmAction !== null}
        onOpenChange={(open) => {
          if (!open) {
            setConfirmAction(null);
            setConfirmError(null);
          }
        }}
        title={getConfirmTitle()}
        impactText={getConfirmImpactText()}
        confirmLabel={getConfirmLabel()}
        variant={getConfirmVariant()}
        isPending={getConfirmPending()}
        onConfirm={handleConfirm}
        error={confirmError}
      />
    </div>
  );
}
