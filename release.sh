#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}$1${NC}"
}

log_success() {
    echo -e "${GREEN}$1${NC}"
}

log_warning() {
    echo -e "${YELLOW}$1${NC}"
}

log_error() {
    echo -e "${RED}$1${NC}"
}

# Get new version based on bump type
get_new_version() {
    local bump_type=$1
    uv run bump-my-version bump "$bump_type" --dry-run --no-commit --no-tag | grep "New version" | cut -d"'" -f2
}

# Prepare release
prepare_release() {
    log_info "Preparing release..."
    
    local new_version
    local bump_type
    
    # Determine version bump strategy
    if [ -n "$VERSION" ]; then
        new_version="$VERSION"
        log_info "Using specified version: $new_version"
    elif [ -n "$BUMP" ]; then
        new_version=$(get_new_version "$BUMP")
        log_info "Using $BUMP bump: $new_version"
    else
        log_info "Auto-detecting version bump using git-cliff..."
        new_version=$(uv run git-cliff --bumped-version | sed 's/^v//')
        log_info "Auto-detected version: $new_version"
    fi
    
    # Update version
    log_info "Updating version to $new_version..."
    uv run bump-my-version bump --new-version "$new_version"
    
    # Generate changelog
    log_info "Generating changelog..."
    uv run git-cliff --tag "v$new_version" -o CHANGELOG.md
    
    # Create release commit and tag
    log_info "Creating release commit and tag..."
    git add pyproject.toml CHANGELOG.md uv.lock
    git commit -m "chore: release v$new_version"
    git tag -a "v$new_version" -m "Release v$new_version"
    
    # Build package
    log_info "Building package..."
    uv build
    
    # Success message
    echo ""
    log_success "✅ Release v$new_version prepared!"
    log_info "📦 Package built in dist/"
    log_info "🧪 Test the release, then run 'make publish' to publish it."
    log_warning "🔄 Or run 'make reset-release' to undo and try again."
}

# Reset release preparation
reset_release() {
    log_info "Checking if last commit is a release commit..."
    
    local last_commit_msg
    last_commit_msg=$(git log -1 --pretty=format:"%s")
    
    if echo "$last_commit_msg" | grep -q "^chore: release v"; then
        local release_tag
        release_tag=$(echo "$last_commit_msg" | sed 's/chore: release //')
        
        log_info "Found release commit: $release_tag"
        log_info "Removing release commit and tag..."
        
        git reset --hard HEAD~1
        git tag -d "$release_tag" 2>/dev/null || true
        
        log_success "✅ Release preparation reset."
    else
        log_error "❌ Last commit is not a release commit. Nothing to reset."
        exit 1
    fi
}

# Check if last commit is a release commit
is_release_commit() {
    git log -1 --pretty=format:"%s" | grep -q "^chore: release v"
}

# Check if working directory is clean
is_working_directory_clean() {
    git diff-index --quiet HEAD --
}

# Check if we're on main branch
is_on_main_branch() {
    [ "$(git branch --show-current)" = "main" ]
}

# Publish release
publish_release() {
    log_info "Verifying release is ready..."
    
    # Check that last commit is a release commit
    if ! is_release_commit; then
        log_error "❌ Last commit is not a release commit. Run 'make prepare-release' first."
        exit 1
    fi
    
    # Check that working directory is clean
    if ! is_working_directory_clean; then
        log_error "❌ Working directory is not clean. Commit or stash changes first."
        exit 1
    fi
    
    # Check that we're on main branch
    if ! is_on_main_branch; then
        log_error "❌ Not on main branch. Switch to main branch first."
        exit 1
    fi
    
    # Extract release version
    local release_version
    release_version=$(git log -1 --pretty=format:"%s" | sed 's/chore: release v//')
    
    log_info "Publishing release v$release_version..."
    
    # Clean and rebuild package
    log_info "Cleaning and rebuilding package..."
    rm -rf dist/
    uv build
    
    # Publish to PyPI
    log_info "Publishing to PyPI..."
    uv publish
    
    # Push to GitHub
    log_info "Pushing to GitHub..."
    git push origin main
    git push origin "v$release_version"
    
    # Create GitHub release
    log_info "Creating GitHub release..."
    local changelog_content
    changelog_content=$(uv run git-cliff --tag "v$release_version" --strip header)
    gh release create "v$release_version" --title "Release v$release_version" --notes "$changelog_content"
    
    # Success message
    echo ""
    log_success "🎉 Release v$release_version published successfully!"
    log_info "📦 PyPI: https://pypi.org/project/moomoolah/$release_version/"
    log_info "🐙 GitHub: https://github.com/eliasdorneles/moomoolah/releases/tag/v$release_version"
}

# Main script logic
case "$1" in
    "prepare")
        prepare_release
        ;;
    "reset")
        reset_release
        ;;
    "publish")
        publish_release
        ;;
    *)
        echo "Usage: $0 {prepare|reset|publish}"
        echo "  prepare: Prepare a new release"
        echo "  reset:   Reset the last release preparation"
        echo "  publish: Publish the prepared release"
        exit 1
        ;;
esac
