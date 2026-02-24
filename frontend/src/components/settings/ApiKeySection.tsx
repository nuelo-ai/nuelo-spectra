"use client";

/**
 * API key management section for the Settings page.
 * Displays list of API keys with create, copy, and revoke functionality.
 */

import { useState } from "react";
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from "@/hooks/useApiKeys";
import type { ApiKeyCreateResponse } from "@/hooks/useApiKeys";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Copy, Check, Plus, Key, Trash2 } from "lucide-react";

export function ApiKeySection() {
  const { data: keys, isLoading, error } = useApiKeys();
  const createKey = useCreateApiKey();
  const revokeKey = useRevokeApiKey();

  // Create dialog state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyDescription, setNewKeyDescription] = useState("");

  // One-time key display dialog state
  const [createdKey, setCreatedKey] = useState<ApiKeyCreateResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // Revoke confirmation state
  const [revokeTarget, setRevokeTarget] = useState<{ id: string; name: string } | null>(null);

  const handleCreate = () => {
    if (!newKeyName.trim()) return;

    createKey.mutate(
      {
        name: newKeyName.trim(),
        description: newKeyDescription.trim() || undefined,
      },
      {
        onSuccess: (data) => {
          setCreateDialogOpen(false);
          setNewKeyName("");
          setNewKeyDescription("");
          setCreatedKey(data);
          setCopied(false);
        },
      }
    );
  };

  const handleCopyKey = async () => {
    if (!createdKey) return;
    await navigator.clipboard.writeText(createdKey.full_key);
    setCopied(true);
  };

  const handleConfirmCopied = () => {
    setCreatedKey(null);
    setCopied(false);
  };

  const handleRevoke = () => {
    if (!revokeTarget) return;
    revokeKey.mutate(revokeTarget.id, {
      onSuccess: () => {
        setRevokeTarget(null);
      },
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>Manage your API keys for programmatic access</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>Manage your API keys for programmatic access</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Failed to load API keys. Please try again.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>Manage your API keys for programmatic access</CardDescription>
            </div>
            <Button onClick={() => setCreateDialogOpen(true)} size="sm">
              <Plus className="mr-2 h-4 w-4" />
              Create API Key
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Empty state */}
          {(!keys || keys.length === 0) && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Key className="h-10 w-10 text-muted-foreground/50 mb-3" />
              <p className="text-sm font-medium text-muted-foreground">No API keys yet</p>
              <p className="text-xs text-muted-foreground/70 mt-1">
                Create an API key to access the Spectra API programmatically.
              </p>
            </div>
          )}

          {/* Key list */}
          {keys && keys.length > 0 && (
            <div className="space-y-3">
              {keys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="space-y-1 min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium truncate">{key.name}</span>
                      {key.is_active ? (
                        <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                          Revoked
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="font-mono">{key.key_prefix}...</span>
                      <span>Created {new Date(key.created_at).toLocaleDateString()}</span>
                      {key.last_used_at && (
                        <span>Last used {new Date(key.last_used_at).toLocaleDateString()}</span>
                      )}
                      <span>Credits: {key.total_credits_used.toFixed(1)}</span>
                    </div>
                  </div>
                  {key.is_active && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive hover:bg-destructive/10 ml-2"
                      onClick={() => setRevokeTarget({ id: key.id, name: key.name })}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create API Key Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create API Key</DialogTitle>
            <DialogDescription>
              Create a new API key for programmatic access. The key will only be shown once.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="key-name">Name</Label>
              <Input
                id="key-name"
                placeholder="e.g., Production Server"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreate();
                }}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="key-description">Description (optional)</Label>
              <Input
                id="key-description"
                placeholder="What this key is used for"
                value={newKeyDescription}
                onChange={(e) => setNewKeyDescription(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newKeyName.trim() || createKey.isPending}
            >
              {createKey.isPending ? "Creating..." : "Create Key"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* One-time Key Display Dialog */}
      <Dialog
        open={createdKey !== null}
        onOpenChange={() => {
          // Prevent closing via overlay click or escape — user must click "I have copied my key"
        }}
      >
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>API Key Created</DialogTitle>
            <DialogDescription>
              This key will not be shown again. Copy it now and store it securely.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <Label>Your API Key</Label>
            <div className="flex items-center gap-2">
              <code className="flex-1 rounded-md border bg-muted px-3 py-2 font-mono text-sm break-all select-all">
                {createdKey?.full_key}
              </code>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyKey}
                className="shrink-0"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
            {copied && (
              <p className="text-xs text-green-600">Copied to clipboard</p>
            )}
          </div>
          <DialogFooter>
            <Button onClick={handleConfirmCopied}>
              I have copied my key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Revoke Confirmation Dialog */}
      <AlertDialog open={revokeTarget !== null} onOpenChange={(open) => { if (!open) setRevokeTarget(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke API Key</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to revoke &quot;{revokeTarget?.name}&quot;? This action cannot be
              undone. Any applications using this key will immediately lose access.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleRevoke}
            >
              {revokeKey.isPending ? "Revoking..." : "Revoke Key"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
