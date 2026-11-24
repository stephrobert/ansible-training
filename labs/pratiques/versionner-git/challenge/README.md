# A playbook nobody can roll back

## The situation

Your team keeps its playbooks in a shared folder. Last week someone overwrote
`site.yml`, the change broke production, and there was no way to see what it
looked like before. No history, no blame, no rollback. The fix is not a fancy
platform: it is Git, used the way the EX294 objective *"Manage content in a git
repository"* expects it, and nothing more.

Everything happens on **your own control node**. No managed node, no remote
forge: a local **bare** repository plays the role of the server, so you practice
`push` without a network.

Your mission:

1. **Initialize** a Git repository for a small playbook project, on branch
   `main`.
2. Set a **local author identity** on that repository.
3. **Track and commit** the playbooks, then add a second playbook in its own
   commit so the repository has a real **history**.
4. **Push** the history to a local bare repository and confirm it arrived
   (same commit on both sides).

Keep it at the level of the objective: no CI, no GitOps, no distant forge. Just
init, add, commit, push, done right.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/versionner-git/ (in French)

## 🎯 Challenge — Versioning your playbooks with Git

### ✅ Objective

Write a Bash script `solution.sh` at the root of **this directory**
(`labs/pratiques/versionner-git/challenge/solution.sh`) that automates the whole
versioning cycle, in an **isolated folder** `challenge/work/` (never in
the ansible-training repo's Git repository).

The script must:

1. Start from a clean state, then **initialize** a Git repo in
   `challenge/work/playbooks` on the `main` branch.
2. Set a **local author identity** (`git config user.name` and
   `user.email`).
3. Create **playbooks** (at least one `.yml`) and **track** them (`git add`).
4. **Commit** with a non-empty message, then add a **second commit**
   to build a history.
5. Finish with a **clean working tree** (everything is committed).
6. Set up a **local bare repo** in `challenge/work/playbooks.git`
   (`git init --bare`), add it as `origin`, and **push** the `main`
   branch to it.
7. **Exit 0** if everything went well.

Skeleton to complete:

```bash
#!/usr/bin/env bash
set -euo pipefail

# ABSOLUTE paths, derived from the script location: the workdir is isolated
# and no git command can climb up to the parent repo.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="$SCRIPT_DIR/work"
REPO="$WORKDIR/playbooks"
BARE="$WORKDIR/playbooks.git"

# 0. Start from a clean state (replayable lab).
rm -rf "$WORKDIR"; mkdir -p "$REPO"

# 1. Write the playbooks in "$REPO" (site.yml, etc.).
#    Tip: cat > "$REPO/site.yml" <<'EOF' ... EOF

# 2. git -C "$REPO" init ???   # main branch
# 3. git -C "$REPO" config ??? # local identity

# 4. git -C "$REPO" add ???    # track the files
#    git -C "$REPO" commit ??? # non-empty message
#    (add a second playbook + a second commit)

# 5. git init --bare ??? "$BARE"
#    git -C "$REPO" remote add origin "$BARE"
#    git -C "$REPO" push ???   # push main
```

> ⚠️ **Bash trap**: in the `cat <<'EOF'`, keep the delimiter between
> single quotes (`<<'EOF'`) to avoid any interpretation, and beware of
> single quotes in commit messages within double quotes.

### 🧪 Validation

The tests **do not inspect the text** of your script (that would be forgeable):
they run `solution.sh`, then query the **real state** of the produced Git
repo (`git log`, `git ls-files`, `git ls-remote`, `git config --local`).

```bash
pytest -v labs/pratiques/versionner-git/challenge/tests/
```

What is proven:

- a repo really initialized (`.git/` + `rev-parse --is-inside-work-tree`);
- **tracked** playbooks (`git ls-files` non-empty);
- a **history** (at least two commits on the `main` branch), a non-empty
  **message**, a **local identity** set;
- a **clean tree** (nothing forgotten at commit);
- a **push received** by the bare (same SHA as the local HEAD).

### 🚀 Going further

- Add a `git tag v1.0` after the second commit and check it with
  `git tag -l`.
- Clone the bare elsewhere (`git clone challenge/work/playbooks.git /tmp/clone`)
  and observe that the history is intact.
