# 🎯 Challenge — Build a custom EE with `ansible-builder`

## ✅ Objective

Produce the 5 files required to build a custom **v3 schema** EE. A sixth file, `configs/ansible.cfg`, is delivered and must be kept as-is:

| File | Expectation |
| --- | --- |
| `execution-environment.yml` | `version: 3`. `images.base_image.name` contains `community-ee-minimal`. `dependencies.ansible_core.package_pip` pinned with `==`. |
| `requirements.yml` | Every collection declares `version:` (no floating `>=` range). |
| `requirements.txt` | Every Python dependency pinned with `==`. |
| `bindep.txt` | Contains `[platform:rpm]` (RHEL system deps). |
| `build-ee.sh` | Executable. Uses `--container-runtime podman`. |
| `configs/ansible.cfg` | Delivered. Keep `host_key_checking = False` (injected into the EE). |

## 🧩 Hints

### `execution-environment.yml` (v3 schema)

```yaml
---
version: 3

images:
  base_image:
    name: ???                 # ghcr.io/ansible-community/community-ee-minimal:latest

dependencies:
  ansible_core:
    package_pip: ???          # ansible-core==2.18.0  (strict pin, not >=)
  ansible_runner:
    package_pip: ansible-runner==2.4.0
  galaxy: requirements.yml
  python: requirements.txt
  system: bindep.txt
```

### `requirements.yml` (pinned collections)

```yaml
---
collections:
  - name: community.docker
    version: ???              # e.g.: 3.10.4
  - name: ansible.posix
    version: ???              # e.g.: 1.5.4
```

### `requirements.txt` (pinned Python)

```text
???==???        # each Python dependency pinned to an exact version
```

Check the real versions with `pip index versions <package>`.

### `bindep.txt` (system deps)

```text
[platform:???]  # the profile of UBI/RHEL bases
???             # the binaries your collections need (git...)
```

### `build-ee.sh`

```bash
cat > build-ee.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
ansible-builder build \
    --container-runtime ???                  # podman (not docker)
    --tag ???                                 # localhost/lab86-custom-ee:latest
    --verbosity 2
SH
chmod +x build-ee.sh
```

> 💡 **Pitfalls**:
>
> - **v3 schema mandatory**: forgetting `version: 3` makes
>   `ansible-builder` fail with a cryptic error. The pytest test
>   checks it explicitly.
> - **Strict `==` pinning**: `ansible_core: { package_pip: ansible-core==2.18.0 }`.
>   A `>=2.18.0` range can break build reproducibility (the
>   installed version depends on the build date).
> - **Collections**: every entry must have `version:` (no
>   `latest`). The pytest test scans `requirements.yml` and rejects if
>   absent.
> - **`bindep.txt`**: the `[platform:rpm]` header is essential for
>   RHEL/AlmaLinux builds. For Debian, add `[platform:dpkg]`.
> - **`localhost/`** in the tag: convention for local images
>   not pushed. Without this prefix, Podman may try to look for the image
>   on Docker Hub.

## 🚀 Launch

```bash
cd labs/ee/builder-custom/
./build-ee.sh
podman run --rm localhost/lab86-custom-ee:latest ansible --version
```

## 📓 Command log

Record in `challenge/solution.sh` the commands you ran (build,
podman checks). This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ee/builder-custom/challenge/tests/
```

The tests check the semantics of your 5 files and, if
ansible-builder is installed, run `ansible-builder create` to
prove that the definition is accepted by the tool.

## 🧹 Reset

```bash
dsoxlab clean ee-builder-custom
```

## 💡 Going further

- **`additional_build_steps`** in `execution-environment.yml`:
  inject arbitrary `RUN` commands (custom CA cert, debug tools).
- **Multi-stage build**: a separate `builder_image` to reduce the
  size of the final image.
- **Sign the image**: `cosign sign localhost/lab86-custom-ee:latest`
  after build (see lab 87 CI).
