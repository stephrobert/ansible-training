# Context — Tests written after the code always agree with the code

The team's roles are all tested, and the tests never catch anything. The reason
is visible in the git history: the tasks are written first, the assertions are
written afterwards, and they end up describing what the code happens to do
rather than what was asked for. You are starting a new `users` role, and this
time the order is reversed: nothing gets written until a test demands it.

Your mission, from the project directory:

1. Write the **assertions first**, on a role whose tasks do not exist yet, and
   run the cycle to watch them fail. A test that has never failed proves nothing.
2. Declare the role's input contract before its code: the shape and type of the
   list of users to create, so a bad call is rejected up front.
3. Only then write the **minimum** tasks that turn the assertions green, looping
   over the requested users rather than hardcoding any of them.
4. Refactor the role once green, and use the suite as your safety net: it must
   stay green through the rewrite, or it was never protecting you.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-tdd-cycle/
