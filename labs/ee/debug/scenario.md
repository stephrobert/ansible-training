# Context — The build says success and the image cannot run Ansible

A colleague left you an EE recipe and a problem. The build prints no error worth
stopping for, the image lands on the registry, and the first playbook that tries
to use it dies instantly: there is no `ansible` command inside. Somewhere in
those files, several mistakes are hiding, and the nastiest one is the mistake
that does not fail. The build is not lying to you, you are reading the wrong
line of its output.

Your mission, from the project directory:

1. Try to build the **broken recipe** as it stands, with verbosity turned up, and
   inspect the resulting image rather than trusting the build's exit code.
2. Explain why the image ships **without `ansible-core`** even though the recipe
   plainly asks for it, and find the warning that announced it.
3. Track down the two dependencies that do not exist, one collection and one
   Python version, and prove each is missing at the source rather than blaming
   the network or a proxy.
4. Produce a **fixed set of files**, complete with the system dependencies the
   original forgot, build it, and prove the image now carries what it claims.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/debug-ee-casse/
