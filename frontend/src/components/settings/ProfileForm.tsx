"use client";

/**
 * ProfileForm component for editing first name and last name.
 * Pre-fills with current user data and saves changes via API.
 */

import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useUpdateProfile } from "@/hooks/useSettings";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

export function ProfileForm() {
  const { user } = useAuth();
  const updateProfile = useUpdateProfile();

  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName, setLastName] = useState(user?.last_name || "");

  // Check if form has changes from initial values
  const hasChanges =
    firstName !== (user?.first_name || "") ||
    lastName !== (user?.last_name || "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // At least one field must be provided
    if (!firstName && !lastName) {
      return;
    }

    updateProfile.mutate(
      {
        first_name: firstName || undefined,
        last_name: lastName || undefined,
      },
      {
        onSuccess: (updatedUser) => {
          // Update local state to match new values
          setFirstName(updatedUser.first_name || "");
          setLastName(updatedUser.last_name || "");
        },
      }
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile Information</CardTitle>
        <CardDescription>Update your personal details</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="firstName">First Name</Label>
            <Input
              id="firstName"
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Enter your first name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="lastName">Last Name</Label>
            <Input
              id="lastName"
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Enter your last name"
            />
          </div>

          <Button
            type="submit"
            disabled={!hasChanges || updateProfile.isPending}
            className="w-full sm:w-auto"
          >
            {updateProfile.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              "Save Changes"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
