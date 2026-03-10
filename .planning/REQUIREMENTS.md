# Requirements: Spectra v0.8.1

**Defined:** 2026-03-10
**Core Value:** Accurate data analysis through correct, safe Python code generation

## v0.8.1 Requirements

Requirements for v0.8.1 UI Fixes & Enhancement. Phases continue from v0.8 (last phase: 52.1).

### Leftbar

- [x] **LBAR-01**: Leftbar collapse toggle is visible when Pulse Analysis is selected (positioned at top left of main screen next to the leftbar)
- [x] **LBAR-02**: Menu items (Pulse Analysis, Chat, Files, Admin Panel) have correct left padding aligned with other icons

### Pulse Analysis

- [x] **PULSE-01**: Credit Used card on Collection Overview reflects actual credits used after pulse runs (not stuck at "5")
- [x] **PULSE-02**: Signal View is mobile responsive — Signal detail panel is accessible on small screens (not hidden behind signals list)
- [x] **PULSE-03**: "Chat with Spectra" button appears between Analysis and Statistical Evidence sections on Signal View, opening a new Chat session with the collection's files pre-linked
- [x] **PULSE-04**: Activity history list displays both date and time per entry
- [x] **PULSE-05**: File added list displays both date and time per entry

### Chat

- [x] **CHAT-01**: Spectra logo is not shown in the top left of the Chat main panel when Chat section is selected
- [x] **CHAT-02**: Chat dashboard (new chat) rightbar expand toggle is visible after the rightbar is collapsed (positioned at top right of the chat area)
- [x] **CHAT-03**: Chat screen (existing chat) rightbar collapse/expand toggle is positioned at top right of the chat area (not top middle)

### Files

- [x] **FILES-01**: Spectra logo is not shown in the top left of the Files main panel when Files section is selected
- [x] **FILES-02**: Leftbar collapse toggle is in the correct position in Files section (at top of main screen next to leftbar)

## Future Requirements

(None for this patch milestone)

## Out of Scope

| Feature | Reason |
|---------|--------|
| New features (Explain, What-If) | v0.9+ implementation milestones |
| Backend API changes | v0.8.1 is UI-only fixes |
| New Pulse pipeline capabilities | Next milestone scope |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LBAR-01 | Phase 53 | Complete |
| LBAR-02 | Phase 53 | Complete |
| CHAT-01 | Phase 53 | Complete |
| CHAT-02 | Phase 53 | Complete |
| CHAT-03 | Phase 53 | Complete |
| FILES-01 | Phase 53 | Complete |
| FILES-02 | Phase 53 | Complete |
| PULSE-01 | Phase 54 | Complete |
| PULSE-02 | Phase 54 | Complete |
| PULSE-03 | Phase 54 | Complete |
| PULSE-04 | Phase 54 | Complete |
| PULSE-05 | Phase 54 | Complete |

**Coverage:**
- v0.8.1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-10*
*Last updated: 2026-03-10 — traceability updated after roadmap creation (phases 53-54)*
