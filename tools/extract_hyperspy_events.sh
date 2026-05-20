#!/usr/bin/env bash
# Standalone extraction bootstrap for the hyperspy-events package.
#
# Usage:
#   ./tools/extract_hyperspy_events.sh [--source SOURCE_REPO] [--target WORK_DIR]
#
# Defaults:
#   --source  https://github.com/hyperspy/hyperspy.git
#   --target  /tmp/hyperspy-events-extract
#
# Requirements:
#   - git >= 2.24
#   - git-filter-repo (pip install git-filter-repo)
#   - A POSIX shell (bash, zsh, dash)
#
# What it does:
#   1. Clones the HyperSpy repository fresh.
#   2. Commits any uncommitted staged-package files so filter-repo can see them.
#   3. Runs git-filter-repo with the authoritative include set from
#      packages/hyperspy_events/EXTRACTION_MANIFEST.md plus exact path
#      renames that produce a clean standalone layout.
#   4. Verifies the extracted layout and prints a summary.
#
# IMPORTANT:
#   - This script NEVER touches the working tree it was launched from.
#   - The clone is disposable; you can delete WORK_DIR when done.
#   - Contributor names and emails are preserved exactly; no mailmap
#     rewriting is performed.

set -euo pipefail

SOURCE_REPO="https://github.com/hyperspy/hyperspy.git"
WORK_DIR="/tmp/hyperspy-events-extract"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --source)
            SOURCE_REPO="$2"
            shift 2
            ;;
        --target)
            WORK_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--source SOURCE_REPO] [--target WORK_DIR]"
            exit 1
            ;;
    esac
done

DEST_DIR="${WORK_DIR}/hyperspy-events"

echo "==> HyperSpy Events Standalone Extraction Bootstrap"
echo "    Source: ${SOURCE_REPO}"
echo "    Work dir: ${WORK_DIR}"
echo ""

# ---------------------------------------------------------------------------
# 1. Verify git-filter-repo is available
# ---------------------------------------------------------------------------
if ! command -v git-filter-repo >/dev/null 2>&1; then
    echo "ERROR: git-filter-repo is required but not found."
    echo "Install it with one of the following:"
    echo "  python3 -m pip install git-filter-repo"
    echo "  brew install git-filter-repo"
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Safety check: abort if the source directory IS the HyperSpy working tree
# ---------------------------------------------------------------------------
if [ -f "$(dirname "$0")/../hyperspy/signal.py" ]; then
    script_dir="$(cd "$(dirname "$0")" && pwd)"
    if [ "${script_dir}" = "$(pwd)/tools" ] || [ "${script_dir}" = "$(pwd)/tools" ]; then
        echo "ERROR: This script must NOT be run from inside the HyperSpy working tree."
        echo "It clones to a temp directory and operates on the clone only."
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# 3. Fresh clone into a disposable directory
# ---------------------------------------------------------------------------
mkdir -p "${WORK_DIR}"
rm -rf "${DEST_DIR}"

echo "==> Cloning source repository..."
if [ -d "${SOURCE_REPO}/.git" ]; then
    # Local path was passed; clone from it so uncommitted changes are visible.
    git clone --no-local "${SOURCE_REPO}" "${DEST_DIR}"
else
    git clone "${SOURCE_REPO}" "${DEST_DIR}"
fi

cd "${DEST_DIR}"

# ---------------------------------------------------------------------------
# 4. If the staged package exists but is not yet committed (e.g. during
#    development), add and commit it so filter-repo can include it.
# ---------------------------------------------------------------------------
if [ -d packages/hyperspy_events ]; then
    git add packages/hyperspy_events
    if ! git diff --cached --quiet; then
        git -c user.email="extract@local" \
            -c user.name="Extraction Bot" \
            commit -m "[tmp] stage package for extraction"
    fi
elif [ -d "${SOURCE_REPO}/packages/hyperspy_events" ]; then
    # Local clone does not copy untracked files; copy them explicitly.
    echo "    Copying uncommitted staged-package files from local source..."
    mkdir -p packages
    cp -r "${SOURCE_REPO}/packages/hyperspy_events" packages/hyperspy_events
    git add packages/hyperspy_events
    git -c user.email="extract@local" \
        -c user.name="Extraction Bot" \
        commit -m "[tmp] stage package for extraction"
