# No public image fits, and the audit wants to know what runs

## The situation

None of the official EEs work for you. The minimal one lacks the collections your
playbooks call; the fat ones carry hundreds of megabytes you will never use and
an `ansible-core` you do not control. Meanwhile the security team asks a fair
question: what exactly is running on the automation hosts? "Whatever `:latest`
resolved to on build day" is not an answer they will accept, and it is not one
you can reproduce either.

Your mission, from the project directory:

1. Write the recipe for a **custom EE**, on the current schema, based on a minimal
   image and built with Podman.
2. **Pin everything**: `ansible-core`, every collection, every Python dependency
   to an exact version, and declare the system dependencies the image needs.
3. Inspect the container file the build generates, so you know what is being
   assembled instead of trusting a black box.
4. Test the resulting image, then push it to a **private registry** so the team
   consumes a version, not a moving tag.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/ee-builder/ (in French)

## 🎯 Challenge — Build a custom EE with `ansible-builder`

### ✅ Objective

Produce the 5 files required to build a custom **v3 schema** EE. A sixth file, `configs/ansible.cfg`, is delivered and must be kept as-is:

| File | Expectation |
| --- | --- |
| `execution-environment.yml` | `version: 3`. `images.base_image.name` contains `community-ee-minimal`. `dependencies.ansible_core.package_pip` pinned with `==`. |
| `requirements.yml` | Every collection declares `version:` (no floating `>=` range). |
| `requirements.txt` | Every Python dependency pinned with `==`. |
| `bindep.txt` | Contains `[platform:rpm]` (RHEL system deps). |
| `build-ee.sh` | Executable. Uses `--container-runtime podman`. |
| `configs/ansible.cfg` | Delivered. Keep `host_key_checking = False` (injected into the EE). |

### 🧩 Stuck?

```bash
dsoxlab hint ee-builder-custom
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
cd labs/ee/builder-custom/
./build-ee.sh
podman run --rm localhost/lab86-custom-ee:latest ansible --version
```

### 📓 Command log

Record in `challenge/solution.sh` the commands you ran (build,
podman checks). This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ee/builder-custom/challenge/tests/
```

The tests check the semantics of your 5 files and, if
ansible-builder is installed, run `ansible-builder create` to
prove that the definition is accepted by the tool.

### 🧹 Reset

```bash
dsoxlab clean ee-builder-custom
```

### 💡 Going further

- **`additional_build_steps`** in `execution-environment.yml`:
  inject arbitrary `RUN` commands (custom CA cert, debug tools).
- **Multi-stage build**: a separate `builder_image` to reduce the
  size of the final image.
- **Sign the image**: `cosign sign localhost/lab86-custom-ee:latest`
  after build (see lab 87 CI).
