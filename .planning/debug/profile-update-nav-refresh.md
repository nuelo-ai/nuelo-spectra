# Debug Session: Profile Update Not Reflecting in Top Nav

**Date:** 2026-02-04
**Phase:** 06-frontend-ui-interactive-data-cards
**Test:** UAT Test 23
**Severity:** minor

## Problem Statement

After updating profile (first name/last name) in Settings page, changes appear successfully but do NOT update in the top navigation immediately. User must refresh page to see changes.

**Expected Behavior:**
1. User edits first name and/or last name in Profile section
2. Click Save Changes
3. See success toast "Profile updated successfully"
4. Changes appear in top nav immediately (without page refresh)

**Actual Behavior:**
- Profile update succeeds
- Success toast appears
- Top nav shows OLD name until page refresh

## Investigation Plan

1. Find the profile update mutation code
2. Check TanStack Query invalidation after update
3. Examine useAuth hook and user context
4. Verify top nav data source and refresh mechanism
5. Identify the missing link in the refresh chain

## Code Investigation

### Step 1: Profile Update Flow

**File:** `/frontend/src/hooks/useSettings.ts`
**Function:** `useUpdateProfile()`

```typescript
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ProfileUpdateRequest) => {
      const response = await apiClient.patch("/auth/me", data);
      // ... error handling ...
      return (await response.json()) as UserResponse;
    },
    onSuccess: (updatedUser) => {
      // Invalidate user query to refetch latest data
      queryClient.invalidateQueries({ queryKey: ["user"] });
      toast.success("Profile updated successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update profile");
    },
  });
}
```

**Key Finding:** The mutation invalidates `queryKey: ["user"]` after successful update.

### Step 2: Profile Form Component

**File:** `/frontend/src/components/settings/ProfileForm.tsx`

```typescript
export function ProfileForm() {
  const { user } = useAuth();
  const updateProfile = useUpdateProfile();

  // ... form state ...

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
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

  // ...
}
```

**Key Finding:** Form uses `useAuth()` to get user data.

### Step 3: Authentication Context

**File:** `/frontend/src/hooks/useAuth.tsx`

```typescript
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Load user on mount if tokens exist
  useEffect(() => {
    async function loadUser() {
      if (checkAuth()) {
        try {
          const response = await apiClient.get("/auth/me");
          if (response.ok) {
            const userData: UserResponse = await response.json();
            setUser(userData);
          } else {
            clearTokens();
          }
        } catch (error) {
          clearTokens();
        }
      }
      setIsLoading(false);
    }

    loadUser();
  }, []);

  // ... login, signup, logout methods ...

  const value = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    signup,
    logout,
    forgotPassword,
    resetPassword,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
```

**CRITICAL FINDING:**
- `AuthProvider` uses **React Context** with local `useState` for user data
- User is loaded ONLY on mount (in `useEffect` with empty dependency array)
- User state is NEVER updated after initial load
- User state is NOT managed by TanStack Query

### Step 4: Top Navigation User Display

**File:** `/frontend/src/app/(dashboard)/layout.tsx`

```typescript
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user, logout } = useAuth();

  // Get user initials for avatar
  const getInitials = () => {
    if (!user) return "U";
    const firstInitial = user.first_name?.[0] || "";
    const lastInitial = user.last_name?.[0] || "";
    if (firstInitial || lastInitial) {
      return (firstInitial + lastInitial).toUpperCase();
    }
    return user.email[0].toUpperCase();
  };
  const initials = getInitials();

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-14 items-center justify-between px-4">
          {/* ... */}
          <DropdownMenuLabel>
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium leading-none">
                {user?.first_name || user?.last_name
                  ? `${user.first_name || ""} ${user.last_name || ""}`.trim()
                  : "User"}
              </p>
              <p className="text-xs leading-none text-muted-foreground">
                {user?.email}
              </p>
            </div>
          </DropdownMenuLabel>
          {/* ... */}
        </div>
      </header>
      {/* ... */}
    </div>
  );
}
```

**Key Finding:** Top nav displays user name from `useAuth()` context.

## Root Cause Analysis

### The Disconnect

1. **Profile Update Flow:**
   - User submits profile update
   - `useUpdateProfile()` mutation calls API: `PATCH /auth/me`
   - On success: `queryClient.invalidateQueries({ queryKey: ["user"] })`
   - Toast shows: "Profile updated successfully"

2. **The Problem:**
   - `queryClient.invalidateQueries({ queryKey: ["user"] })` is called
   - BUT there is NO TanStack Query with `queryKey: ["user"]` in the codebase
   - The invalidation is targeting a query that DOESN'T EXIST

3. **User Data Management:**
   - User data is stored in React Context (`AuthProvider`)
   - User state is local `useState`, NOT TanStack Query
   - User is loaded once on mount, never refreshed
   - AuthProvider has no mechanism to listen for query invalidations

4. **Top Navigation:**
   - Reads user data from `useAuth()` context
   - Context state is never updated after profile change
   - Shows stale data until page refresh (which remounts AuthProvider)

### Architecture Mismatch

```
Profile Update:
  useUpdateProfile() → API → invalidates ["user"] query
                                    ↓
                             (No query exists!)
                                    ↓
                               Does nothing

Top Navigation:
  useAuth() → AuthContext → useState (never updated)
                               ↓
                        Displays stale data
```

## ROOT CAUSE

**The user data is managed in two incompatible ways:**

1. **Settings mutation** expects user data to be managed by TanStack Query and tries to invalidate `queryKey: ["user"]`
2. **AuthProvider** manages user data with React Context and `useState`, which is completely independent of TanStack Query
3. The query invalidation does nothing because no such query exists
4. The AuthProvider never updates its state after the initial load
5. Top navigation displays stale data from the unchanged context

**The disconnect:** The profile update successfully invalidates a non-existent query, while the actual user state in React Context remains unchanged.

## Verification

Searched entire codebase for TanStack Query usage with user data:
```bash
grep -r "useQuery.*user\|queryKey.*user" frontend/src/**/*.{ts,tsx}
```

**Result:** Only ONE occurrence found:
- `/frontend/src/hooks/useSettings.ts:35` - the invalidation call
- NO `useQuery` with `queryKey: ["user"]` exists anywhere

This confirms that:
1. No TanStack Query manages user data
2. The invalidation has no effect
3. AuthProvider's React Context state is the sole source of truth
4. That state is never updated after initial mount

## Summary

**ROOT CAUSE:** Architecture mismatch between data management approaches.

- User data is stored in React Context with `useState` (AuthProvider)
- Profile update mutation attempts to invalidate a TanStack Query that doesn't exist
- Top navigation reads from React Context, which never updates after profile changes
- Page refresh works because it remounts AuthProvider and fetches fresh user data

**Solution paths:**
1. Make AuthProvider update its state when profile changes (add method to context)
2. Migrate user data management from React Context to TanStack Query
3. Have mutation directly update AuthProvider's state via callback/event

**Files involved:**
- `/frontend/src/hooks/useAuth.tsx` - AuthProvider with stale state
- `/frontend/src/hooks/useSettings.ts` - useUpdateProfile with ineffective invalidation
- `/frontend/src/app/(dashboard)/layout.tsx` - Top nav displaying stale data
- `/frontend/src/components/settings/ProfileForm.tsx` - Profile update form
