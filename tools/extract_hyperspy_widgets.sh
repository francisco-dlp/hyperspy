#!/usr/bin/env bash
# Standalone extraction bootstrap for the hyperspy-widgets package.
#
# Usage:
#   ./tools/extract_hyperspy_widgets.sh [--source SOURCE_REPO] [--target WORK_DIR]
#
# Defaults:
#   --source  https://github.com/hyperspy/hyperspy.git
#   --target  /tmp/hyperspy-widgets-extract
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
#      packages/hyperspy_widgets/EXTRACTION_MANIFEST.md plus exact path
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
WORK_DIR="/tmp/hyperspy-widgets-extract"

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

DEST_DIR="${WORK_DIR}/hyperspy-widgets"

echo "==> HyperSpy Widgets Standalone Extraction Bootstrap"
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
# 2. Fresh clone into a disposable directory
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
# 3. If the staged package exists but is not yet committed (e.g. during
#    development), add and commit it so filter-repo can include it.
# ---------------------------------------------------------------------------
if [ -d packages/hyperspy_widgets ]; then
    git add packages/hyperspy_widgets
    if ! git diff --cached --quiet; then
        git -c user.email="extract@local" \
            -c user.name="Extraction Bot" \
            commit -m "[tmp] stage package for extraction"
    fi
elif [ -d "${SOURCE_REPO}/packages/hyperspy_widgets" ]; then
    # Local clone does not copy untracked files; copy them explicitly.
    echo "    Copying uncommitted staged-package files from local source..."
    mkdir -p packages
    cp -r "${SOURCE_REPO}/packages/hyperspy_widgets" packages/hyperspy_widgets
    git add packages/hyperspy_widgets
    git -c user.email="extract@local" \
        -c user.name="Extraction Bot" \
        commit -m "[tmp] stage package for extraction"
fi

# ---------------------------------------------------------------------------
# 4. Run git-filter-repo
#    Include set is authoritative per EXTRACTION_MANIFEST.md.
# ---------------------------------------------------------------------------
echo "==> Running git filter-repo (this may take a while)..."

# Build the command in an array to keep it readable and safe.
cmd=(
    git-filter-repo
    --force
    # Staged package subtree
    --path packages/hyperspy_widgets/src/hyperspy_widgets
    --path packages/hyperspy_widgets/tests
    --path packages/hyperspy_widgets/docs
    --path packages/hyperspy_widgets/pyproject.toml
    --path packages/hyperspy_widgets/README.md
    --path packages/hyperspy_widgets/EXTRACTION_MANIFEST.md
    # Legacy widget core paths whose history must be preserved
    --path hyperspy/drawing/widget.py
    --path hyperspy/drawing/widgets.py
    --path hyperspy/drawing/_widgets/__init__.py
    --path hyperspy/drawing/_widgets/vertical_line.py
    --path hyperspy/drawing/_widgets/horizontal_line.py
    --path hyperspy/drawing/_widgets/label.py
    --path hyperspy/drawing/_widgets/line2d.py
    --path hyperspy/drawing/_widgets/range.py
    --path hyperspy/drawing/_widgets/rectangles.py
    --path hyperspy/drawing/_widgets/circle.py
    --path hyperspy/drawing/_widgets/polygon.py
    --path hyperspy/drawing/_widgets/scalebar.py
    # Legacy helper dependencies whose authorship must be preserved
    --path hyperspy/drawing/utils.py
    --path hyperspy/misc/math_tools.py
    # Path renames: staged package -> clean standalone layout
    --path-rename packages/hyperspy_widgets/src/hyperspy_widgets:src/hyperspy_widgets
    --path-rename packages/hyperspy_widgets/tests:tests
    --path-rename packages/hyperspy_widgets/docs:docs
    --path-rename packages/hyperspy_widgets/pyproject.toml:pyproject.toml
    --path-rename packages/hyperspy_widgets/README.md:README.md
    --path-rename packages/hyperspy_widgets/EXTRACTION_MANIFEST.md:EXTRACTION_MANIFEST.md
    # Path renames: legacy widget core -> merge into staged package paths
    --path-rename hyperspy/drawing/widget.py:src/hyperspy_widgets/widget.py
    --path-rename hyperspy/drawing/widgets.py:src/hyperspy_widgets/widgets.py
    --path-rename hyperspy/drawing/_widgets/__init__.py:src/hyperspy_widgets/_widgets/__init__.py
    --path-rename hyperspy/drawing/_widgets/vertical_line.py:src/hyperspy_widgets/_widgets/vertical_line.py
    --path-rename hyperspy/drawing/_widgets/horizontal_line.py:src/hyperspy_widgets/_widgets/horizontal_line.py
    --path-rename hyperspy/drawing/_widgets/label.py:src/hyperspy_widgets/_widgets/label.py
    --path-rename hyperspy/drawing/_widgets/line2d.py:src/hyperspy_widgets/_widgets/line2d.py
    --path-rename hyperspy/drawing/_widgets/range.py:src/hyperspy_widgets/_widgets/range.py
    --path-rename hyperspy/drawing/_widgets/rectangles.py:src/hyperspy_widgets/_widgets/rectangles.py
    --path-rename hyperspy/drawing/_widgets/circle.py:src/hyperspy_widgets/_widgets/circle.py
    --path-rename hyperspy/drawing/_widgets/polygon.py:src/hyperspy_widgets/_widgets/polygon.py
    --path-rename hyperspy/drawing/_widgets/scalebar.py:src/hyperspy_widgets/_widgets/scalebar.py
    # Path renames: legacy helpers -> preserved for attribution
    --path-rename hyperspy/drawing/utils.py:src/hyperspy_widgets/_legacy_drawing_utils.py
    --path-rename hyperspy/misc/math_tools.py:src/hyperspy_widgets/_legacy_math_tools.py
)

