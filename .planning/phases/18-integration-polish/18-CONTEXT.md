# Phase 18: Integration & Polish - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

All v0.3 features work together seamlessly with proper constraints and visual polish. This phase delivers: file-required enforcement before chatting, session title auto-generation, light/dark theme support, and session persistence verification. No new capabilities — this is integration and polish of Phases 14-17.

</domain>

<decisions>
## Implementation Decisions

### File requirement UX
- Input field stays enabled (user can type), but sending is blocked when no files are linked
- On send attempt without files: toast notification for immediate feedback + inline warning below input that persists until a file is linked
- Prevent removing the last file from a session — show warning: "At least one file must be linked" when user tries to unlink the only remaining file
- WelcomeScreen stays as-is — file requirement only enforced on message send, not preemptively on the welcome screen

### Session title generation
- Use LLM to generate session titles — send first user message to LLM with a title-generation prompt
- Title is generated after the first AI response completes (more context available for meaningful title)
- Sidebar shows "Untitled" as placeholder until the LLM-generated title arrives
- Manual rename locks the title — auto-generation never overwrites a user-set title

### Dark mode design
- Toggle located inside user profile/menu dropdown — not in sidebar or navbar directly
- System preference detection: default to OS/system theme on first visit, user can override
- Two options only: Light / Dark (no explicit "System" option — system preference used only for initial default)
- Theme preference persistence: Claude's Discretion (localStorage vs backend based on existing patterns)
- **UI directive:** Use `/frontend-design` skill for all UI work in this phase

### Session persistence & login behavior
- On login: always start with a new empty session — previous sessions accessible from sidebar history
- Sessions must survive page refresh and re-login with all messages and linked files intact

### Claude's Discretion
- Sidebar session item design (title + time vs title + file count)
- Session limit strategy (unlimited vs soft limit with cleanup)
- Theme persistence mechanism (localStorage vs backend user profile)
- Loading/transition animations during theme switch
- Dark mode color palette specifics

</decisions>

<specifics>
## Specific Ideas

- File requirement: "Both toast + inline" pattern — toast for immediate attention, inline for persistent guidance until resolved
- Similar to ChatGPT's behavior where you can type but the system guides you to add context before meaningful interaction
- Always use `/frontend-design` skill when planning and implementing UI components in this phase

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-integration-polish*
*Context gathered: 2026-02-11*
