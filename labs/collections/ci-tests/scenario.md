# Context — Your collection ships Python, and Python is where it will break

A role is YAML, and YAML mostly survives an upgrade. Your collection ships a
compiled-against-reality Python module, and it breaks on things a role never
notices: a Python version that removed a stdlib call, an `ansible-core` that
changed a module_utils import. Users hit it, you do not, because your machine
runs exactly one combination. And the workflow that is supposed to catch it uses
floating action tags and a token with more rights than it needs.

Your mission, from the project directory:

1. Cross **`ansible-core` versions with Python versions** in a matrix, at least
   two of each, so the combinations your users actually run get tested.
2. Run the collection's own **sanity and unit tests** in containers, so the result
   does not depend on what happens to be installed on the runner.
3. Harden the workflow itself: **no permissions at all globally**, each job
   granted only what it needs, and **no credentials left behind** in the checkout.
4. **Pin every third-party action by commit SHA**: a tag can be moved under you,
   and a supply-chain linter will tell you so.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/pipeline-ci/
