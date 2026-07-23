# Context — The company runs GitLab, and a release just shipped from a branch

The team's roles moved to the internal GitLab, and the old GitHub workflow does
not translate. The first attempt made things worse: the publish job had no
condition on it, so a merge to a feature branch pushed a release to Galaxy that
nobody had approved. Publishing is not a step in a test pipeline. It is what
happens when, and only when, someone deliberately tags a version.

Your mission, from the project directory:

1. Lay the pipeline out in **three stages**, lint then test then release, so a
   job never runs before the one that could have stopped it.
2. Spread the test stage over a **distribution and version matrix**, in parallel,
   and cache the Python dependencies between runs.
3. Gate the release job so it triggers **only on a Git tag**, never on a branch
   push and never on a merge request.
4. Have the release job publish to Galaxy with its token, and keep that token out
   of every other stage.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-gitlab/
