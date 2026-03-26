"use client";

import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useBillingSettings,
  useUpdateBillingSettings,
  type BillingSettings,
} from "@/hooks/useBilling";

function centsToDisplay(cents: number): string {
  return (cents / 100).toFixed(2);
}

function displayToCents(display: string): number {
  return Math.round(parseFloat(display) * 100);
}

export default function BillingSettingsPage() {
  const { data, isLoading, error } = useBillingSettings();
  const updateSettings = useUpdateBillingSettings();

  // Local form state
  const [form, setForm] = useState<BillingSettings | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  // Price display values (dollars as strings for controlled inputs)
  const [standardPrice, setStandardPrice] = useState("");
  const [premiumPrice, setPremiumPrice] = useState("");

  useEffect(() => {
    if (data && !form) {
      setForm(data);
      setStandardPrice(centsToDisplay(data.price_standard_monthly_cents));
      setPremiumPrice(centsToDisplay(data.price_premium_monthly_cents));
    }
  }, [data, form]);

  const updateField = useCallback(
    <K extends keyof BillingSettings>(key: K, value: BillingSettings[K]) => {
      setForm((prev) => (prev ? { ...prev, [key]: value } : null));
      setIsDirty(true);
    },
    []
  );

  const handleSave = async () => {
    if (!form || !data) return;

    // Compute changed fields only
    const changes: Partial<BillingSettings> = {};
    if (form.monetization_enabled !== data.monetization_enabled) {
      changes.monetization_enabled = form.monetization_enabled;
    }

    // Include price changes from display inputs
    const newStandardCents = displayToCents(standardPrice);
    const newPremiumCents = displayToCents(premiumPrice);
    if (newStandardCents !== data.price_standard_monthly_cents) {
      changes.price_standard_monthly_cents = newStandardCents;
    }
    if (newPremiumCents !== data.price_premium_monthly_cents) {
      changes.price_premium_monthly_cents = newPremiumCents;
    }

    if (Object.keys(changes).length === 0) {
      toast.info("No changes to save");
      return;
    }

    try {
      const updated = await updateSettings.mutateAsync(changes);
      toast.success("Billing settings saved");
      setIsDirty(false);
      // Update form with server response to avoid stale query snap-back
      setForm(updated);
      setStandardPrice(centsToDisplay(updated.price_standard_monthly_cents));
      setPremiumPrice(centsToDisplay(updated.price_premium_monthly_cents));
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-destructive">
          Failed to load settings: {error.message}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Billing Settings</h1>
        <p className="text-muted-foreground">
          Configure monetization and pricing settings
        </p>
      </div>

      <div className="max-w-2xl mx-auto space-y-6">
        {/* Card 1: Monetization */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Monetization</CardTitle>
            <CardDescription>Master switch for billing features</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading || !form ? (
              <Skeleton className="h-10 w-full" />
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <Label htmlFor="monetization-switch">
                    Enable Monetization
                  </Label>
                  <Switch
                    id="monetization-switch"
                    checked={form.monetization_enabled}
                    onCheckedChange={(v) =>
                      updateField("monetization_enabled", v)
                    }
                  />
                </div>
                <p className="text-sm text-muted-foreground">
                  When disabled, all billing UI is hidden from users. Existing
                  subscribers keep their plan and can still cancel. New users
                  receive Free Trial as default.
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Card 2: Subscription Pricing */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Subscription Pricing</CardTitle>
            <CardDescription>
              Changing prices creates new Stripe Price objects automatically
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading || !form ? (
              <div className="space-y-4">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <Label htmlFor="basic-price">Basic Monthly Price ($)</Label>
                  <Input
                    id="basic-price"
                    type="number"
                    min={0}
                    step="0.01"
                    value={standardPrice}
                    onChange={(e) => {
                      setStandardPrice(e.target.value);
                      setIsDirty(true);
                    }}
                    className="mt-1.5"
                  />
                </div>
                <div>
                  <Label htmlFor="premium-price">
                    Premium Monthly Price ($)
                  </Label>
                  <Input
                    id="premium-price"
                    type="number"
                    min={0}
                    step="0.01"
                    value={premiumPrice}
                    onChange={(e) => {
                      setPremiumPrice(e.target.value);
                      setIsDirty(true);
                    }}
                    className="mt-1.5"
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Save button */}
        <Button
          onClick={handleSave}
          disabled={!isDirty || updateSettings.isPending}
          className="w-full"
        >
          {updateSettings.isPending ? "Saving..." : "Save Billing Settings"}
        </Button>
      </div>
    </div>
  );
}
