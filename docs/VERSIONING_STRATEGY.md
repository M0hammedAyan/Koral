# KORAL Production Versioning Strategy

## Overview
KORAL follows **Semantic Versioning (SemVer)** with the format: `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

## Version Components

### MAJOR Version (Breaking Changes)
- Incremented when incompatible API changes are made
- Database schema migrations requiring manual intervention
- Significant architectural changes
- Example: `1.0.0` → `2.0.0`

### MINOR Version (Features)
- Incremented when new features are added in backward-compatible manner
- New endpoints, configuration options
- Performance improvements
- Example: `1.0.0` → `1.1.0`

### PATCH Version (Bug Fixes)
- Incremented for bug fixes and security patches
- Critical hotfixes
- Example: `1.0.0` → `1.0.1`

### Pre-release Tags
- Format: `v1.0.0-rc.1`, `v1.0.0-beta.1`, `v1.0.0-alpha.1`
- Not included in stable release channels
- Ordered alphabetically before release version

### Build Metadata
- Format: `v1.0.0+build.123`
- CI/CD build number
- Not included in precedence for version comparison

## Tagging Convention

### Git Tags
- Format: `v{MAJOR}.{MINOR}.{PATCH}`
- Annotated tags with release notes
- Point to merge commits on `main` branch
- Examples:
  - `v1.0.0` - Release
  - `v1.0.1` - Patch release
  - `v1.1.0` - Feature release
  - `v1.0.0-rc.1` - Release candidate

### Docker Image Tags
- **Semantic**: `ghcr.io/m0hammedayan/koral/koral-backend:v1.0.0`
- **Major.Minor**: `ghcr.io/m0hammedayan/koral/koral-backend:v1.0`
- **Latest**: `ghcr.io/m0hammedayan/koral/koral-backend:latest` (only for releases)
- **Commit SHA**: `ghcr.io/m0hammedayan/koral/koral-backend:abc123def` (for debugging)
- **Pre-release**: `ghcr.io/m0hammedayan/koral/koral-backend:v1.0.0-rc.1`

## Release Process

### 1. Development Branch
- All changes made on `feature/*` or `bugfix/*` branches
- Pull requests with automated testing
- Code review required before merge

### 2. Version Bump
- Automated or manual: update version in `VERSION` file
- Trigger: Push to `main` branch with version change
- Workflow: `version-and-release.yml`

### 3. Build & Scan
- Multi-arch builds (amd64, arm64)
- Security scanning with Trivy
- SBOM generation (SPDX format)
- Image signing with Cosign

### 4. Registry Push
- Push to GitHub Container Registry (ghcr.io)
- Multiple image tags
- Publish SBOM and scan results

### 5. Release Notes
- Auto-generated from commit messages
- Manual review for accuracy
- Published on GitHub Releases

### 6. Deployment
- Development: automatic on merge
- Staging: manual trigger
- Production: manual approval

## Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning:

### Types
- `feat:` - New feature (triggers MINOR bump)
- `fix:` - Bug fix (triggers PATCH bump)
- `perf:` - Performance improvement (triggers MINOR bump)
- `docs:` - Documentation only (no version bump)
- `style:` - Code style (no version bump)
- `test:` - Testing (no version bump)
- `chore:` - Maintenance (no version bump)
- `ci:` - CI/CD (no version bump)

### BREAKING CHANGE
- Add footer: `BREAKING CHANGE: description`
- Or prefix with `!`: `feat!: new API`
- Triggers MAJOR bump

### Examples
```
feat: add anomaly detection threshold adjustment
fix: resolve race condition in correlation engine
perf: optimize database queries for incident retrieval
feat!: redesign incident response API (BREAKING CHANGE)
docs: update deployment guide
chore: update dependencies
```

## Version File

### VERSION File Location
- Path: `/VERSION`
- Content: Single line with semantic version
- Example: `1.0.0`

### Environment Variable
- `KORAL_VERSION`: Set in CI/CD
- `VERSION`: Available in containers

## Backward Compatibility

### Guarantees
- PATCH versions: Always backward compatible
- MINOR versions: Backward compatible with same MAJOR
- MAJOR versions: No compatibility guarantee

### Deprecation Policy
- Deprecations: Announced 1 MINOR version in advance
- Removal: Happens in next MAJOR version
- Documentation: Clear migration paths

## Release Channels

### Stable (Production)
- Format: `v{MAJOR}.{MINOR}.{PATCH}`
- Recommended for production deployments
- Tested and stable

### Latest (Recommended)
- Most recent stable release
- Always `v{MAJOR}.{MINOR}.{PATCH}`
- Recommended for new deployments

### Pre-release (Testing)
- Format: `v{MAJOR}.{MINOR}.{PATCH}-{PRERELEASE}`
- Examples: `rc`, `beta`, `alpha`
- For testing before stable release

### Nightly (Development)
- Built from `main` branch
- Not guaranteed to be stable
- For early testing

## Versioning Timeline

| Phase | Duration | Activity |
|-------|----------|----------|
| Development | Variable | Feature branches, PRs |
| Release Candidate | 1 week | Testing, beta feedback |
| Stable Release | Ongoing | Support, bug fixes |
| Next Development | Ongoing | Features for next release |

## Security Patch Policy

- Critical fixes: Released ASAP
- High priority: Released within 48 hours
- Medium/Low: Released in next MINOR version
- Patch release: Published separately with security notice

## Version Retention

### Docker Registry
- Keep last 10 releases
- Keep latest MAJOR.MINOR versions
- Delete pre-releases after 30 days
- Delete nightly builds older than 7 days

### GitHub Releases
- Keep all releases
- Archive older than 1 year

## Examples

### Normal Release Cycle
```
v0.9.0 (development)
v0.10.0 (feature release)
v0.10.1 (security patch)
v0.10.2 (bug fix)
v0.11.0 (feature release)
v1.0.0-rc.1 (release candidate)
v1.0.0 (stable release)
```

### Patch Release
```
v1.0.0 (initial release)
v1.0.1 (bug fix)
v1.0.2 (security patch)
v1.0.3 (critical hotfix)
```

## Tools & Automation

### GitHub Actions
- **version-and-release.yml**: Semantic versioning workflow
- **build-and-push.yml**: Multi-arch build & push
- **security-scan.yml**: Vulnerability scanning

### Scripts
- **scripts/version-bump.sh**: Local version bumping
- **scripts/create-release.sh**: Manual release creation
- **scripts/validate-version.sh**: Version format validation

## References

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Container Image Tags](https://docs.docker.com/develop/dev-best-practices/image-naming/)
- [Container Metadata](https://github.com/opencontainers/image-spec)
