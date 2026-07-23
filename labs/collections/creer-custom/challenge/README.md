# 🎯 Challenge — Initialize and build your minimalist collection

## ✅ Objective

Initialize a collection **`student.lab95`**, add **a Python module** to it that returns `"Hello, lab95!"`, build the tarball, and prove that the structure passes `ansible-test sanity --docker default --test ansible-doc`.

| Element | Expected value |
| --- | --- |
| Namespace | `student` |
| Collection name | `lab95` |
| Version | `1.0.0` |
| Custom module | `plugins/modules/lab95_hello.py` that returns `msg="Hello, lab95!"` |
| Tarball | `build/student-lab95-1.0.0.tar.gz` |
| `galaxy.yml` tags | at least `[demo, lab95]` |

## 🧩 Stuck?

```bash
dsoxlab hint collections-creer-custom
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
cd labs/collections/creer-custom/challenge/
# Follow the steps above to produce build/student-lab95-1.0.0.tar.gz
```

## 🧪 Automated validation

```bash
pytest -v labs/collections/creer-custom/challenge/tests/
```

The pytest test validates the **generated structure**: tarball present, compliant galaxy.yml, Python module with `DOCUMENTATION` + `EXAMPLES` + `RETURN`.

## 🧹 Reset

```bash
dsoxlab clean collections-creer-custom
```

## 💡 Going further

- **`ansible-test sanity --docker default --test ansible-doc`** in the collection.
- **`ansible-galaxy collection publish ...`** to Galaxy (API token required).
- **`changelogs/fragments/`**: one YAML per PR rather than a monolithic CHANGELOG.rst.
