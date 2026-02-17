"use client";

import { useCallback, useEffect, useState } from "react";
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
import { Loader2Icon } from "lucide-react";

interface ChallengeCodeDialogProps {
  open: boolean;
  onClose: () => void;
  onFetchChallenge: () => Promise<{ challenge_code: string; expires_in: number }>;
  onConfirm: (challengeCode: string) => void;
  title: string;
  description: string;
  loading?: boolean;
}

export function ChallengeCodeDialog({
  open,
  onClose,
  onFetchChallenge,
  onConfirm,
  title,
  description,
  loading = false,
}: ChallengeCodeDialogProps) {
  const [input, setInput] = useState("");
  const [challengeCode, setChallengeCode] = useState("");
  const [fetching, setFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setInput("");
      setChallengeCode("");
      setFetchError(null);
      setFetching(true);
      onFetchChallenge()
        .then((result) => {
          setChallengeCode(result.challenge_code);
        })
        .catch((err) => {
          setFetchError(err.message || "Failed to fetch challenge code");
        })
        .finally(() => {
          setFetching(false);
        });
    }
  }, [open, onFetchChallenge]);

  const isMatch = challengeCode !== "" && input.toUpperCase() === challengeCode.toUpperCase();

  const handleRetry = useCallback(() => {
    setFetchError(null);
    setFetching(true);
    onFetchChallenge()
      .then((result) => {
        setChallengeCode(result.challenge_code);
      })
      .catch((err) => {
        setFetchError(err.message || "Failed to fetch challenge code");
      })
      .finally(() => {
        setFetching(false);
      });
  }, [onFetchChallenge]);

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
          {fetching ? (
            <div className="flex items-center justify-center py-4">
              <Loader2Icon className="size-5 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">
                Fetching challenge code...
              </span>
            </div>
          ) : fetchError ? (
            <div className="space-y-2 text-center py-4">
              <p className="text-sm text-destructive">{fetchError}</p>
              <Button variant="outline" size="sm" onClick={handleRetry}>
                Retry
              </Button>
            </div>
          ) : (
            <>
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
                  maxLength={challengeCode.length || 6}
                  className="font-mono tracking-widest text-center"
                  autoComplete="off"
                />
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={() => onConfirm(challengeCode)}
            disabled={!isMatch || loading || fetching}
          >
            {loading ? "Processing..." : "Confirm"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
