"use client";

import { useState } from "react";
import { toast } from "sonner";
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
import { useCreateInvitation } from "@/hooks/useInvitations";

interface CreateInviteDialogProps {
  open: boolean;
  onClose: () => void;
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function CreateInviteDialog({ open, onClose }: CreateInviteDialogProps) {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const createInvitation = useCreateInvitation();

  const handleSubmit = async () => {
    if (!isValidEmail(email)) {
      setEmailError("Please enter a valid email address");
      return;
    }
    setEmailError("");

    try {
      await createInvitation.mutateAsync({ email: email.trim() });
      toast.success(`Invitation sent to ${email}`);
      setEmail("");
      onClose();
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  const handleClose = () => {
    setEmail("");
    setEmailError("");
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Invitation</DialogTitle>
          <DialogDescription>
            Send an invitation email to a new user. They will receive a link to
            register.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 py-2">
          <div>
            <Label htmlFor="invite-email">Email Address</Label>
            <Input
              id="invite-email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (emailError) setEmailError("");
              }}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              placeholder="user@example.com"
              className="mt-1.5"
            />
            {emailError && (
              <p className="text-sm text-destructive mt-1">{emailError}</p>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={createInvitation.isPending || !email.trim()}
          >
            {createInvitation.isPending ? "Sending..." : "Send Invitation"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
