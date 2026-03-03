---
phase: quick-2
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - requirements/Spectra-Pulse-Requirement.md
autonomous: true
requirements: [QUICK-2]

must_haves:
  truths:
    - "Spectra-Pulse-Requirement.md exists in requirements/ folder"
    - "Document faithfully transcribes product requirements from brainstorm-idea-1.md"
    - "Milestone/implementation strategy sections are excluded"
    - "Competitive landscape sections are excluded"
    - "Future exploration sections (Monitoring appendix, Persistent AI Memory, Predictive ML appendix) are excluded"
    - "No requirements are adjusted, improved, or editorially changed"
  artifacts:
    - path: "requirements/Spectra-Pulse-Requirement.md"
      provides: "End-to-end product requirements summary for Spectra Pulse (Frontend and Admin)"
      min_lines: 200
  key_links: []
---

<objective>
Create `requirements/Spectra-Pulse-Requirement.md` that summarizes the end-to-end product requirements (Frontend and Admin) from the brainstorm document (`requirements/brainstorm-idea-1.md`).

Purpose: Provide a clean, focused product requirements reference that strips away strategic/competitive/milestone content, keeping only what defines what to build and how it should work.

Output: `requirements/Spectra-Pulse-Requirement.md`
</objective>

<execution_context>
@/Users/marwazisiagian/.claude/get-shit-done/workflows/execute-plan.md
@/Users/marwazisiagian/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@requirements/brainstorm-idea-1.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create Spectra-Pulse-Requirement.md from brainstorm source</name>
  <files>requirements/Spectra-Pulse-Requirement.md</files>
  <action>
Read `requirements/brainstorm-idea-1.md` in full. Create `requirements/Spectra-Pulse-Requirement.md` that faithfully transcribes the product requirements content.

**INCLUDE these sections (transcribe faithfully, preserve all detail, tables, data model fields, method descriptions):**

1. **Decisions Log** — The blockquoted decisions at the top (items 1-8). Include as-is since they provide binding context for requirements.

2. **The Problem** — The problem statement and analytics maturity curve description.

3. **Naming: "Spectra Pulse"** — The confirmed naming decision, the naming table, and the terminology (Pulse = detection stage, Signals = individual findings).

4. **Product Architecture: Two Modules, One Platform** — Module 1 (Chat Sessions), Module 2 (Analysis Workspace), Module 3 (Monitoring - deferred note), Platform Architecture diagram, and the comparison table (Chat Sessions vs Analysis Workspace).

5. **Data Model: Collections as Workspace** — The full revised data model including the ER diagram with ALL entity definitions (Collection, File, Signal, Investigation, Root_Cause, Scenario, Chat_Item, Report) and ALL fields. Include the key relationships list.

6. **Core UX Principles** — The 4 principles from the Apple PM Assessment section (progressive disclosure, Q&A flow, Collections as output, AI-guided scenarios). Extract these principles only, not the assessment framing.

7. **The User Journey (end to end)** — The full flow diagram and all 4 steps with their deliverables:
   - Step 1: Start an Analysis (deliverable: Signals)
   - Step 2: Guided Investigation (deliverable: Root Cause Hypothesis)
   - Step 3: What-If Scenarios (deliverable: Scenario Comparison) — include all 4 phases, the comparison table (old vs new approach), and design principles
   - Step 4: Save to Collections

8. **Statistical Methods by Stage** — All 3 stages in full:
   - Stage 1: PULSE (Signal Identification) — all methods table, signal classification, "no signals" behavior
   - Stage 2: EXPLAIN (Root Cause & Diagnostic) — all methods table, Q&A exchange mapping table
   - Stage 3: WHAT-IF (AI-Driven Scenario Exploration) — agent capabilities table, design principles

9. **Method Availability by Data Shape** — The full data characteristic / methods enabled-disabled table and the note about What-If flexibility.

10. **Library Requirements (E2B Sandbox)** — The package table with "Already in Spectra?" column.

11. **Critical Challenges & Honest Assessment** — All 6 challenges faithfully transcribed.

12. **Admin Portal: Analysis Workspace Management** — All subsections:
    - 1. Tier-Based Access & Collection Limits (table, key design decisions, proposed user_classes.yaml extension)
    - 2. Granular Credit Costs per Workspace Activity (cost table, implementation approach, credit transparency)
    - 3. Admin Monitoring & Analytics (3a dashboard metrics, 3b per-user activity, 3c activity log with field table, 3d alerts)

13. **Why Spectra, Not ChatGPT/Claude?** — The full section including the 5 breakdown points and positioning table.

14. **Practicality Notes** — The buildability, testability, and risks sections.

**EXCLUDE these sections entirely (do NOT include any content from):**
- Business Executive Assessment (evaluative framing, not requirements)
- Apple PM Assessment framing text (only extract the 4 UX Principles from within it)
- Revised Milestone Sequence (milestone/implementation strategy)
- Scope per Milestone tables (milestone/implementation strategy)
- Competitive Landscape and all subsections (competitive analysis)
- Appendix: Monitoring Module (future exploration - deferred)
- Future Exploration: Persistent AI Memory System (future exploration)
- Appendix: Predictive ML Model Platform (future exploration)

**Formatting rules:**
- Use a clear title: `# Spectra Pulse — Product Requirements`
- Add a one-line note at the top: `> Extracted from brainstorm-idea-1.md. Product requirements only — excludes milestone strategy, competitive landscape, and future exploration sections.`
- Preserve original section hierarchy but renumber/restructure for clean flow
- Preserve all mermaid diagrams, tables, code blocks, and yaml blocks exactly as they appear in the source
- Preserve all blockquoted decision notes and revision notes
- Do NOT rephrase, summarize, improve, or editorialize any content — transcribe faithfully
- Do NOT add commentary like "this is important" or "note that..."
  </action>
  <verify>
    <automated>test -f requirements/Spectra-Pulse-Requirement.md && wc -l requirements/Spectra-Pulse-Requirement.md | awk '{if ($1 > 200) print "PASS: " $1 " lines"; else print "FAIL: only " $1 " lines"}'</automated>
  </verify>
  <done>
    - requirements/Spectra-Pulse-Requirement.md exists
    - Contains all 14 included sections with faithful transcription
    - Excludes milestone strategy, competitive landscape, and future exploration content
    - All tables, diagrams, code blocks, and yaml preserved exactly
    - No editorial changes to requirements content
  </done>
</task>

</tasks>

<verification>
- File exists at `requirements/Spectra-Pulse-Requirement.md`
- File is >200 lines (source product sections are substantial)
- Spot-check: Data model entities match source exactly
- Spot-check: Statistical methods tables match source exactly
- Spot-check: Admin Portal credit cost table matches source exactly
- No mention of milestone sequence, competitive landscape companies, or appendix modules
</verification>

<success_criteria>
A clean product requirements document that a developer or product owner can reference without wading through competitive analysis, milestone planning, or future exploration content. All product requirements faithfully preserved from the brainstorm source.
</success_criteria>

<output>
After completion, create `.planning/quick/2-create-spectra-pulse-requirement-md-summ/2-SUMMARY.md`
</output>