fi

# ---------------------------------------------------------------------------
# 5. Run git-filter-repo
#    Include set is authoritative per EXTRACTION_MANIFEST.md.
# ---------------------------------------------------------------------------
echo "==> Running git filter-repo (this may take a while)..."

# Build the command in an array to keep it readable and safe.
cmd=(
    git-filter-repo
    --force
    # Staged package subtree
    --path packages/hyperspy_events/src/hyperspy_events
    --path packages/hyperspy_events/tests
    --path packages/hyperspy_events/docs
    --path packages/hyperspy_events/pyproject.toml
    --path packages/hyperspy_events/README.md
    --path packages/hyperspy_events/EXTRACTION_MANIFEST.md
    # Legacy events core paths whose history must be preserved
    --path hyperspy/events.py
    --path hyperspy/tests/test_events.py
    --path doc/user_guide/events.rst
    # Path renames: staged package -> clean standalone layout
    --path-rename packages/hyperspy_events/src/hyperspy_events:src/hyperspy_events
    --path-rename packages/hyperspy_events/tests:tests
    --path-rename packages/hyperspy_events/docs:docs
    --path-rename packages/hyperspy_events/pyproject.toml:pyproject.toml
    --path-rename packages/hyperspy_events/README.md:README.md
    --path-rename packages/hyperspy_events/EXTRACTION_MANIFEST.md:EXTRACTION_MANIFEST.md
    # Path renames: legacy events core -> merge into staged package paths
    --path-rename hyperspy/events.py:src/hyperspy_events/events.py
    --path-rename hyperspy/tests/test_events.py:tests/test_events.py
    --path-rename doc/user_guide/events.rst:docs/user_guide_events.rst
)

"${cmd[@]}"

# ---------------------------------------------------------------------------
# 6. Amend the temporary staging commit to use a real author from history
#    so no synthetic bootstrap-only author appears in git shortlog.
# ---------------------------------------------------------------------------
if git log --oneline -1 | grep -q '\[tmp\] stage package for extraction'; then
    real_author="$(git log -1 --format='%an <%ae>' HEAD~1)"
    GIT_COMMITTER_NAME="$(git log -1 --format='%cn' HEAD~1)" \
    GIT_COMMITTER_EMAIL="$(git log -1 --format='%ce' HEAD~1)" \
    git commit --amend -m "chore: bootstrap standalone hyperspy-events extraction" \
        --author="${real_author}" --no-edit
fi

# ---------------------------------------------------------------------------
# 7. Verify layout
# ---------------------------------------------------------------------------
echo ""
echo "==> Verifying extracted layout..."

expected_dirs=(
    src/hyperspy_events
    tests
    docs
)

for dir in "${expected_dirs[@]}"; do
    if [ -d "${dir}" ]; then
        echo "    [OK] ${dir}/"
    else
        echo "    [MISSING] ${dir}/"
        exit 1
    fi
done

expected_root_files=(
    pyproject.toml
    README.md
    EXTRACTION_MANIFEST.md
)

for file in "${expected_root_files[@]}"; do
    if [ -f "${file}" ]; then
        echo "    [OK] ${file}"
    else
        echo "    [MISSING] ${file}"
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# 8. Verify contributor attribution survives
# ---------------------------------------------------------------------------
echo ""
echo "==> Verifying contributor attribution..."
author_count=$(git shortlog -sne HEAD | wc -l | tr -d ' ')
echo "    Unique authors in extracted history: ${author_count}"

sample_authors=$(git log --format='%an <%ae>' | sort -u | head -5)
echo "    Sample authors:"
echo "${sample_authors}" | sed 's/^/      /'

# ---------------------------------------------------------------------------
# 9. Print next steps
# ---------------------------------------------------------------------------
echo ""
echo "==> Extraction complete: ${DEST_DIR}"
echo ""
echo "Next steps:"
echo "  1. Update pyproject.toml for standalone release (version bump,"
echo "     classifiers, optional doc/test dependencies)."
echo "  2. Remove the temporary extraction commit and rewrite the first"
echo "     commit message if desired."
echo "  3. Push to the new hyperspy-events repository."
echo ""
echo "To verify manually:"
echo "  cd ${DEST_DIR}"
echo "  git shortlog -sne"
echo "  git log --oneline --graph --all | head -20"
