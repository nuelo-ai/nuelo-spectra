---
status: resolved
trigger: "Upload file modal (FileUploadZone dialog) is too narrow compared to FileContextModal"
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T00:00:00Z
---

## Current Focus

hypothesis: Upload dialog uses sm:max-w-lg while FileContextModal uses sm:max-w-4xl -- inconsistent sizing
test: Compare DialogContent className across all upload dialog instances vs FileContextModal
expecting: Upload dialogs are narrower than info modals
next_action: Document findings for fix

## Symptoms

expected: Upload modal and FileContextModal should have consistent widths
actual: Upload modal is noticeably narrower than FileContextModal (the (i) info modal)
errors: None (visual inconsistency, not a runtime error)
reproduction: Go to My Files page, drag-drop a file (observe upload modal width), then click (i) on a file (observe wider info modal)
started: Since upload modal was first created

## Eliminated

(none -- root cause found on first hypothesis)

## Evidence

- timestamp: 2026-02-12
  checked: FileContextModal.tsx line 60
  found: `<DialogContent className="sm:max-w-4xl max-h-[85vh] overflow-y-auto">`
  implication: Info modal uses `sm:max-w-4xl` (max-width: 56rem / 896px)

- timestamp: 2026-02-12
  checked: dialog.tsx (base DialogContent component) line 64
  found: Default className includes `sm:max-w-lg` (max-width: 32rem / 512px)
  implication: Any DialogContent without an override inherits sm:max-w-lg

- timestamp: 2026-02-12
  checked: my-files/page.tsx line 149
  found: `<DialogContent className="sm:max-w-lg">` wrapping FileUploadZone
  implication: My Files page upload dialog explicitly sets sm:max-w-lg (same as default, so redundant but narrow)

- timestamp: 2026-02-12
  checked: WelcomeScreen.tsx lines 385, 409
  found: Both upload dialogs use `<DialogContent className="sm:max-w-lg">`
  implication: WelcomeScreen upload dialogs are also narrow

- timestamp: 2026-02-12
  checked: ChatInterface.tsx line 343
  found: `<DialogContent className="sm:max-w-lg">` wrapping FileUploadZone
  implication: ChatInterface upload dialog is also narrow

- timestamp: 2026-02-12
  checked: FileLinkingDropdown.tsx line 187
  found: `<DialogContent className="sm:max-w-lg">` wrapping FileUploadZone
  implication: FileLinkingDropdown upload dialog is also narrow

- timestamp: 2026-02-12
  checked: FileSidebar.tsx line 190
  found: `<DialogContent className="sm:max-w-4xl max-h-[85vh] overflow-y-auto">` wrapping FileUploadZone
  implication: FileSidebar upload dialog ALREADY uses the correct wider size -- inconsistency even among upload dialogs

- timestamp: 2026-02-12
  checked: FileUploadZone.tsx lines 222-228 (markdown rendering)
  found: Uses `<ReactMarkdown remarkPlugins={[remarkGfm]}>{analysisText}</ReactMarkdown>` inside `<div className="prose prose-sm max-w-none dark:prose-invert">`
  implication: Markdown rendering setup is IDENTICAL to FileContextModal.tsx (lines 82-85). Both use react-markdown + remark-gfm + prose classes. The @tailwindcss/typography plugin is properly installed and configured in globals.css. Markdown rendering should work correctly.

- timestamp: 2026-02-12
  checked: package.json and globals.css
  found: `@tailwindcss/typography` v0.5.19 installed, `@plugin "@tailwindcss/typography"` in globals.css line 2
  implication: Typography plugin is correctly wired for Tailwind v4. Prose classes should render markdown properly.

## Resolution

root_cause: |
  **Width inconsistency:** 4 out of 5 upload dialog instances use `sm:max-w-lg` (512px) while the
  FileContextModal uses `sm:max-w-4xl` (896px). This creates a noticeable size discrepancy.
  The FileSidebar upload dialog already uses the correct `sm:max-w-4xl` -- proving this is an oversight
  in the other 4 locations, not a deliberate design choice.

  **Markdown rendering:** NOT a bug. The FileUploadZone uses the exact same ReactMarkdown + remarkGfm +
  prose class setup as FileContextModal. The `@tailwindcss/typography` plugin is properly installed and
  configured. If markdown appears "not rendering," it may be because the narrow `sm:max-w-lg` dialog
  constrains the content, making tables and other wide markdown elements look broken or cramped.
  Widening the modal to `sm:max-w-4xl` should resolve any perceived markdown rendering issues.

fix: |
  Change `sm:max-w-lg` to `sm:max-w-4xl max-h-[85vh] overflow-y-auto` in these 4 locations:

  1. frontend/src/app/(dashboard)/my-files/page.tsx line 149
  2. frontend/src/components/session/WelcomeScreen.tsx line 385
  3. frontend/src/components/session/WelcomeScreen.tsx line 409
  4. frontend/src/components/chat/ChatInterface.tsx line 343
  5. frontend/src/components/file/FileLinkingDropdown.tsx line 187

verification: Pending -- changes not yet applied
files_changed:
  - frontend/src/app/(dashboard)/my-files/page.tsx
  - frontend/src/components/session/WelcomeScreen.tsx
  - frontend/src/components/chat/ChatInterface.tsx
  - frontend/src/components/file/FileLinkingDropdown.tsx
