# Context — "It works on my machine" is not a test report

The `webserver` role passes on your laptop and breaks at your colleague's. Every
review ends the same way: someone claims the role is fine, nobody can prove it,
and the only way to check is to burn a VM and eyeball the result. Before your
team can automate anything, it needs a test harness it can read and trust, and
a shared vocabulary for what "tested" actually means.

Your mission, from the project directory:

1. Open the scenario shipped in `molecule/default/` and account for each of its
   three files: what creates the instance, what applies the role, what asserts
   the result.
2. Identify the **driver** (what the instance runs on), the **platforms** (which
   instances get created) and the **verifier** (who judges the outcome).
3. Walk the full cycle from creation to destruction, and place the
   **idempotence** step: what it re-runs, and what a failure there really means.
4. Confirm the scenario is standard-compliant, not just present.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tdd-molecule-introduction/
