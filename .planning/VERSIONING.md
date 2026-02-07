# Versioning & Release Strategy

**Project:** Spectra
**Strategy:** Development Branch with Semantic Versioning
**Last Updated:** 2026-02-06

---

## Versioning Scheme

Spectra uses **semantic versioning** with a beta phase:

```
v0.1, v0.2, v0.3, ... → v1.0 → v1.1, v1.2, ... → v2.0
```

### Version Meaning

- **v0.x (Beta):** Pre-1.0 releases, beta testing, rapid iteration
  - v0.1: Initial beta MVP
  - v0.2: Intelligence & Integration
  - v0.3+: Incremental feature additions
  - Breaking changes acceptable in beta (user expectations managed)

- **v1.0 (Stable):** First production-ready release
  - Feature-complete
  - Polished UI/UX
  - Remove "beta" label
  - Backward compatibility commitment begins

- **v1.x (Minor):** Feature additions, non-breaking changes
  - v1.1, v1.2, v1.3, etc.
  - New features
  - Enhancements
  - Backward compatible

- **v2.0+ (Major):** Breaking changes, major rewrites
  - Architecture changes
  - Breaking API changes
  - Migration guides required

### Hotfix Versions

For critical bugs in released versions:

```
v0.1.1, v0.1.2, v1.0.1, v1.0.2, etc.
```

---

## Branch Strategy

### Branch Structure

```
master    →  Stable releases only (v0.1, v0.2, v1.0, etc.)
develop   →  Active development for next version
hotfix/*  →  Emergency fixes for current stable version (if needed)
```

### Branch Purposes

| Branch | Purpose | Protected | Tags |
|--------|---------|-----------|------|
| `master` | Production-ready code, always stable | ✅ Yes | All version tags (v0.1, v0.2, etc.) |
| `develop` | Active development for next milestone | ❌ No | Pre-release tags (v0.2-beta, optional) |
| `hotfix/*` | Emergency fixes for current release | ❌ No | Hotfix tags (v0.1.1, v0.1.2) |

---

## Development Workflow

### Starting New Milestone

When starting a new milestone (e.g., v0.2):

```bash
# 1. Ensure current release is tagged
git checkout master
git tag v0.1  # if not already tagged
git push origin v0.1

# 2. Create develop branch from master
git checkout -b develop

# 3. Push develop branch to remote
git push -u origin develop

# 4. All GSD phases work on develop
/gsd:plan-phase 7
/gsd:execute-phase 7
# ... all Phase 7-11 commits go to develop ...

# Develop branch accumulates all phase work
```

### During Development

**All GSD commands execute on `develop` branch:**

```bash
# Verify you're on develop
git branch --show-current  # should show "develop"

# Normal GSD workflow
/gsd:plan-phase 7
/gsd:execute-phase 7
/gsd:verify-phase 7

# All commits automatically go to develop
# GSD atomic commits continue as normal
```

### Releasing New Version

When milestone is complete and tested:

```bash
# 1. Ensure all work is committed on develop
git checkout develop
git status  # should be clean

# 2. Run final milestone audit
/gsd:audit-milestone v0.2

# 3. Switch to master and merge
git checkout master
git merge develop --no-ff  # create merge commit for clarity

# 4. Tag the release
git tag v0.2
git tag -a v0.2 -m "Release v0.2: Intelligence & Integration

Features:
- AI agent memory persistence (12K token window)
- Multi-LLM provider support (Ollama + OpenRouter)
- Smart query suggestions (5-6 grouped)
- Web search tool integration (Serper.dev)
- Production SMTP email infrastructure

43 requirements completed across 5 phases (Phases 7-11).
5 days development time (Feb 7-12, 2026)."

# 5. Push master and tags
git push origin master
git push origin v0.2

# 6. Update MILESTONES.md with release notes
# (GSD handles this via /gsd:complete-milestone)

# 7. Optionally delete develop branch
git branch -d develop
git push origin --delete develop

# 8. For next milestone, create new develop branch from master
git checkout -b develop
```

---

## Hotfix Workflow

If critical bug found in stable release (v0.1) while developing v0.2:

### Option A: Quick Hotfix (Simple Bug)

```bash
# 1. Create hotfix branch from master
git checkout master
git checkout -b hotfix/v0.1.1

# 2. Fix the bug
# ... make changes ...
git add .
git commit -m "hotfix: fix critical authentication bug"

# 3. Merge to master and tag
git checkout master
git merge hotfix/v0.1.1 --no-ff
git tag v0.1.1
git push origin master
git push origin v0.1.1

# 4. Merge hotfix back to develop (avoid losing fix)
git checkout develop
git merge hotfix/v0.1.1
git push origin develop

# 5. Delete hotfix branch
git branch -d hotfix/v0.1.1
```

### Option B: Direct Master Hotfix (Emergency)

```bash
# 1. Fix directly on master
git checkout master
# ... make emergency fix ...
git commit -m "hotfix: critical security patch"

# 2. Tag hotfix version
git tag v0.1.1
git push origin master --tags

# 3. Merge back to develop immediately
git checkout develop
git merge master
git push origin develop
```

---

## Tag Conventions

### Version Tags

