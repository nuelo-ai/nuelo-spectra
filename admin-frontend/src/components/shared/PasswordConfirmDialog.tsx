"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface PasswordConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  impactText: string;
  confirmLabel: string;
  variant?: "default" | "destructive";
  isPending: boolean;
  onConfirm: (password: string) => void;
  error?: string | null;
}

export function PasswordConfirmDialog({
  open,
  onOpenChange,
  title,
  impactText,
  confirmLabel,
  variant = "default",
  isPending,
  onConfirm,
  error,
}: PasswordConfirmDialogProps) {
  const [password, setPassword] = useState("");

  function handleOpenChange(v: boolean) {
    if (!v) {
      setPassword("");
    }
    onOpenChange(v);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{impactText}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="confirm-password">
              Enter your password to confirm
            </Label>
            <Input
              id="confirm-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-2"
              onKeyDown={(e) => {
                if (e.key === "Enter" && password && !isPending) {
                  onConfirm(password);
                }
              }}
            />
            {error && (
              <p className="text-sm text-destructive mt-1">{error}</p>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isPending}
          >
            Go Back
          </Button>
          <Button
            variant={variant === "destructive" ? "destructive" : "default"}
            disabled={!password || isPending}
            onClick={() => onConfirm(password)}
          >
            {isPending ? "Confirming..." : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
