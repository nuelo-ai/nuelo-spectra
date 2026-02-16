# Constraint: Personal Files - Never Update Without Consent

**Created:** 2026-02-15
**Type:** Hard Constraint
**Priority:** Critical

## Files Protected

- `ms-notes.txt`
- `ms-milestone-strategy.md`

## Rules

1. **NEVER read these files** unless explicitly asked by the user
2. **NEVER update these files** unless explicitly asked by the user
3. **NEVER use these files for context or planning**
4. **NEVER commit these files** to git (already in .gitignore)
5. **NEVER push these files** to remote repository
6. These are the user's personal files - hands off completely

## What These Files Are

- `ms-notes.txt`: User's personal notes
- `ms-milestone-strategy.md`: User's personal strategy notes

## Actions Allowed

❌ **Not Allowed:** Reading for context
❌ **Not Allowed:** Reading for planning
❌ **Not Allowed:** Using information from them
❌ **Not Allowed:** Writing/editing
✅ **ONLY Allowed:** When user explicitly says "read ms-notes.txt" or "update ms-milestone-strategy.md"

**Bottom line: Don't touch these files. Period.**

## Git Status

Both files are in `.gitignore` and will never be committed to the repository.
