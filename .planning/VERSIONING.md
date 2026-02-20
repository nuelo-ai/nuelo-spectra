# Versioning & Release Strategy

**Project:** Spectra
**Strategy:** Development Branch with Semantic Versioning
**Last Updated:** 2026-02-20

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

### Patch Versions

For bug fixes, minor improvements, or small changes to a released version — without bumping the minor version:

```
v0.1.1, v0.1.2, v1.0.1, v1.0.2, etc.
```

Use a patch version when the change is:
- A bug fix (critical or non-critical)
- A minor UI/UX improvement
- A small config or documentation change
- A dependency update
- Any small change that doesn't warrant a full milestone

Do **not** use a patch version for new features or significant additions — those belong in the next minor version (e.g., v0.6, v1.1).

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
| `hotfix/*` | Bug fixes and minor changes for current release | ❌ No | Patch tags (v0.1.1, v0.1.2) |

### Remote Branch Policy

**Both `master` and `develop` are always pushed to the remote repository:**

- `origin/master` — stable, production-ready code; what Dokploy production services pull from
- `origin/develop` — work in progress; never deployed to production

```bash
# After every milestone, both branches are pushed:
git push origin master
git push origin develop
```

This means the remote always reflects both the latest stable release and the current development state.

---

## Production Deployment Branch

**Dokploy production services always use `master` branch.**

- All 4 Dokploy Application services (`spectra-public-backend`, `spectra-admin-backend`, `spectra-public-frontend`, `spectra-admin-frontend`) are configured to build from `master`
- `develop` branch is **never** deployed to production
- When a milestone is complete: merge `develop` → `master`, push both, then trigger Dokploy redeployment on each service

This ensures the live beta app always runs code that has been audited, verified, and released.

---

## Development Workflow

### Starting New Milestone

When starting a new milestone (e.g., v0.7):

```bash
# 1. Ensure you're on develop
git checkout develop

# 2. All GSD phases work on develop
/gsd:plan-phase 37
/gsd:execute-phase 37
# ... all phase commits go to develop ...

# Develop branch accumulates all phase work
```

### During Development

**All GSD commands execute on `develop` branch:**

```bash
# Verify you're on develop
git branch --show-current  # should show "develop"

# Normal GSD workflow
/gsd:plan-phase 37
/gsd:execute-phase 37
/gsd:verify-phase 37

# All commits automatically go to develop
# GSD atomic commits continue as normal
```

### Releasing New Version

When milestone is complete and audit passes:

```bash
# 1. Ensure all work is committed on develop
git checkout develop
git status  # should be clean

# 2. Run final milestone audit
/gsd:audit-milestone

# 3. Switch to master and merge
git checkout master
git merge develop --no-ff  # create merge commit for clarity

# 4. Tag the release
git tag -a v0.6 -m "Release v0.6: Docker and Dokploy Support

Features:
- Fixed localhost hardcodes, standalone Next.js builds
- Version API endpoint with live display in both frontends
- Production Dockerfiles for backend, public frontend, admin frontend
- Docker Compose for local development validation
- Deployed 4 Dokploy services with Tailscale split-horizon architecture
- DEPLOYMENT.md complete guide

24 requirements completed across 4 phases (Phases 33-36)."

# 5. Push master with tag
git push origin master
git push origin v0.6

# 6. Push develop to keep remote in sync
git push origin develop

# 7. Complete milestone via GSD
/gsd:complete-milestone v0.6
```

**After release:** Dokploy services automatically pick up the new code on next redeploy (they pull from `master`).

---

## Patch Workflow

Use a `hotfix/*` branch for bug fixes, minor improvements, or small changes to a released version. This applies whether it's a critical bug or a minor tweak — anything too small to wait for the next milestone.

### Option A: Patch Branch (Recommended)

