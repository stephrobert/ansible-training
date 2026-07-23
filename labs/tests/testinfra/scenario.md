# Context — The YAML assertions have outgrown YAML

Your `verify.yml` has become a wall. Checking eight packages means eight
near-identical blocks, each with its own `register` and its own `assert`. When
one fails, the report says a task failed, not which package. The reviewer asked
for coverage of the service, the socket, the config file and the users, and the
YAML is now longer than the role it tests. The assertions are not wrong, they
have simply outgrown the language they are written in.

Your mission, from the project directory:

1. Switch the scenario's **verifier** to the Python one, and make the cycle run
   the new assertions in place of the YAML ones.
2. Rewrite the checks against the live instance: package installed, service
   running, socket listening, config file present, users and groups as expected.
3. Collapse the repetitive cases into a **single parametrized test**, so eight
   packages cost one test and each failure names its own case.
4. Argue the trade-off: when the YAML verifier is still the right call, and when
   Python earns its dependency.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-testinfra/
