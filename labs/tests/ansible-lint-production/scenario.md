# Context — The review that keeps having the same argument

Every pull request on the team's roles reopens the same debate: bare module
names, unnamed tasks, a `shell:` where a dedicated module exists, `yes` instead
of `true`. The reviewers are tired of being a linter. Then last month someone
committed a private key, and it sat in the history for three days before anyone
noticed. Style is negotiable in a review; a leaked key is not. Both belong to a
machine, and the machine should say no before the commit exists.

Your mission, from the project directory:

1. Pin the linter to its **strictest profile**, the one expected of code that
   ships to production, and see what it says about the role as it stands.
2. Add a strict YAML policy on top: the ambiguous booleans and the sloppy
   formatting stop passing review because they stop passing the tool.
3. Wire both into a **Git hook** that runs on every commit, so non-conforming
   code never reaches the branch, and CI merely confirms what you already know.
4. Add a hook that **blocks secret leaks** at commit time, private keys included.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ansible-lint-production-profile/
