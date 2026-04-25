#!/usr/bin/env bash
# Lance ansible-lint puis yamllint sur tout le repo.

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${LAB_DIR}"

log()  { echo -e "\033[0;34m[lint-all]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
fail() { echo -e "\033[0;31m[FAIL]\033[0m $*" >&2; }

EXIT=0

log "yamllint..."
if yamllint . ; then
    ok "yamllint"
else
    fail "yamllint"
    EXIT=1
fi

log "ansible-lint..."
if ansible-lint --strict ; then
    ok "ansible-lint"
else
    fail "ansible-lint"
    EXIT=1
fi

exit "${EXIT}"