```bash
# 1. Create patch branch from master
git checkout master
git checkout -b hotfix/v0.6.1

# 2. Make changes (bug fix, minor improvement, config update, etc.)
# ... make changes ...
git add .
git commit -m "fix: correct authentication timeout logic"
# or: git commit -m "chore: update default SMTP port"

# 3. Merge to master and tag
git checkout master
git merge hotfix/v0.6.1 --no-ff
git tag -a v0.6.1 -m "v0.6.1: [brief description of change]"
git push origin master
git push origin v0.6.1

# 4. Merge back to develop (keep develop in sync)
git checkout develop
git merge hotfix/v0.6.1
git push origin develop

# 5. Delete patch branch
git branch -d hotfix/v0.6.1
```

### Option B: Direct Master Patch (Simple/Emergency)

```bash
# 1. Make change directly on master
git checkout master
# ... make changes ...
git commit -m "fix: critical security patch"
# or: git commit -m "chore: minor UI label correction"

# 2. Tag patch version
git tag -a v0.6.1 -m "v0.6.1: [brief description]"
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
git tag v0.6
git tag v1.0

# Patch releases (bug fixes, minor improvements, small changes)
git tag v0.6.1
git tag v0.6.2
git tag v1.0.1

# Annotated tags (preferred for releases)
git tag -a v0.6 -m "Release v0.6: Docker and Dokploy Support"
```

### Pre-release Tags (Optional)

```bash
# Beta/RC tags on develop branch (optional)
git tag v0.6-beta.1
git tag v0.6-rc.1

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
   - `/gsd:execute-phase 37` commits go to current branch (develop)
   - Planning docs in `.planning/` also committed to current branch

3. **Before merging to master:**
   - Run `/gsd:audit-milestone` to verify completion
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
- [ ] `/gsd:audit-milestone` passes
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
- [ ] Tag release: `git tag -a v0.x -m "Release v0.x: ..."`
- [ ] Push master: `git push origin master`
- [ ] Push tag: `git push origin v0.x`
- [ ] Push develop: `git push origin develop`
- [ ] Verify GitHub shows correct tag on master
- [ ] Update Dokploy services to use `master` branch (if not already set)
- [ ] Trigger redeployment on each Dokploy service

### Post-Release

- [ ] Create new develop branch if deleted (or continue on existing develop)
- [ ] Update PROJECT.md with next milestone goals
- [ ] `/gsd:new-milestone v0.x` for next version

---

## Example: v0.6 Release

### Development Phase

```bash
# Feb 18-20, 2026: Execute Phases 33-36 on develop
/gsd:plan-phase 33
/gsd:execute-phase 33
# ... all phase work ...
/gsd:audit-milestone  # passes

# Feb 20, 2026: Ready to release
```

### Release Phase

```bash
# Feb 20, 2026: Merge and release
git checkout master
git merge develop --no-ff

git tag -a v0.6 -m "Release v0.6: Docker and Dokploy Support

Features:
- Fixed localhost hardcodes, standalone Next.js builds
- Version API with live display in both frontends
- Production Dockerfiles (backend, frontend, admin)
- Docker Compose for local dev validation
- 4 Dokploy services with Tailscale split-horizon
- DEPLOYMENT.md complete guide

24 requirements completed, 4 phases."

git push origin master
git push origin v0.6

# Keep develop in sync
git push origin develop

# Both branches now on remote, master is production source
```

### Update Dokploy

After pushing master, update each Dokploy service to use `master` branch and redeploy:
- `spectra-public-backend` → Branch: `master` → Deploy
- `spectra-admin-backend` → Branch: `master` → Deploy
- `spectra-public-frontend` → Branch: `master` → Deploy
- `spectra-admin-frontend` → Branch: `master` → Deploy

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
git show v0.6

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
git push origin develop

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
3. **Tag every release** on master (v0.1, v0.6, etc.)
4. **Use descriptive tag messages** (include feature summary)
5. **Merge develop to master only when milestone audit passes**
6. **Always push both branches** after a release (`git push origin master && git push origin develop`)
7. **Use `--no-ff` for merge commits** (preserves branch history)
8. **Dokploy services always point to `master`** — never deploy from `develop`

---

*Last Updated: 2026-02-20*
*Strategy Established: v0.2 milestone*
*Updated: v0.6 milestone — clarified remote branch policy and Dokploy branch requirement*
*Next Review: After v1.0 release*