"${cmd[@]}"

# ---------------------------------------------------------------------------
# 5. Amend the temporary staging commit to use a real author from history
#    so no synthetic bootstrap-only author appears in git shortlog.
# ---------------------------------------------------------------------------
if git log --oneline -1 | grep -q '\[tmp\] stage package for extraction'; then
    real_author="$(git log -1 --format='%an <%ae>' HEAD~1)"
    GIT_COMMITTER_NAME="$(git log -1 --format='%cn' HEAD~1)" \
    GIT_COMMITTER_EMAIL="$(git log -1 --format='%ce' HEAD~1)" \
    git commit --amend -m "chore: bootstrap standalone hyperspy-widgets extraction" \
        --author="${real_author}" --no-edit
fi

# ---------------------------------------------------------------------------
# 6. Verify layout
# ---------------------------------------------------------------------------
echo ""
echo "==> Verifying extracted layout..."

expected_dirs=(
    src/hyperspy_widgets
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
# 7. Verify contributor attribution survives
# ---------------------------------------------------------------------------
echo ""
echo "==> Verifying contributor attribution..."
author_count=$(git shortlog -sne HEAD | wc -l | tr -d ' ')
echo "    Unique authors in extracted history: ${author_count}"

sample_authors=$(git log --format='%an <%ae>' | sort -u | head -5)
echo "    Sample authors:"
echo "${sample_authors}" | sed 's/^/      /'

# ---------------------------------------------------------------------------
# 8. Print next steps
# ---------------------------------------------------------------------------
echo ""
echo "==> Extraction complete: ${DEST_DIR}"
echo ""
echo "Next steps:"
echo "  1. Inspect src/hyperspy_widgets/_legacy_*.py and trim/copy the"
echo "     narrow helper logic (picker_kwargs, on_figure_window_close,"
echo "     closest_nice_number) into package-local modules."
echo "  2. Update pyproject.toml for standalone release (version bump,"
echo "     classifiers, optional doc/test dependencies)."
echo "  3. Remove the temporary extraction commit and rewrite the first"
echo "     commit message if desired."
echo "  4. Push to the new hyperspy-widgets repository."
echo ""
echo "To verify manually:"
echo "  cd ${DEST_DIR}"
echo "  git shortlog -sne"
echo "  git log --oneline --graph --all | head -20"
