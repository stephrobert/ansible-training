# Your team's automation does not fit in a role any more

## The situation

The team's shared automation has outgrown what a role can carry. There is a role
for nginx, a Python module someone wrote to health-check the app, and three
playbooks that tie them together, each living in its own repository with its own
version, and no version of the set as a whole. Users install three things and hope
the combination works. Besides, the platform the company publishes to no longer
accepts standalone roles at all.

Your mission, from **control-node.lab**:

1. Scaffold a **collection** under your namespace and fill in its manifest:
   namespace, name, version, dependencies and tags. This is now the versioned unit.
2. Bring in a **role**, and add a **Python module** of your own with the
   documentation, examples and return block a module is expected to carry.
3. Account for the standard layout: what belongs in plugins, roles, playbooks,
   meta and tests, and why a module cannot just be dropped anywhere.
4. **Build the tarball** and check the collection passes sanity, because a
   collection that fails sanity is not distributable.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/creer-collection-custom/ (in French)

## 🎯 Challenge — Initialize and build your minimalist collection

### ✅ Objective

Initialize a collection **`student.lab95`**, add **a Python module** to it that returns `"Hello, lab95!"`, build the tarball, and prove that the structure passes `ansible-test sanity --docker default --test ansible-doc`.

| Element | Expected value |
| --- | --- |
| Namespace | `student` |
| Collection name | `lab95` |
| Version | `1.0.0` |
| Custom module | `plugins/modules/lab95_hello.py` that returns `msg="Hello, lab95!"` |
| Tarball | `build/student-lab95-1.0.0.tar.gz` |
| `galaxy.yml` tags | at least `[demo, lab95]` |

### 🧩 Stuck?

```bash
dsoxlab hint collections-creer-custom
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
cd labs/collections/creer-custom/challenge/
# Follow the steps above to produce build/student-lab95-1.0.0.tar.gz
```

### 🧪 Automated validation

```bash
pytest -v labs/collections/creer-custom/challenge/tests/
```

The pytest test validates the **generated structure**: tarball present, compliant galaxy.yml, Python module with `DOCUMENTATION` + `EXAMPLES` + `RETURN`.

### 🧹 Reset

```bash
dsoxlab clean collections-creer-custom
```

### 💡 Going further

- **`ansible-test sanity --docker default --test ansible-doc`** in the collection.
- **`ansible-galaxy collection publish ...`** to Galaxy (API token required).
- **`changelogs/fragments/`**: one YAML per PR rather than a monolithic CHANGELOG.rst.
