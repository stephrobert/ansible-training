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

## 🧩 Stuck?

```bash
dsoxlab hint ee-builder-custom
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

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
