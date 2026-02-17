"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
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

interface ChallengeCodeDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  loading?: boolean;
}

function generateCode(): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let code = "";
  for (let i = 0; i < 6; i++) {
    code += chars[Math.floor(Math.random() * chars.length)];
  }
  return code;
}

export function ChallengeCodeDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  loading = false,
}: ChallengeCodeDialogProps) {
  const [input, setInput] = useState("");
  const challengeCode = useMemo(() => (open ? generateCode() : ""), [open]);

  useEffect(() => {
    if (open) setInput("");
  }, [open]);

  const isMatch = input.toUpperCase() === challengeCode;

  const handlePaste = useCallback(
    (e: React.ClipboardEvent<HTMLInputElement>) => {
      e.preventDefault();
    },
    []
  );

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-2">
          <p className="text-sm text-muted-foreground">
            To confirm this action, type the following code:
          </p>
          <div className="flex items-center justify-center">
            <span className="rounded-md bg-muted px-4 py-2 font-mono text-lg font-bold tracking-widest">
              {challengeCode}
            </span>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="challenge-input">Confirmation code</Label>
            <Input
              id="challenge-input"
              value={input}
              onChange={(e) => setInput(e.target.value.toUpperCase())}
              onPaste={handlePaste}
              placeholder="Type the code above"
              maxLength={6}
              className="font-mono tracking-widest text-center"
              autoComplete="off"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={!isMatch || loading}
          >
            {loading ? "Processing..." : "Confirm"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
