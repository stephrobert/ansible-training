# Context — a playbook nobody can roll back

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
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/versionner-git/
