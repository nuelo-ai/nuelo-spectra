# Debug Session: Sidebar File List Not Showing

**Date:** 2026-02-04
**Phase:** 06-frontend-ui-interactive-data-cards
**Test:** UAT Test 5
**Status:** ✅ ROOT CAUSE FOUND

## Problem Statement

Uploaded files are not appearing in the sidebar file list after upload completes, even though:
- Upload progress shows 0-100%
- Upload completes with "ready" status
- New tab opens automatically

## Expected Behavior

Per Requirements.md sections File-03 to File-06:
- Files should be listed in sidebar after upload
- File list should show file metadata
- Users should be able to interact with uploaded files

## Actual Behavior

- Upload completes successfully
- Progress bar reaches 100%
- New tab opens
- **BUT: Uploaded files do not appear in sidebar file list**

## Impact

Blocks UAT tests 7, 9, and 10 which depend on files being visible in sidebar

## Investigation Steps

### 1. Component Architecture Review
- [ ] Examine FileSidebar component structure
- [ ] Check useFiles hook implementation
- [ ] Review file list refresh/polling logic
- [ ] Verify API integration for file listing

### 2. Data Flow Analysis
- [ ] Check upload completion callback
- [ ] Verify file list state management
- [ ] Check if file list updates trigger after upload
- [ ] Review websocket/polling for real-time updates

### 3. Root Cause Hypotheses
- Missing file list refresh after upload completion?
- State not updating after successful upload?
- API not returning uploaded files?
- Component not re-rendering after state change?

## Investigation Log

### Step 1: Component Architecture Review

**Files examined:**
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/file/FileSidebar.tsx`
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/file/FileUploadZone.tsx`
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/hooks/useFileManager.ts`

**FileSidebar component (FileSidebar.tsx):**
- Line 35: Uses `useFiles()` hook to fetch file list
- Line 94-159: Renders file list when `files && files.length > 0`
- Line 160-166: Shows "No files yet" empty state
- Query invalidation should trigger re-fetch and re-render

**useFiles hook (useFileManager.ts):**
- Lines 12-24: Uses TanStack Query with queryKey `["files"]`
- Line 16: Calls `/files/` API endpoint
- Line 22: Has `refetchOnWindowFocus: true` enabled
- Should automatically refetch when query is invalidated

### Step 2: File Upload Flow Analysis

**FileUploadZone component (FileUploadZone.tsx):**
- Line 22: Gets `queryClient` instance via `useQueryClient()`
- Line 23: Gets `uploadFile` mutation from `useUploadFile()` hook
- Line 78-114: Upload mutation with `onSuccess` callback

**Query invalidation locations:**
1. **useUploadFile hook (useFileManager.ts line 53-56):**
   ```typescript
   onSuccess: () => {
     queryClient.invalidateQueries({ queryKey: ["files"] });
   },
   ```

2. **FileUploadZone onSuccess callback (FileUploadZone.tsx line 87-88):**
   ```typescript
   // Invalidate file list to trigger refresh
   queryClient.invalidateQueries({ queryKey: ["files"] });
   ```

**Observation:** Query invalidation happens in TWO places (duplicate but should be harmless)

### Step 3: Root Cause Discovery

**CRITICAL BUG FOUND in FileUploadZone.tsx lines 34-53:**

```typescript
// Check if analysis is complete
if (uploadStage === "analyzing" && summary?.data_summary) {
  setUploadStage("ready");
  setProgress(100);

  // Auto-close dialog after brief delay
  setTimeout(() => {
    if (uploadedFileId) {
      openTab(uploadedFileId, uploadedFileName);
    }
    if (onUploadComplete) {
      onUploadComplete();
    }
    // Reset state
    setUploadStage("idle");
    setProgress(0);
    setUploadedFileId(null);
    setUploadedFileName("");
  }, 1500);
}
```

**Problems identified:**

1. **❌ This code runs OUTSIDE of a useEffect hook**
   - Executes on EVERY render when condition is true
   - Creates multiple setTimeout calls on each re-render
   - Causes race conditions and unpredictable behavior

2. **❌ State updates trigger immediate re-renders**
   - Line 35: `setUploadStage("ready")` triggers re-render
   - Line 36: `setProgress(100)` triggers another re-render
   - Component re-renders before setTimeout executes
   - Condition `uploadStage === "analyzing"` is false after first render
   - But multiple setTimeout callbacks are already scheduled

3. **❌ Dialog closes before query invalidation completes**
   - Query invalidation happens at upload success (line 88)
   - Dialog closes 1.5 seconds later via setTimeout (line 44)
   - React Query refetch may not complete in this window
   - FileSidebar doesn't re-render with new data

4. **❌ Component unmounts while query is still fetching**
   - Dialog closes → FileUploadZone unmounts
   - FileSidebar may receive data after dialog is already closed
   - If FileSidebar hasn't re-rendered yet, files don't appear

### Step 4: Backend API Verification

**Backend endpoint verified:**
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/routers/files.py` lines 91-106
- GET `/files/` endpoint correctly returns list of FileListItem
- Calls `FileService.list_user_files()` which queries database correctly

**No backend issues found** - the API endpoint is correctly implemented

## ROOT CAUSE

**Primary Issue:** Side effect code (setTimeout with state updates and callbacks) runs in component body instead of useEffect hook in `FileUploadZone.tsx` lines 34-53.

**Consequences:**
1. Multiple setTimeout callbacks are created on each re-render
2. Race conditions between state updates and dialog closure
3. Query invalidation completes but component doesn't wait for refetch
4. FileSidebar doesn't re-render with new file data before dialog closes
5. User sees empty file list even though upload succeeded

**Why files don't appear:**
- Upload completes successfully ✅
- Query invalidation is triggered ✅
- But dialog closes immediately (1.5s timeout) ❌
- FileSidebar query refetch may still be in progress ❌
- Files don't appear in sidebar because refetch completes after user has moved on ❌

## Summary

### Root Cause
Side effect code in `FileUploadZone.tsx` lines 34-53 runs directly in component body instead of being wrapped in `useEffect`. This causes multiple setTimeout callbacks to be scheduled on every re-render, creating race conditions between dialog closure and query refetch completion.

### Affected File
`/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/file/FileUploadZone.tsx`

### Problematic Code Location
Lines 34-53 (the if statement checking `uploadStage === "analyzing" && summary?.data_summary`)

### Technical Details
1. Code executes on every render when condition is met (not in useEffect)
2. State updates (`setUploadStage`, `setProgress`) trigger immediate re-renders
3. Multiple setTimeout callbacks get scheduled from repeated renders
4. Dialog closes via `onUploadComplete()` after 1.5 seconds
5. React Query refetch may not complete before dialog closes
6. FileSidebar doesn't receive updated data in time to re-render

### Fix Strategy (NOT IMPLEMENTED - DIAGNOSIS ONLY)
Wrap the analysis completion logic in a `useEffect` hook that runs when `uploadStage === "analyzing" && summary?.data_summary` becomes true. This will ensure the side effects (setTimeout, state updates, callbacks) only run once when the condition changes, not on every render.

### Related Issues
This bug likely affects:
- UAT Test 5: File upload via click browse (files not listed)
- UAT Test 6: File tab opens (no files listed)
- UAT Test 7: Multiple tabs (can't test without files)
- UAT Test 9: File info modal (no files to click)
- UAT Test 10: Delete file (no files to delete)

