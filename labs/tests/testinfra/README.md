# Lab 66 — Molecule + testinfra

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisites: Molecule installed (see [lab 62](../../molecule/introduction/))
> + `pipx inject molecule pytest-testinfra`.

## 🧠 Recap

🔗 [**Molecule tests with testinfra**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-testinfra/)

The `verifier: ansible` (lab 62-65) writes assertions in **YAML**, which
is OK but limited. The `verifier: testinfra` writes them in **Python**:

| Approach | Form | Strength |
| --- | --- | --- |
| `verifier: ansible` | YAML + `ansible.builtin.assert` | Simple, no Python dependency |
| `verifier: testinfra` | Python + `pytest-testinfra` | Rich, idiomatic, fixtures, parametrization |

testinfra provides an **idiomatic Python API**:

```python
def test_nginx_running(host):
    assert host.package("nginx").is_installed
    assert host.service("nginx").is_running
    assert host.socket("tcp://0.0.0.0:8080").is_listening
    assert host.file("/etc/nginx/nginx.conf").exists
```

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Configure Molecule to use **`verifier: testinfra`**.
2. Write Python tests with testinfra's **`host`** fixture.
3. Use the **inspectors**: `host.package`, `host.service`,
   `host.file`, `host.socket`, `host.user`, `host.group`, `host.process`.
4. Parametrize a test with **`@pytest.mark.parametrize`** (the Ansible
   `loop` equivalent).
5. Choose between `verifier: ansible` (fast) and `verifier: testinfra`
   (powerful).

## 🔧 Preparation

```bash
pipx inject molecule pytest-testinfra
pipx inject molecule pytest
```

## ⚙️ Tree layout

```text
labs/tests/testinfra/
├── README.md
├── roles/
│   └── webserver/
└── molecule/
    └── default/
        ├── molecule.yml          ← verifier: testinfra
        ├── converge.yml
        └── tests/
            └── test_webserver.py ← Python assertions (≥4)
```

## 📚 Exercise 1 — `molecule.yml` with `verifier: testinfra`

```yaml
verifier:
  name: testinfra
  options:
    v: 1                           # verbose
```

🔍 **Observation**: no `verify.yml`, the tests are in Python in
`molecule/default/tests/`.

## 📚 Exercise 2 — First testinfra test

```python
# molecule/default/tests/test_webserver.py
import pytest


def test_nginx_installed(host):
    assert host.package("nginx").is_installed


def test_nginx_running(host):
    svc = host.service("nginx")
    assert svc.is_running
    assert svc.is_enabled


def test_port_80_listening(host):
    sock = host.socket("tcp://0.0.0.0:8080")
    assert sock.is_listening


def test_nginx_conf_owned_by_root(host):
    f = host.file("/etc/nginx/nginx.conf")
    assert f.exists
    assert f.user == "root"
    assert f.mode == 0o644
```

🔍 **Observation**: the **`host`** fixture is injected automatically
by pytest-testinfra. It represents the Molecule instance.

## 📚 Exercise 3 — Advanced inspectors

```python
def test_nginx_user_exists(host):
    u = host.user("nginx")
    assert u.exists
    assert u.shell in ("/sbin/nologin", "/usr/sbin/nologin")


def test_no_default_index_page(host):
    """The default apache must no longer be there."""
    cmd = host.run("curl -s http://localhost")
    assert "Welcome to nginx" not in cmd.stdout


@pytest.mark.parametrize("port", [80, 443])
def test_ports_listening(host, port):
    """Parametrized test: 80 and 443 must be open."""
    sock = host.socket(f"tcp://0.0.0.0:{port}")
    assert sock.is_listening
```

## 📚 Exercise 4 — Run

```bash
cd labs/tests/testinfra
molecule test
```

🔍 The `verify` phase now runs the Python tests.

## 🔍 Observations to note

- **`verifier: testinfra`** = Python power (fixtures, parametrization,
  inheritance). Prefer it for complex tests.
- **`verifier: ansible`** = YAML simplicity. Good for basic assertions.
  Needs no extra Python env.
- **testinfra inspectors**: `host.package`, `host.service`, `host.file`,
  `host.socket`, `host.user`, `host.group`, `host.process`,
  `host.command`, `host.run`, `host.system_info`. Covers 95% of
  needs.
- **The `lab_host` helper** this repo uses for challenges is based on
  testinfra, so you already know it.

## 🤔 Reflection questions

1. How would you adapt your solution if the target went from **1 host** to
   a fleet of **50 servers**? Which parameters (`forks`, `serial`, `strategy`)
   would you need to tune to keep execution times acceptable?

2. Which alternative Ansible modules could you have used to reach the same
   result? What are their trade-offs (guaranteed idempotence, performance,
   external collection dependencies)?

3. If a playbook step fails mid-run, what is the impact on the hosts already
   processed? How do you make the scenario resumable
   (`block/rescue/always`, `--start-at-task`, `serial`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`host.iptables`**: validate specific netfilter rules.
- **`host.mount_point`**: validate NFS/iSCSI mounts.
- **`host.docker(name)`**: if the instance runs Docker.
- **pytest markers**: skip depending on OS (`@pytest.mark.skipif(host.system_info.distribution == 'debian'`).

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/tests/testinfra/
```
