# The role that ran when it was told not to

## The situation

A colleague guarded the `webserver` role with a `when:` and a feature flag, and
the role deployed anyway on a host that was supposed to stay untouched. The
condition was there, in plain sight, and it was ignored. The bug is not in the
`when:`, it is in the way the role was called: two of the three ways to invoke a
role resolve at parse time, and only one of them evaluates conditions at runtime.

Your mission, from the project directory, against **db1.lab**:

1. Deploy the `webserver` role the standard way, at play level, listening on
   port 8080: package, service, page, everything provable on the target.
2. **Import** the role's trace entry point statically, guarded by a feature
   flag that is off, and show both faces of "static": the trace file must NOT
   appear, yet the role's default variables must be visible to the play,
   because the role was loaded at parse time anyway.
3. **Include** the same entry point dynamically, under a condition that only
   exists at runtime (the live state of the nginx service), and show the
   mirror image: the trace file appears, but the role's variables stay
   private.
4. State the rule you would give your team: which form for a systematic role,
   which for a tag-driven one, which for a flag decided at runtime.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/consommer-role/ (in French)

## 🎯 Challenge — Consume the `webserver` role the 3 ways, and prove it

### ✅ Objective

Write `challenge/solution.yml`: **3 plays** on db1.lab that consume the
`webserver` role shipped in `roles/`, each through a different form
(`roles:`, `import_role`, `include_role`). The tests do not read your
YAML: they check **the state of db1.lab**, including the traces that
distinguish the static (resolved at parsing) from the dynamic (resolved at runtime).

The role provides two entry points:

- `tasks/main.yml`: installs and configures nginx (the real deployment);
- `tasks/stamp.yml`: writes `/tmp/consommer-{{ webserver_invocation }}.txt`,
  the trace of the invocation. The caller provides `webserver_invocation`.

### 🧩 Expected contract

#### Play 1 — `roles:` (the systematic deployment)

Consume `webserver` at play level, with `webserver_listen_port: 8080`.

State checked on db1: `nginx` package installed, service **started and
enabled**, nginx **listening on 8080**, the role's default welcome page
in place (mode `0644`).

#### Play 2 — `import_role` (static), guarded by a flag TURNED OFF

In a play with `vars: {deploy_extras: false}`:

1. Import (`ansible.builtin.import_role`) the `stamp.yml` entry point with
   `webserver_invocation: import`, guarded by `when: deploy_extras | bool`.
2. Then a task that writes `/tmp/consommer-vars-import.txt` with the
   content `package={{ webserver_package | default('UNDEFINED') }}`,
   mode `0644`.

State checked: `/tmp/consommer-import.txt` **does not exist** (the `when:`
applied to each imported task), BUT
`/tmp/consommer-vars-import.txt` contains `package=nginx`: the role was
**loaded at parsing**, its defaults are visible in the play, even though
none of its tasks ran. That is what "static" means.

#### Play 3 — `include_role` (dynamic), under a runtime condition

1. An `ansible.builtin.service_facts:` task: the real state of services,
   information that exists **only at runtime**.
2. Include (`ansible.builtin.include_role`) `stamp.yml` with
   `webserver_invocation: include`, only if the `nginx.service` service
   is `running` in `ansible_facts.services`.
3. Then a task that writes `/tmp/consommer-vars-include.txt` with the same
   templated content as play 2, mode `0644`.

State checked: `/tmp/consommer-include.txt` **exists** (the runtime
condition was true, the role was loaded and executed on the fly), BUT
`/tmp/consommer-vars-include.txt` contains `package=UNDEFINED`: an
`include_role` keeps its variables **private** (unless `public: true`).
An exact mirror of play 2: executed but invisible, versus visible but
not executed.

### 🧩 Skeleton

```yaml
---
- name: Play 1 - deploiement via roles
  hosts: ???
  become: true
  gather_facts: false
  roles:
    - role: ???
      vars:
        webserver_listen_port: ???

- name: Play 2 - import statique garde par un flag eteint
  hosts: ???
  become: true
  gather_facts: false
  vars:
    deploy_extras: false
  tasks:
    - name: Importer la trace (ne doit PAS s'executer)
      ansible.builtin.import_role:
        name: ???
        tasks_from: ???
      vars:
        webserver_invocation: ???
      when: ???

    - name: Tracer la visibilite des variables du role
      ansible.builtin.copy:
        dest: /tmp/consommer-vars-import.txt
        content: ???
        mode: "0644"

- name: Play 3 - include dynamique sous condition runtime
  hosts: ???
  become: true
  gather_facts: false
  tasks:
    - name: Etat des services (info qui n'existe qu'au runtime)
      ansible.builtin.service_facts:

    - name: Inclure la trace si nginx est actif
      ansible.builtin.include_role:
        name: ???
        tasks_from: ???
      vars:
        webserver_invocation: ???
      when: ???

    - name: Tracer la visibilite des variables du role
      ansible.builtin.copy:
        dest: /tmp/consommer-vars-include.txt
        content: ???
        mode: "0644"
```

> 💡 **Pitfalls**:
>
> - **`ANSIBLE_ROLES_PATH`**: the role lives in `labs/roles/consommer-role/roles`,
>   not next to `solution.yml`. Export
>   `ANSIBLE_ROLES_PATH=labs/roles/consommer-role/roles` before running
>   (pytest does it for you).
> - **`tasks_from: stamp.yml`**: without it, `import_role`/`include_role`
>   replay `main.yml` and reinstall nginx in each play.
> - **`when:` on an `import_role`** is copied onto **each task** of the
>   role: nothing runs, but the role is already loaded. On an
>   `include_role`, the `when:` decides whether the role is loaded **at all**.
> - **Do not define `webserver_package` anywhere** in your playbook:
>   the two `consommer-vars-*.txt` files must reveal what each
>   form actually exposes.

### 🚀 Run

```bash
ANSIBLE_ROLES_PATH=labs/roles/consommer-role/roles \
  ansible-playbook labs/roles/consommer-role/challenge/solution.yml
```

### 🧪 Validation

```bash
pytest -v labs/roles/consommer-role/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean roles-consommer-role
```

### 💡 Going further

- **Pass `deploy_extras: true`** (`-e deploy_extras=true`): the trace
  `consommer-import.txt` appears. An import's `when:` is indeed evaluated
  at runtime, task by task; it is the **loading** that is static.
- **`public: true`** on the `include_role`: re-run and observe
  `consommer-vars-include.txt` switch to `package=nginx`.
- **`ansible-lint --profile production labs/roles/consommer-role/challenge/solution.yml`**:
  expected output `Passed: 0 failure(s), 0 warning(s)`.
