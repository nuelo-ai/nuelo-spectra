# Constraint: Personal Files - Never Update Without Consent

**Created:** 2026-02-15
**Type:** Hard Constraint
**Priority:** Critical

## Files Protected

- `ms-notes.txt`
- `ms-milestone-strategy.md`

## Rules

1. **NEVER update these files** without explicit user consent
2. **NEVER commit these files** to git (already in .gitignore)
3. **NEVER push these files** to remote repository
4. These are the user's personal planning and notes files

## What These Files Are

- `ms-notes.txt`: Personal development notes, error logs, troubleshooting
- `ms-milestone-strategy.md`: Personal milestone planning strategy and versioning decisions

## If User Asks to Update

✅ **Allowed:** Reading these files to understand context
✅ **Allowed:** Using information from these files for planning
❌ **Not Allowed:** Writing/editing without explicit permission

Always ask: "Would you like me to update [filename]?" before making changes.

## Git Status

Both files are in `.gitignore` and will never be committed to the repository.
