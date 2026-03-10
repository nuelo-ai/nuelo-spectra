"use client";

import { useEffect, useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2Icon, SaveIcon } from "lucide-react";
import { toast } from "sonner";
import type { PlatformSettings } from "@/types/settings";
import { useUpdateSettings } from "@/hooks/useSettings";
import { useTiers } from "@/hooks/useTiers";
import { useAppVersion } from "@/hooks/useAppVersion";

interface SettingsFormProps {
  settings: PlatformSettings | undefined;
  isLoading: boolean;
}

export function SettingsForm({ settings, isLoading }: SettingsFormProps) {
  const updateSettings = useUpdateSettings();
  const { data: tiers } = useTiers();
  const { data: versionData } = useAppVersion();

  const [allowPublicSignup, setAllowPublicSignup] = useState(false);
  const [defaultUserClass, setDefaultUserClass] = useState("free");
  const [inviteExpiryDays, setInviteExpiryDays] = useState(7);
  const [defaultCreditCost, setDefaultCreditCost] = useState(1);
  const [maxPendingInvites, setMaxPendingInvites] = useState(10);
  const [pulseCreditCost, setPulseCreditCost] = useState(5);

  // Sync form state when settings data loads
  useEffect(() => {
    if (settings) {
      setAllowPublicSignup(settings.allow_public_signup);
      setDefaultUserClass(settings.default_user_class);
      setInviteExpiryDays(settings.invite_expiry_days);
      setDefaultCreditCost(settings.default_credit_cost);
      setMaxPendingInvites(settings.max_pending_invites);
      setPulseCreditCost(settings.workspace_credit_cost_pulse);
    }
  }, [settings]);

  const handleSave = () => {
    // Validation
    if (defaultCreditCost <= 0) {
      toast.error("Credit cost must be greater than 0");
      return;
    }
    if (pulseCreditCost <= 0) {
      toast.error("Pulse detection cost must be greater than 0");
      return;
    }
    if (inviteExpiryDays <= 0) {
      toast.error("Invite expiry must be greater than 0");
      return;
    }
    if (maxPendingInvites <= 0) {
      toast.error("Max pending invites must be greater than 0");
      return;
    }

    updateSettings.mutate(
      {
        allow_public_signup: allowPublicSignup,
        default_user_class: defaultUserClass,
        invite_expiry_days: inviteExpiryDays,
        default_credit_cost: defaultCreditCost,
        max_pending_invites: maxPendingInvites,
        workspace_credit_cost_pulse: pulseCreditCost,
      },
      {
        onSuccess: () => {
          toast.success("Settings saved successfully");
        },
        onError: (error) => {
          toast.error(error.message || "Failed to save settings");
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Signup Control */}
      <Card>
        <CardHeader>
          <CardTitle>Signup Control</CardTitle>
          <CardDescription>
            Control how new users can join the platform
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="public-signup">Allow Public Signup</Label>
              <p className="text-sm text-muted-foreground">
                When enabled, users can register without an invitation
              </p>
            </div>
            <Switch
              id="public-signup"
              checked={allowPublicSignup}
              onCheckedChange={setAllowPublicSignup}
            />
          </div>
          <Separator />
          <div className="space-y-2">
            <Label htmlFor="default-class">Default User Class</Label>
            <Select
              value={defaultUserClass}
              onValueChange={setDefaultUserClass}
            >
              <SelectTrigger id="default-class" className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {tiers?.map((tier) => (
                  <SelectItem key={tier.name} value={tier.name}>
                    {tier.display_name}
                  </SelectItem>
                )) ?? (
                  <SelectItem value={defaultUserClass} disabled>
                    Loading...
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Tier assigned to newly registered users
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Invitations */}
      <Card>
        <CardHeader>
          <CardTitle>Invitations</CardTitle>
          <CardDescription>
            Configure invitation behavior and limits
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="invite-expiry">Invite Expiry (days)</Label>
            <Input
              id="invite-expiry"
              type="number"
              min={1}
              value={inviteExpiryDays}
              onChange={(e) => setInviteExpiryDays(Number(e.target.value))}
              className="w-32"
            />
            <p className="text-sm text-muted-foreground">
              Number of days before an invitation link expires
            </p>
          </div>
          <Separator />
          <div className="space-y-2">
            <Label htmlFor="max-pending">Max Pending Invites</Label>
            <Input
              id="max-pending"
              type="number"
              min={1}
              value={maxPendingInvites}
              onChange={(e) => setMaxPendingInvites(Number(e.target.value))}
              className="w-32"
            />
            <p className="text-sm text-muted-foreground">
              Maximum number of pending invitations allowed at once
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Credits */}
      <Card>
        <CardHeader>
          <CardTitle>Credits</CardTitle>
          <CardDescription>
            Configure credit allocation and cost settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>Credit Reset Policy (per tier)</Label>
            <p className="text-sm text-muted-foreground mb-2">
              Reset policies are defined per tier in user_classes.yaml
            </p>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tier</TableHead>
                    <TableHead>Reset Policy</TableHead>
                    <TableHead className="text-right">Credits</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tiers?.map((tier) => (
                    <TableRow key={tier.name}>
                      <TableCell className="font-medium">{tier.display_name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{tier.reset_policy}</Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono">{tier.credits}</TableCell>
                    </TableRow>
                  )) ?? (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-muted-foreground">
                        Loading tiers...
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
          <Separator />
          <div className="space-y-2">
            <Label htmlFor="credit-cost">Default Credit Cost per Message</Label>
            <Input
              id="credit-cost"
              type="number"
              min={0.1}
              step={0.1}
              value={defaultCreditCost}
              onChange={(e) => setDefaultCreditCost(Number(e.target.value))}
              className="w-32"
            />
            <p className="text-sm text-muted-foreground">
              Number of credits deducted per agent message
            </p>
          </div>
          <Separator />
          <div className="space-y-2">
            <Label htmlFor="pulse-credit-cost">Pulse Detection Cost per Run</Label>
            <Input
              id="pulse-credit-cost"
              type="number"
              min={0.1}
              step={0.1}
              value={pulseCreditCost}
              onChange={(e) => setPulseCreditCost(Number(e.target.value))}
              className="w-32"
            />
            <p className="text-sm text-muted-foreground">
              Number of credits deducted per Pulse detection run
            </p>
          </div>
        </CardContent>
      </Card>

      {/* App Version */}
      <Card>
        <CardHeader>
          <CardTitle>App Version</CardTitle>
          <CardDescription>
            Current deployment version and environment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Version</Label>
            <p className="text-sm text-muted-foreground font-mono">
              {versionData?.version ?? "\u2014"}
            </p>
          </div>
          <div className="space-y-2">
            <Label>Environment</Label>
            <p className="text-sm text-muted-foreground font-mono">
              {versionData?.environment ?? "\u2014"}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Save button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={updateSettings.isPending}
          size="lg"
        >
          {updateSettings.isPending ? (
            <Loader2Icon className="mr-2 size-4 animate-spin" />
          ) : (
            <SaveIcon className="mr-2 size-4" />
          )}
          Save Settings
        </Button>
      </div>
    </div>
  );
}
