# Lab 75 — Auditing an Ansible role before adoption

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisite: Ansible installed. No VMs needed (purely local lab + reading).

## 🧠 Recap

🔗 [**Auditing a third-party Ansible role**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/auditer-role-existant/)

Before adopting a Galaxy or GitHub role in your project (and therefore
**running it with `become: true`** on your production servers), put it
through an **audit checklist**. Third-party roles are **arbitrary
code** that will run as root on your machines.

| Risk | If not audited |
| --- | --- |
| Maintenance | Role abandoned for 3 years, Ansible 2.18 breaking change |
| Security | Unencrypted HTTP download, hardcoded secret |
| Quality | No idempotence, breaks on 2nd run |
| Compat | RHEL 7 only targets, your prod is RHEL 10 |

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Evaluate a role on **6 axes**: maintainer, quality, security, tests,
   compat, idempotence.
2. Read `meta/main.yml` to identify the **supported platforms**.
3. Detect the classic **anti-patterns** (missing FQCN, hardcoded secrets,
   `command:` without `creates:`).
4. Compute a numeric **audit score** (9-10/10 = adopt).
5. **Decide**: adopt / fork / reject.

## 🔧 Preparation

```bash
# For the examples: install a famous Galaxy role
ansible-galaxy role install geerlingguy.docker
ls ~/.ansible/roles/geerlingguy.docker/
```

## ⚙️ Directory tree

```text
labs/galaxy/auditer-role-existant/
├── README.md
├── AUDIT_CHECKLIST.md       ← shipped checklist (to study)
├── roles/
│   └── webserver/            ← healthy example role (for comparison)
└── vendor/
    └── thirdparty_backup/    ← third-party role TO AUDIT (challenge)
```

## 📚 Exercise 1 — Read `AUDIT_CHECKLIST.md`

The checklist covers **6 sections**:

| Section | Key items |
| --- | --- |
| ✅ Maintainer | Author, last commit date, CHANGELOG |
| ✅ Code quality | meta/main.yml, argument_specs, FQCN, prefixed variables |
| ✅ Security | Secrets, HTTPS, checksum, permissions, become |
| ✅ Tests | molecule, verify, ansible-lint, CI/CD |
| ✅ Compatibility | Platforms, min_ansible_version, obsolete deps |
| ✅ Idempotence | changed=0 on 2nd run, justified changed_when |
| ✅ Maintainability | Comments, defaults, structure |

## 📚 Exercise 2 — Practical audit of `geerlingguy.docker`

```bash
cd ~/.ansible/roles/geerlingguy.docker/

# Check last commit date
git log -1 --format="%cd" 2>/dev/null || stat -c '%y' meta/main.yml

# Check FQCN (find the non-FQCN ones)
grep -rE "^\s*-\s*(dnf|apt|copy|template|file|service):" tasks/

# Check presence of argument_specs
ls meta/argument_specs.yml 2>/dev/null

# Check molecule scenario
ls molecule/default/molecule.yml 2>/dev/null
```

🔍 **Observation**: `geerlingguy.docker` is a **Galaxy reference role**:
it should pass most of the checkpoints.

## 📚 Exercise 3 — Detect the classic red flags

```bash
# Anti-pattern 1: hardcoded secrets
grep -rE "(password|api_key|secret).*=.*[a-zA-Z0-9]{8,}" roles/

# Anti-pattern 2: insecure HTTP URLs
grep -rE "http://" roles/

# Anti-pattern 3: downloads without checksum
grep -B2 -A5 "get_url:" roles/ | grep -v "checksum:"

# Anti-pattern 4: command/shell without creates/removes
grep -rB2 -A5 "command:\|shell:" roles/ | grep -v "creates:\|removes:\|changed_when:"
```

## 📚 Exercise 4 — Audit score

| Score | Decision |
| --- | --- |
| **9-10/10** sections OK | ✅ Adopt without reservation. |
| **7-8/10** | ⚠️ Acceptable with additional audit. |
| **5-6/10** | 🔧 Risky. Fork or look for an alternative. |
| **< 5/10** | ❌ Reject. Maintenance too costly. |

🔍 **Observation**: a score < 5/10 on a third-party role is a strong signal
to **write your own** rather than inherit the technical debt.

## 📚 Exercise 5 — Audit the lab's `roles/webserver/`

The role shipped in `roles/webserver/` is a **simple** role. Run it through
the checklist:

- [ ] `meta/main.yml` present? Which `galaxy_info` fields?
- [ ] `meta/argument_specs.yml` present?
- [ ] `tasks/main.yml` uses FQCN?
- [ ] `defaults/main.yml` documents the variables?
- [ ] `README.md` present?

Compute its score out of 10.

## 🔍 Observations to note

- **Auditing** = mandatory before production adoption.
- A role without **`molecule/`** = no guarantee it works.
- A role without **`argument_specs.yml`** = you must validate the
  inputs yourself at runtime.
- **CHANGELOG.md missing** or empty = the maintainer does not invest in
  communicating breaking changes.
- **Prefer Red Hat / geerlingguy / ansible-collections**: these authors
  have a verifiable track record.

## 🤔 Reflection questions

1. You find a perfect role except that it downloads a binary over HTTP
   (not HTTPS). Do you adopt it? What mitigations do you consider?

2. Difference between **forking** a role and writing your own? What criteria
   to choose?

3. On what criteria do you rate a finding **CRITICAL** (immediate reject) vs
   **MAJOR** (additional audit)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`ansible-lint --profile=production`**: run on the audited role.
- **`safety check`** on any `requirements.txt`.
- **`grype`** or **`trivy`**: vulnerability scan on the referenced Docker
  images.
- **Automated audit**: integrate the role into a repo + run
  Molecule to validate in practice.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/galaxy/auditer-role-existant/
```
