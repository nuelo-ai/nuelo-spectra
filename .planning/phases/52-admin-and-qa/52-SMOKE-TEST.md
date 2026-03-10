# Phase 52 Smoke Test — Workspace and Pulse Flows

**Version:** v0.8 pre-release
**Date:** (fill in when executing)
**Tester:** (fill in)
**Stack:** backend + frontend + admin-frontend all running locally

---

## Prerequisites

- Running local stack (backend + frontend + admin-frontend)
- Test accounts: one free tier user, one free_trial tier user, one standard tier user
- Admin credentials for the Admin Portal

---

## Flow 1: Tier Access Gating UI

**Goal:** Confirm free tier user cannot access the workspace.

- [ ] Log in as a free tier user
- [ ] Navigate to /workspace
- [ ] Confirm: page shows an access-gated state (upgrade prompt or locked message)
- [ ] Confirm: page does NOT show a 500 error or blank screen
- [ ] Confirm: page does NOT show the Collections list
- [ ] Log out

---

## Flow 2: Collection and Pulse Flow

**Goal:** Confirm the full workspace happy path works end-to-end.

- [ ] Log in as a standard tier user
- [ ] Navigate to /workspace — confirm Collections list page loads
- [ ] Click "Create Collection", enter a name, submit
- [ ] Confirm: new collection card appears in the list with correct name
- [ ] Click the collection card to open the detail page
- [ ] Navigate to the Files tab
- [ ] Upload a CSV file via drag-drop or click
- [ ] Confirm: file row appears in the Files tab with the filename
- [ ] Select the file via checkbox — confirm sticky action bar appears
- [ ] Click "Run Detection (N credits)"
- [ ] Confirm: inline progress banner appears on the Overview tab
- [ ] Wait for detection to complete (30-90 seconds typical)
- [ ] Confirm: global toast notification appears on any page with a link to signals
- [ ] Click the link — confirm navigation to Detection Results page
- [ ] Confirm: at least one Signal card is visible, sorted by severity
- [ ] Click a Signal card — confirm detail panel shows chart + analysis text
- [ ] Navigate to Reports tab — confirm at least one report row appears
- [ ] Click "View Report" — confirm the full-page report viewer opens with markdown content rendered
- [ ] Click "Download Markdown" — confirm browser downloads a .md file

---

## Flow 3: Credit Cost Display

**Goal:** Confirm the Run Detection button shows the live value from platform settings.

- [ ] Log in as a standard tier user
- [ ] Open any collection with files
- [ ] Note the N value shown in "Run Detection (N credits)"
- [ ] In a separate tab, log in to the Admin Portal as admin
- [ ] Navigate to Settings — find the Credits card
- [ ] Note the "Pulse Detection Cost per Run" value
- [ ] Confirm: the button value (N) matches the Admin Portal setting value
- [ ] Log out of both sessions

---

## Flow 4: Admin Settings Round-Trip

**Goal:** Confirm changing workspace_credit_cost_pulse in Admin Portal reflects in the frontend within the cache TTL.

- [ ] Log in to Admin Portal as admin
- [ ] Navigate to Settings — Credits card
- [ ] Note the current "Pulse Detection Cost per Run" value (e.g., 5)
- [ ] Change the value to a different number (e.g., 7)
- [ ] Click Save — confirm success toast appears
- [ ] Log in as a standard tier user (or use existing session in another tab)
- [ ] Navigate to a collection with files
- [ ] Hard-reload the page (Cmd+Shift+R or Ctrl+Shift+R) to bypass browser cache
- [ ] Wait up to 5 minutes for the TanStack Query staleTime to expire, then reload again
- [ ] Confirm: "Run Detection (N credits)" now shows the new value (7)
- [ ] (Cleanup) Return to Admin Portal and restore the value to 5
- [ ] Confirm: after another reload/wait, the button shows 5 again
