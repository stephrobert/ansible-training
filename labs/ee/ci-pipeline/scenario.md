# Context — Your EE was built by hand, and it is nine months old

The custom EE runs everything in production, and it was built on a laptop last
autumn. Since then its base image has collected critical CVEs, nobody rebuilt it
because nobody owns the job, and nobody can prove the image on the registry is
the one that was built: it was pushed from a workstation with a personal token.
An artefact that runs your whole fleet cannot come from someone's afternoon.

Your mission, from the project directory:

1. Build the EE in **CI** instead of on a workstation, so a rebuild is a commit
   away and the CVE clock stops running unattended.
2. **Scan the image and block on it**: a build that finds high or critical
   vulnerabilities must fail the pipeline, not warn in a log nobody reads.
3. **Sign the image** keylessly, so consumers can verify the artefact came from
   your pipeline and not from a workstation, then publish it.
4. Harden the pipeline itself: **pin third-party actions by commit SHA**, keep
   global permissions empty and grant only what each job needs, and leave no
   credentials behind in the checkout.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/exec-playbook/#pipeline-github-actions
