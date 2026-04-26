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
master      →  Stable releases only (tagged versions)
develop     →  Integration branch — completed features accumulate here
feature/*   →  One branch per feature, auto-created by GSD milestone strategy
release/*   →  Short-lived release staging branch (cut from develop, merged to master)
hotfix/*    →  Emergency fixes for current stable version
```

### Branch Purposes

| Branch | Purpose | Protected | Tags |
|--------|---------|-----------|------|
| `master` | Production-ready code, always stable | ✅ Yes | All version tags (v0.1, v0.2, etc.) |
| `develop` | Integration — completed features land here | ❌ No | Pre-release tags (optional) |
| `feature/*` | GSD-managed: auto-created at first `execute-phase` per milestone | ❌ No | None |
| `release/*` | Release staging — integration fixes only, no new features | ❌ No | None |
| `hotfix/*` | Bug fixes and minor changes for current release | ❌ No | Patch tags (v0.1.1, v0.1.2) |

> **Feature-based workflow:** Features are developed as GSD milestones with `branching_strategy: "milestone"`. GSD auto-creates `feature/*` branches — no manual branching needed. See [FEATURE-WORKFLOW.md](./FEATURE-WORKFLOW.md) for the complete guide.

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

### Starting a New Feature

See [FEATURE-WORKFLOW.md](./FEATURE-WORKFLOW.md) for the complete step-by-step guide.

**Summary:**

1. Write a requirements document in `requirements/`
2. Hand off to GSD: `/gsd:new-milestone <feature-name>` — GSD plans on `develop` (research, requirements, roadmap), then auto-creates the `feature/*` branch at first `/gsd:execute-phase`
3. GSD signals completion via `/gsd:complete-milestone`
4. PR the feature branch into `develop`
5. Reconcile `.planning/` files on merge

### Releasing New Version

When the project owner decides which completed features to ship:

```bash
# 1. Ensure all feature PRs are merged and develop is clean
git checkout develop
git pull origin develop
git status  # should be clean

# 2. Cut release branch from develop
git checkout -b release/vX.Y

# 3. Smoke test — fix integration issues only (no new features)

# 4. Switch to master and merge
git checkout master
git merge release/vX.Y --no-ff  # create merge commit for clarity

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

# 6. Merge release branch back to develop and clean up
git checkout develop
git merge release/vX.Y
git push origin develop
git branch -d release/vX.Y
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

### GSD Config

```json
{
  "git": {
    "branching_strategy": "milestone",
    "milestone_branch_template": "feature/{milestone}-{slug}"
  }
}
```

GSD manages the feature development lifecycle on `feature/*` branches. Our process takes over after GSD signals completion. See [FEATURE-WORKFLOW.md](./FEATURE-WORKFLOW.md) for the full handshake details.

### Handshake Points

| Point | Direction | What happens |
|-------|-----------|--------------|
| `/gsd:new-milestone` | Us → GSD | We hand off a requirements doc; GSD plans on `develop` (research, requirements, roadmap) |
| `/gsd:execute-phase` | GSD | GSD auto-creates `feature/*` branch on first execution; all code committed there |
| `/gsd:complete-milestone` | GSD → Us | GSD signals feature is done; we take over for PR + release |

---

## Release Checklist

### Pre-Release

- [ ] All target feature branches merged into `develop` via PR
- [ ] `.planning/` reconciliation done for each merged feature
- [ ] No critical bugs or blockers on `develop`
- [ ] README.md updated (if needed)

### Release

- [ ] Cut release branch: `git checkout -b release/vX.Y` from `develop`
- [ ] Smoke test — fix integration issues only
- [ ] Merge to master: `git merge release/vX.Y --no-ff`
- [ ] Tag release: `git tag -a vX.Y -m "Release vX.Y: ..."`
- [ ] Push master: `git push origin master`
- [ ] Push tag: `git push origin vX.Y`
- [ ] Merge release back to develop: `git merge release/vX.Y`
- [ ] Push develop: `git push origin develop`
- [ ] Delete release branch: `git branch -d release/vX.Y`
- [ ] Trigger Dokploy redeployment

### Post-Release

- [ ] Verify Dokploy services running new version
- [ ] Update PROJECT.md with next goals (if applicable)

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

1. **Use GSD milestone branching strategy** — let GSD create `feature/*` branches automatically
2. **Never commit directly to master** except for emergency hotfixes
3. **Tag every release** on master (v0.1, v0.6, etc.)
4. **Use descriptive tag messages** (include feature summary)
5. **Use `release/vX.Y` branches** for release staging — no new features on release branches
6. **Always push both `master` and `develop`** after a release
7. **Use `--no-ff` for merge commits** (preserves branch history)
8. **Dokploy services always point to `master`** — never deploy from `develop`

---

*Last Updated: 2026-03-17*
*Strategy Established: v0.2 milestone*
*Updated: v0.6 milestone — clarified remote branch policy and Dokploy branch requirement*
*Updated: 2026-03-17 — adopted GSD milestone branching strategy (feature/* auto-branches), added release/* for release staging, aligned with GSD native parallel development (see FEATURE-WORKFLOW.md)*
*Next Review: After v1.0 release*