```bash
# Stable releases (on master only)
git tag v0.1
git tag v0.2
git tag v1.0

# Hotfix releases
git tag v0.1.1
git tag v0.1.2
git tag v1.0.1

# Annotated tags (preferred for releases)
git tag -a v0.2 -m "Release v0.2: Intelligence & Integration"
```

### Pre-release Tags (Optional)

```bash
# Beta/RC tags on develop branch (optional)
git tag v0.2-beta.1
git tag v0.2-rc.1

# Use for testing before merge to master
```

---

## GSD Integration

### GSD Commands Aware of Branches

When working with GSD:

1. **Always verify branch before starting phase:**
   ```bash
   git branch --show-current  # ensure you're on develop
   ```

2. **GSD atomic commits respect current branch:**
   - `/gsd:execute-phase 7` commits go to current branch (develop)
   - Planning docs in `.planning/` also committed to current branch

3. **Before merging to master:**
   - Run `/gsd:audit-milestone v0.2` to verify completion
   - Ensure all UAT tests pass
   - Review all commits since branch creation

### GSD Config

Current `.planning/config.json` setting:

```json
{
  "git": {
    "branching_strategy": "none"
  }
}
```

**Note:** `"branching_strategy": "none"` means GSD does NOT automatically create branches. Branch management is manual (as documented in this file).

---

## Release Checklist

### Pre-Release (on develop branch)

- [ ] All phase plans executed and verified
- [ ] `/gsd:audit-milestone v0.x` passes
- [ ] All UAT tests passed
- [ ] No critical bugs or blockers
- [ ] All commits include proper messages
- [ ] MILESTONES.md updated with release notes
- [ ] README.md updated (if needed)
- [ ] Documentation updated

### Release (merge to master)

- [ ] Switch to master: `git checkout master`
- [ ] Merge develop: `git merge develop --no-ff`
- [ ] Resolve any conflicts
- [ ] Tag release: `git tag v0.x`
- [ ] Push: `git push origin master --tags`
- [ ] Verify GitHub shows correct tag
- [ ] Update GitHub release notes (optional)

### Post-Release

- [ ] Optionally delete develop branch
- [ ] Create new develop branch for next milestone
- [ ] Update PROJECT.md with next milestone goals
- [ ] `/gsd:new-milestone v0.x` for next version

---

## Example: v0.2 Release

### Development Phase

```bash
# Feb 6, 2026: Start v0.2 development
git checkout master
git checkout -b develop
git push -u origin develop

# Feb 6-12, 2026: Execute Phase 7-11 on develop
/gsd:plan-phase 7
/gsd:execute-phase 7
# ... all phase work ...
/gsd:audit-milestone v0.2

# Feb 12, 2026: All phases complete, ready to release
```

### Release Phase

```bash
# Feb 12, 2026: Merge and release
git checkout master
git merge develop --no-ff

git tag -a v0.2 -m "Release v0.2: Intelligence & Integration

Features:
- AI agent memory persistence
- Multi-LLM provider support
- Smart query suggestions
- Web search tool integration
- Production SMTP email

43 requirements completed, 5 phases."

git push origin master
git push origin v0.2

# Clean up (optional)
git branch -d develop
```

### Next Milestone

```bash
# Feb 13, 2026: Start v0.3 development
git checkout -b develop
/gsd:new-milestone v0.3
```

---

## Quick Reference

### Common Commands

```bash
# Check current branch
git branch --show-current

# Switch branches
git checkout master
git checkout develop

# View all tags
git tag

# View tag details
git show v0.2

# View commit log with tags
git log --oneline --decorate --graph

# View diff between master and develop
git diff master..develop

# View files changed between master and develop
git diff master..develop --name-only
```

### Emergency Commands

```bash
# Abort merge if conflicts are too complex
git merge --abort

# Revert to previous commit (if bad merge)
git reset --hard HEAD~1  # DANGEROUS: only if unpushed

# Create backup branch before risky operation
git branch backup-develop
```

---

## Troubleshooting

### Issue: Accidentally committed to master instead of develop

```bash
# 1. Save the commit (copy the commit hash)
git log -1  # copy the commit hash

# 2. Switch to develop
git checkout develop

# 3. Cherry-pick the commit
git cherry-pick <commit-hash>

# 4. Switch back to master and reset
git checkout master
git reset --hard HEAD~1  # removes the commit from master

# 5. Force push if already pushed (CAREFUL!)
git push --force origin master  # only if safe
```

### Issue: Develop branch diverged from master (hotfix was applied)

```bash
# Merge master into develop to sync
git checkout develop
git merge master

# Resolve any conflicts, then continue work
```

### Issue: Need to abandon develop and start over

```bash
# Delete local develop branch
git checkout master
git branch -D develop

# Delete remote develop branch
git push origin --delete develop

# Create fresh develop from master
git checkout -b develop
git push -u origin develop
```

---

## Best Practices

1. **Always work on develop branch** during milestone development
2. **Never commit directly to master** except for emergency hotfixes
3. **Tag every release** on master (v0.1, v0.2, etc.)
4. **Use descriptive tag messages** (include feature summary)
5. **Merge develop to master only when milestone complete** and tested
6. **Use `--no-ff` for merge commits** (preserves branch history)
7. **Delete develop branch after release** (optional, keeps repo clean)
8. **Create new develop branch from master** for each milestone

---

*Last Updated: 2026-02-06*
*Strategy Established: v0.2 milestone*
*Next Review: After v1.0 release*
