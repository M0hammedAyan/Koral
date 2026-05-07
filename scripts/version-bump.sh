#!/bin/bash
# KORAL Version Bump Script
# Handles semantic version bumping, git tagging, and release preparation

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSION_FILE="VERSION"
GIT_REMOTE="${GIT_REMOTE:-origin}"
MAIN_BRANCH="${MAIN_BRANCH:-main}"

# Functions

print_help() {
    cat << EOF
KORAL Version Bump Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    major           Bump major version (1.0.0 → 2.0.0)
    minor           Bump minor version (1.0.0 → 1.1.0)
    patch           Bump patch version (1.0.0 → 1.0.1)
    prerelease      Create pre-release (1.0.0 → 1.0.0-rc.1)
    show            Display current version
    validate        Validate version format
    help            Show this help message

Options:
    --dry-run       Don't create git tag or commit
    --force         Force version bump even if dirty working directory
    --no-tag        Bump version without creating git tag
    --prerelease-type TYPE
                    Pre-release type: rc, beta, alpha (default: rc)

Examples:
    $0 patch                    # Bump patch version and create tag
    $0 minor --dry-run          # Test minor version bump
    $0 prerelease --prerelease-type beta
    $0 major --force --no-tag   # Force major bump without git operations

EOF
}

log_info() {
    echo -e "${BLUE}ℹ${NC}  $*"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $*"
}

log_error() {
    echo -e "${RED}✗${NC}  $*"
    exit 1
}

# Get current version
get_current_version() {
    if [[ ! -f "$VERSION_FILE" ]]; then
        log_error "Version file not found: $VERSION_FILE"
    fi
    cat "$VERSION_FILE" | tr -d '\n' | tr -d '\r'
}

# Parse semantic version
parse_version() {
    local version="$1"
    # Remove 'v' prefix if present
    version="${version#v}"
    
    # Extract pre-release if present
    local prerelease=""
    if [[ $version =~ -(.+)$ ]]; then
        prerelease="${BASH_REMATCH[1]}"
        version="${version%-*}"
    fi
    
    # Split version into components
    IFS='.' read -r major minor patch <<< "$version"
    
    echo "$major" "$minor" "${patch:-0}" "$prerelease"
}

# Validate semantic version format
validate_version() {
    local version="$1"
    version="${version#v}"
    
    # Regex: X.Y.Z[-prerelease][+build]
    if [[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$ ]]; then
        return 0
    else
        return 1
    fi
}

# Check if working directory is clean
check_working_directory() {
    if [[ $(git status --porcelain | wc -l) -gt 0 ]]; then
        if [[ "${FORCE:-false}" != "true" ]]; then
            log_error "Working directory is not clean. Use --force to override."
        else
            log_warning "Working directory has uncommitted changes (--force used)"
        fi
    fi
}

# Check if on main branch
check_on_main_branch() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$current_branch" != "$MAIN_BRANCH" ]]; then
        log_error "Must be on $MAIN_BRANCH branch (current: $current_branch)"
    fi
}

# Bump version
bump_version() {
    local current="$1"
    local bump_type="$2"
    local prerelease_type="${3:-rc}"
    
    read -r major minor patch prerelease <<< "$(parse_version "$current")"
    
    case "$bump_type" in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            new_version="$major.$minor.$patch"
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            new_version="$major.$minor.$patch"
            ;;
        patch)
            patch=$((patch + 1))
            new_version="$major.$minor.$patch"
            ;;
        prerelease)
            if [[ -n "$prerelease" ]]; then
                # Increment existing pre-release
                if [[ $prerelease =~ ^([a-z]+)\.?([0-9]*)$ ]]; then
                    local type="${BASH_REMATCH[1]}"
                    local num="${BASH_REMATCH[2]:-0}"
                    num=$((num + 1))
                    new_version="$major.$minor.$patch-$type.$num"
                else
                    new_version="$major.$minor.$patch-$prerelease_type.1"
                fi
            else
                # Create new pre-release
                new_version="$major.$minor.$patch-$prerelease_type.1"
            fi
            ;;
        *)
            log_error "Invalid bump type: $bump_type"
            ;;
    esac
    
    echo "$new_version"
}

# Show version
show_version() {
    local current=$(get_current_version)
    log_info "Current version: $current"
}

# Validate command
validate_command() {
    local command="$1"
    case "$command" in
        major|minor|patch|prerelease|show|validate|help)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Main execution
main() {
    # Parse arguments
    local command="${1:-}"
    shift || true
    
    local DRY_RUN=false
    local FORCE=false
    local CREATE_TAG=true
    local PRERELEASE_TYPE="rc"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --no-tag)
                CREATE_TAG=false
                shift
                ;;
            --prerelease-type)
                PRERELEASE_TYPE="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                ;;
        esac
    done
    
    # Help command
    if [[ -z "$command" || "$command" == "help" ]]; then
        print_help
        exit 0
    fi
    
    # Validate command
    if ! validate_command "$command"; then
        log_error "Invalid command: $command"
    fi
    
    # Show command
    if [[ "$command" == "show" ]]; then
        show_version
        exit 0
    fi
    
    # Validate command
    if [[ "$command" == "validate" ]]; then
        local version=$(get_current_version)
        if validate_version "$version"; then
            log_success "Version is valid: $version"
            exit 0
        else
            log_error "Invalid version format: $version"
        fi
    fi
    
    # Get current version
    current=$(get_current_version)
    log_info "Current version: $current"
    
    # Validate current version
    if ! validate_version "$current"; then
        log_error "Current version is invalid: $current"
    fi
    
    # Check working directory and branch
    if [[ "$DRY_RUN" != "true" ]]; then
        check_working_directory
        check_on_main_branch
    fi
    
    # Bump version
    new_version=$(bump_version "$current" "$command" "$PRERELEASE_TYPE")
    log_info "New version: $new_version"
    
    # Validate new version
    if ! validate_version "$new_version"; then
        log_error "New version is invalid: $new_version"
    fi
    
    # Dry run mode
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Changes not applied"
        exit 0
    fi
    
    # Update VERSION file
    echo -n "$new_version" > "$VERSION_FILE"
    log_success "Updated $VERSION_FILE"
    
    # Git operations if not skipped
    if [[ "$CREATE_TAG" == "true" ]]; then
        # Commit version bump
        git add "$VERSION_FILE"
        git commit -m "chore: bump version to $new_version"
        log_success "Committed version bump"
        
        # Create annotated tag
        git tag -a "v$new_version" \
            -m "Release version $new_version" \
            -m "Bumped from $current to $new_version"
        log_success "Created git tag: v$new_version"
        
        # Push changes and tags
        git push "$GIT_REMOTE" "$MAIN_BRANCH"
        git push "$GIT_REMOTE" "v$new_version"
        log_success "Pushed to $GIT_REMOTE"
    else
        # Just commit the version file
        git add "$VERSION_FILE"
        git commit -m "chore: bump version to $new_version"
        log_success "Committed version bump (no tag created)"
    fi
    
    log_success "Version bump completed: $current → $new_version"
}

# Run main
main "$@"
