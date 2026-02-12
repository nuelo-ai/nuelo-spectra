# Debug: Drag-Drop Upload Hangs on "Analyzing" Stage

**UAT Tests:** 8, 9, 10 (My Files, ChatInterface, WelcomeScreen drag-drop)
**Symptom:** Drag-drop auto-loads file, upload starts, but progress hangs and never reaches "Ready". Backend confirms analysis completes successfully.
**Key Detail:** Normal uploads (click/browse) work perfectly. Only the `initialFiles` drag-drop path fails.

---

## Root Cause

**React Strict Mode double-mount destroys the TanStack Query mutation observer's connection to the in-flight mutation, causing the inline `onSuccess` callback to never fire.**

### Detailed Mechanism

#### The Drag-Drop Code Path

In `FileUploadZone.tsx`, the `initialFiles` prop triggers an upload via a `useEffect`:

```tsx
// Line 55-56: Guard ref
const initialProcessed = useRef(false);

// Line 117-122: Auto-trigger upload
useEffect(() => {
  if (initialFiles && initialFiles.length > 0 && !initialProcessed.current && uploadStage === "idle") {
    initialProcessed.current = true;
    onDrop(initialFiles);  // Calls uploadFile(file, { onSuccess: ... })
  }
}, [initialFiles, onDrop, uploadStage]);
```

The `onDrop` function calls `uploadFile` (from `useMutation`) with an inline `onSuccess` callback that sets `uploadedFileId` and transitions the stage to "analyzing":

```tsx
// Line 81-111: inside onDrop
uploadFile(
  { file },
  {
    onSuccess: (data) => {
      setUploadedFileId(data.id);       // CRITICAL: enables summary polling
      setUploadStage("analyzing");      // CRITICAL: transitions the UI
    },
  }
);
```

#### The Strict Mode Failure Sequence

Next.js 16 (`next.config.ts` does not set `reactStrictMode: false`) enables React Strict Mode by default. In development, React double-mounts components:

1. **Mount 1 (commit phase):** `useSyncExternalStore` subscribes a listener to the `MutationObserver` instance. `observer.hasListeners()` returns `true`.

2. **Mount 1 (effects phase):** The `useEffect` fires. `initialProcessed.current` is `false`, so it sets it to `true` and calls `onDrop(initialFiles)`. This calls `observer.mutate(file, { onSuccess })`. The HTTP upload request begins. The mutation adds the observer to its observer list.

3. **Strict Mode unmount (cleanup phase):** `useSyncExternalStore` unsubscribes its listener from the observer. Now `observer.hasListeners()` returns `false`. This triggers `MutationObserver.onUnsubscribe()`:

   ```typescript
   // @tanstack/query-core/src/mutationObserver.ts, line 96-100
   protected onUnsubscribe(): void {
     if (!this.hasListeners()) {
       this.#currentMutation?.removeObserver(this)  // <-- DISCONNECTS observer from mutation
     }
   }
   ```

   The observer is **removed from the mutation's observer list**. The HTTP request continues in-flight, but the observer is no longer registered to receive completion notifications.

4. **Mount 2 (commit phase):** `useSyncExternalStore` re-subscribes a listener to the same observer (refs/state survive Strict Mode). Now `observer.hasListeners()` returns `true` again. **But the observer is NOT re-added to the mutation's observer list.** There is no mechanism to do so.

5. **Mount 2 (effects phase):** The `useEffect` re-runs, but `initialProcessed.current` is already `true` (refs persist across Strict Mode mounts), so the guard prevents a second `onDrop` call. No new mutation is triggered.

6. **HTTP upload completes:** The mutation finishes successfully. It dispatches a `success` action and notifies its observers:

   ```typescript
   // @tanstack/query-core/src/mutation.ts, line 389-392
   this.#observers.forEach((observer) => {
     observer.onMutationUpdate(action)
   })
   ```

   But our observer was removed in step 3. **Nobody is notified.** The observer's `#notify` method is never called.

7. **Inline `onSuccess` never fires:** The `#notify` method is the only path to invoke inline callbacks. It also requires `this.hasListeners()` to be true:

   ```typescript
   // @tanstack/query-core/src/mutationObserver.ts, line 164
   if (this.#mutateOptions && this.hasListeners()) {
     // ... fire onSuccess, onError, onSettled
   }
   ```

   Since `#notify` is never called, `setUploadedFileId(data.id)` and `setUploadStage("analyzing")` are **never executed**.

#### Result

- `uploadStage` remains `"uploading"` forever
- `uploadedFileId` remains `null`
- `useFileSummary(null)` is disabled (never polls)
- The progress bar stops at 50% (the simulated upload progress interval caps there)
- The UI shows "Uploading..." with the bar at 50%, visually adjacent to the "Analyzing" label

