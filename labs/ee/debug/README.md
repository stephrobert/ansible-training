# Lab 88 — Debug a broken Execution Environment

> 💡 **Prerequisites**: labs 84, 85, 86 completed (you know how to build and test an EE).

## 🧠 Recap

🔗 [**Debugging a broken Execution Environment**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/debug-ee-casse/)

EE definitions break in an often **silent** way: a badly declared schema
makes whole sections ignored, an unresolvable dependency drowns
in verbose logs, and a build that "succeeds" can produce
an unusable image. The page linked above details the classic
pitfalls of ansible-builder.

This lab provides a **deliberately broken** EE (4 planted defects) and asks
you to **diagnose** then **fix** it. The defects are not
listed here: finding them IS the exercise.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Recognize** an EE that builds "OK" but does not contain ansible-core.
2. **Read** the `ansible-builder build --verbosity 2` logs to identify the step that fails.
3. **Diagnose** a nonexistent Galaxy collection.
4. **Diagnose** a nonexistent PyPI version.
5. **Inspect** a built EE with `podman run --rm <ee> ansible --version`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/ee/debug/

# Inspect the buggy file
cat execution-environment-buggy.yml
cat requirements-buggy.yml
cat requirements-buggy.txt
```

## ⚙️ Tree

```text
labs/ee/debug/
├── README.md
├── execution-environment-buggy.yml      ← BROKEN VERSION (4 defects)
├── requirements-buggy.yml
├── requirements-buggy.txt
└── challenge/
    ├── README.md                         ← your mission
    └── tests/                            ← pytest validation
        └── test_functional.py

# To be produced by you (absent from the repo):
# challenge/execution-environment.yml, requirements.yml,
# requirements.txt, bindep.txt
```

## 📚 Exercise 1 — Attempt the buggy build

```bash
ansible-builder build \
  --tag local/lab88-buggy:dev \
  --container-runtime podman \
  --file execution-environment-buggy.yml \
  --context ./context-buggy \
  --verbosity 2
```

🔍 **Read EVERYTHING**: the warnings at the very start of the build matter as much as
the red errors at the end. Note every anomaly before touching a
single file.

## 📚 Exercise 2 : a "successful" build proves nothing

```bash
podman run --rm local/lab88-buggy:dev ansible --version
```

🔍 If this command fails while the build passed, it means a
part of your definition was **silently ignored**. Which build warning
announced it? Which line is missing in the definition so that
`dependencies.*` is actually taken into account?

## 📚 Exercise 3 : check each dependency individually

Do not take the definition at its word: every collection and every
declared Python package must exist where they are supposed to be
downloaded.

```bash
# Does a declared collection really exist, in this version?
ansible-galaxy collection install <namespace.collection>:<version>

# Does a declared Python version really exist on PyPI?
pip index versions <paquet>
```

🔍 **Diagnosis**: note precisely which component fails and why
(Galaxy 404, PyPI no matching distribution...). This diagnosis is what
you will fix in `challenge/`.

## 📚 Exercise 4 : system dependencies

Embedded collections often rely on system binaries
(git, ssh clients...). How does ansible-builder install them in
the image? Which section and which file are missing from the buggy
definition?

## 📚 Exercise 5 : build your fixed version

Once your 4 fixes are placed in `challenge/`:

```bash
cd challenge/
ansible-builder build \
  --tag local/lab88-fixed:dev \
  --container-runtime podman \
  --file execution-environment.yml \
  --context ../context-fixed \
  --verbosity 2

# Check that the EE is actually usable
podman run --rm local/lab88-fixed:dev ansible --version | head -1
podman run --rm local/lab88-fixed:dev ansible-galaxy collection list
```

🔍 **Final validation**: ansible-core present, collections **actually**
installed, Python dependencies resolved.

## 📚 Exercise 6 — Inspect the generated Containerfile

```bash
cat ../context-fixed/Containerfile
```

You see a **multi-stage** build: `base`, `galaxy`, `builder`, `final`. The `final` stage contains only what is useful at runtime (not the Python compilers used to build the wheels).

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must show `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  compliant with best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) over the short name. `ansible-lint --profile
  production` checks it.
- **Targeting convention**: this lab targets your local machine + an existing EE. To adapt it to
  another group, adjust `hosts:` in `lab.yml`/`solution.yml` then rerun.
- **Isolated reset**: `dsoxlab clean <lab-id>` at the lab root cleanly uninstalls
  what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. Why does ansible-builder accept a file without `version:` instead of returning an error?

2. Which Podman command lets you **open an interactive shell in the EE** to inspect the files?

3. How do you **automatically detect** in CI that a built EE does not contain ansible-core?

4. **Podman cache**: modifying `requirements.yml` does not always trigger a rebuild of the galaxy layer. How do you force it?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): the pytest tests
check that your 4 fixed files in `challenge/` each solve one of the
planted defects, and submit your definition to `ansible-builder create`
if the tool is present.

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **`ansible-builder create`** (without `build`): generates the Containerfile without building -> fast debug.
- **`podman build --no-cache`**: forces a full rebuild, useful when the cache hides a bug.
- **`podman run -it --entrypoint /bin/bash <ee>`**: interactive shell in the EE for inspection.
- **`ansible-navigator images --eei <ee>`**: structured TUI exploration.
- **CI smoke test**: a post-build step that runs `ansible --version` in the image and fails if absent.

## 🔍 Security — 2026 best practices

- **Post-build smoke test**: `podman run --rm $TAG ansible --version` must return without error.
- **`--verbosity 2`** at minimum in CI to catch warnings such as "schema v1 default".
- **Pinning by digest** on the base image (`@sha256:abc...`): prevents a silent upstream repush.
- **CI smoke test** on the **critical** collections: `ansible-doc kubernetes.core.k8s` must return.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/ee/debug/lab.yml
ansible-lint labs/ee/debug/challenge/solution.yml
ansible-lint --profile production labs/ee/debug/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
