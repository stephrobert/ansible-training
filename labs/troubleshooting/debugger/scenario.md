# Context — Ninety tasks to replay for a one-word fix

The deployment play dies at task 91 on **db1.lab**: an undefined variable, and no
way to know what it should have been. So you guess, edit the YAML, and re-run the
whole thing from the top. Ninety tasks, twelve minutes, wrong guess. Second
attempt: ninety tasks, twelve minutes. Every iteration of a one-word fix costs a
coffee break, and the run gives you no chance to look around at the moment it
actually knows something.

Your mission, from **control-node.lab**:

1. Arm the play so a failing task **opens a session instead of ending the run**,
   at the exact point where the state is still available.
2. From there, inspect what the run knows: the task as it was resolved, the
   variables in scope, and the module's own result.
3. Fix the failure **live**, by supplying the missing value in the running session
   rather than in the file, and **replay just that task** to confirm your guess.
4. Once the run finishes, commit the fix to the playbook properly, so the value no
   longer depends on someone being at the keyboard.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/debugger-interactif/
