# Debug Session: File Upload Analysis Visibility

**Session ID:** file-upload-analysis-visibility
**Created:** 2026-02-04
**Goal:** find_root_cause_only (diagnosis for UAT gap closure)

## Problem Statement

**What's broken (Truth):** After file upload completes, user can see onboarding analysis result as defined in REQUIREMENTS.md FILE-03 through FILE-06

**Expected Behavior:**
In dashboard sidebar, click Upload button. Drag a CSV or Excel file onto dropzone. See progress: Uploading (0-50%) → Analyzing (50-80%) → Ready (100%, green checkmark). Dialog auto-closes and new tab opens.

**Actual Behavior:**
User reported: "partially pass. User can click the upload, a modal shown, user can select the file or drag the file to upload, the progress bar show from 0 to 100%, it shows ready at the end, the new tab opens, however, user should be able to see the analysis result as defined in the Requirements.md file section File Management (File 03 until file-06)"

**Reproduction:** Test 4 in UAT (.planning/phases/06-frontend-ui-interactive-data-cards/06-UAT.md)

**Timeline:** Discovered during Phase 6 UAT

## Investigation

### Step 1: Understanding Requirements

From `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/.planning/REQUIREMENTS.md`:

- **FILE-03**: System validates file format and structure before acceptance ✅ (working)
- **FILE-04**: AI Onboarding Agent analyzes uploaded data structure and generates natural language summary ✅ (working - analysis happens)
- **FILE-05**: User can provide optional context during upload to improve AI interpretation ✅ (backend supports it)
- **FILE-06**: User can refine AI's understanding of the data after initial analysis ✅ (POST /files/{file_id}/context exists)

### Step 2: Understanding Current Implementation

**Backend Flow** (from `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/routers/files.py`):
1. POST /files/upload accepts file
2. Triggers background task `_run_onboarding_background` (line 77-86)
3. Onboarding agent analyzes file and populates `data_summary` field
4. GET /files/{file_id}/summary endpoint returns the analysis (line 216-249)

**Frontend Flow** (from multiple files):
1. User uploads file via FileUploadZone
2. Progress shows: Uploading (0-50%) → Analyzing (50-80%) → Ready (100%)
3. Component polls for `data_summary` via `useFileSummary` hook
4. When analysis completes, dialog auto-closes after 1.5s
5. New tab opens showing ChatInterface
6. **BUT: Analysis result is NEVER displayed automatically**

**Where Analysis Can Be Viewed:**
The only way to see the analysis is via FileInfoModal (from `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/file/FileInfoModal.tsx`):
- User must click the info icon (ⓘ) next to filename in sidebar
- Modal displays `data_summary` and `user_context`

### Step 3: Design Intent vs User Expectation

**Phase 6 Design** (from `.planning/phases/06-frontend-ui-interactive-data-cards/06-CONTEXT.md` lines 29-32):
```
File Information Display:
- Info icon (ⓘ) next to each filename in sidebar
- Clicking info icon opens modal dialog (center of screen) showing onboarding analysis
- Modal displays the AI's data summary from initial upload
```

**UAT Expectation** (from `.planning/phases/06-frontend-ui-interactive-data-cards/06-UAT.md` line 38):
```
expected: In dashboard sidebar, click Upload button. Drag a CSV or Excel file onto dropzone.
See progress: Uploading (0-50%) → Analyzing (50-80%) → Ready (100%, green checkmark).
Dialog auto-closes and new tab opens.

User should be able to see the analysis result as defined in Requirements.md FILE-03 through FILE-06
```

### Step 4: Root Cause Analysis

**Gap Identified:**
The Phase 6 design assumes users know to click the info icon to see the analysis. However:
1. There's no visual indication that an analysis is available
2. No onboarding/guidance tells users the info icon exists
3. The upload flow shows "Ready!" and auto-closes without showing the analysis
4. FILE-04 requirement says "AI Onboarding Agent analyzes uploaded data structure and generates natural language summary" - users interpret this as "I should SEE the summary after upload"
5. The ChatInterface empty state says "Ask a question about your data to get started" but never mentions the analysis that was just performed

**Why This Happens:**
The FileUploadZone component (lines 35-53 in FileUploadZone.tsx) does this:
```typescript
if (uploadStage === "analyzing" && summary?.data_summary) {
  setUploadStage("ready");
  setProgress(100);

  // Auto-close dialog after brief delay
  setTimeout(() => {
    if (uploadedFileId) {
      openTab(uploadedFileId, uploadedFileName);  // Just opens tab
    }
    if (onUploadComplete) {
      onUploadComplete();  // Closes dialog
    }
    // Reset state
    ...
  }, 1500);
}
```

It never displays the `summary.data_summary` content that was just fetched.

## ROOT CAUSE FOUND

**Problem:** After file upload completes and onboarding analysis finishes, the analysis result is never shown to the user automatically.

**Technical Root Cause:**
The FileUploadZone component successfully:
1. ✅ Polls for analysis completion via `useFileSummary` hook
2. ✅ Detects when `data_summary` is available
3. ✅ Updates progress to 100% and shows "Ready!" state
4. ❌ **NEVER displays the analysis content before closing**

Code location: `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/frontend/src/components/file/FileUploadZone.tsx` (lines 35-53)

**User Experience Gap:**
After upload completes:
- Upload dialog closes automatically
- New tab opens showing ChatInterface with empty state ("Ask a question about your data to get started")
- User has no indication that:
  - An AI analysis was performed
  - Where to find the analysis
  - That clicking info icon (ⓘ) in sidebar will show it

**Missing UX Elements:**
1. No display of analysis result in the upload flow (between "Ready!" and auto-close)
2. No visual indicator in ChatInterface that analysis is available
3. No prompt/tooltip suggesting "View AI analysis" after upload
4. No onboarding to explain the info icon purpose

**Requirements Interpretation:**
- FILE-04 says "AI Onboarding Agent analyzes uploaded data structure and generates natural language summary"
- Users reasonably expect to SEE this summary after analysis completes
- Current implementation satisfies the technical requirement (analysis happens) but fails user expectation (seeing the result)

**Impact:**
Users don't know:
- What the AI learned about their data
- If the analysis succeeded
- What insights are available before they ask questions
- That the info icon provides this information

**Fix Direction (not implemented, just diagnosis):**
Option A: Show analysis in upload dialog before auto-closing
Option B: Auto-open FileInfoModal after upload completes
Option C: Display analysis as first message in ChatInterface
Option D: Add prominent banner in ChatInterface pointing to analysis

---

**Debug Session Complete**
Status: Root cause identified
Next: Gap closure plan needed