The user likely reports "stuck on analyzing" because the 50% progress bar is visually at the "Analyzing" label position in the three-stage indicator (Uploading | Analyzing | Ready).

#### Why Normal Uploads Work

When a user clicks "browse" or drops a file directly onto the `FileUploadZone` dropzone:
- The `onDrop` callback fires from a user event handler, not from a `useEffect`
- The component is already stably mounted with the observer properly subscribed
- No Strict Mode double-mount interference occurs
- The mutation completes normally and `onSuccess` fires as expected

---

## Evidence

### File: `frontend/src/components/file/FileUploadZone.tsx`
- **Lines 117-122:** The `useEffect` that auto-triggers `onDrop(initialFiles)` during mount
- **Lines 55-56:** The `initialProcessed` ref guard that prevents re-invocation on Strict Mode remount
- **Lines 81-111:** The `uploadFile` mutation call with inline `onSuccess` that sets critical state
- **Lines 38-40:** `useFileSummary` depends on `uploadedFileId` being set (which never happens)
- **Lines 46-53:** The "analyzing" -> "ready" transition depends on `useFileSummary` returning data (which never starts polling)

### File: `frontend/node_modules/@tanstack/query-core/src/mutationObserver.ts`
- **Lines 96-100:** `onUnsubscribe()` removes observer from mutation when no listeners exist
- **Lines 161-164:** `#notify()` guards inline callback execution with `this.hasListeners()`
- **Lines 128-143:** `mutate()` method stores inline options but doesn't protect against observer disconnection

### File: `frontend/node_modules/@tanstack/query-core/src/mutation.ts`
- **Lines 143-153:** `removeObserver()` removes the observer from the mutation's notification list
- **Lines 389-392:** `#dispatch()` only notifies observers still in the list

### File: `frontend/node_modules/@tanstack/react-query/src/useMutation.ts`
- **Lines 30-36:** Observer created via `useState` (same instance survives Strict Mode)
- **Lines 42-50:** `useSyncExternalStore` subscribes/unsubscribes on mount/unmount

### File: `frontend/next.config.ts`
- No `reactStrictMode: false` override -- Strict Mode is ON by default in Next.js 16

### All three parent components exhibit the same pattern:
- `frontend/src/app/(dashboard)/my-files/page.tsx` (line 153)
- `frontend/src/components/chat/ChatInterface.tsx` (line 349)
- `frontend/src/components/session/WelcomeScreen.tsx` (line 401)

---

## Suggested Fix Direction

The core problem is calling `mutate()` inside a `useEffect` during initial mount, where React Strict Mode's unmount-remount cycle disconnects the observer from the mutation.

**Option A (Recommended): Remove the `initialProcessed` guard and restructure so the second mount's effect can fire the mutation.**

The guard prevents double-upload but also prevents recovery. Instead:
- Use a `useEffect` cleanup function to track whether the first mutation was orphaned
- On remount, detect the orphaned state and re-trigger the upload
- Or use `mutateAsync` and handle the promise directly to set state

**Option B: Move mutation callbacks to hook-level options instead of inline.**

Hook-level `onSuccess` in `useMutation({ onSuccess })` is called from `mutation.execute()` directly (line 246 of `mutation.ts`), NOT through the observer notification path. This bypasses the Strict Mode disconnection issue. However, TanStack Query v5 removed hook-level `onSuccess` from `useMutation`.

**Option C: Use `useRef` to store a flag and `setTimeout(0)` to defer the mutation call past the Strict Mode cycle.**

This is the same pattern already used in `ChatInterface.tsx` (line 127-128):
```tsx
// Uses setTimeout(0) to survive React Strict Mode double-mount cycle
```

Defer the `onDrop(initialFiles)` call with `setTimeout(0)` so it executes after the Strict Mode unmount-remount cycle completes. At that point the observer is stably subscribed and the mutation will work correctly.

**Option D: React to mutation state via `useSyncExternalStore` / observer result instead of inline callbacks.**

Instead of relying on inline `onSuccess`, watch the mutation's `isSuccess` / `data` fields from the hook's return value and use a `useEffect` to transition state. This reads from the observer's snapshot which can be updated via `useSyncExternalStore` if the mutation state is accessible.

---

## Reproduction Conditions

- **Environment:** Development mode (React Strict Mode enabled)
- **Action:** Drag-and-drop a file onto My Files page, ChatInterface area, or WelcomeScreen
- **Result:** Dialog opens, file upload starts, progress bar reaches ~50%, then freezes
- **Expected:** Progress should continue through "Analyzing" to "Ready" with analysis results
