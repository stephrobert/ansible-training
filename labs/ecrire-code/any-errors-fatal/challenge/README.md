# Half the fleet updated is worse than none

## The situation

Tuesday's config push reached **web1.lab**, failed on **web2.lab**, and
stopped there. That is the default behaviour, and it sounds reasonable until
you look at the result: two webservers behind the same load balancer, running
two different configurations, giving two different answers to the same request.
Support spent a day chasing a bug that only appeared every other refresh. For
this kind of change, half-applied is worse than not applied at all.

You set the policy at the **play level**, from **control-node.lab**.

Your mission:

1. Write a two-step deployment on both webservers: stage the release, run a
   health check, then activate the release. Each step leaves a per-host
   marker file so nothing can be claimed without evidence.
2. Make the health check fail on the host named by a `fail_host` variable
   (`none` by default), so an incident can be simulated on demand with
   `-e fail_host=web1.lab`.
3. Enable the play keyword that **stops the entire play** the moment any host
   fails: when web1 fails its health check, web2 must NOT activate its
   release, even though web2 itself never failed. That absence is what the
   validation checks.
4. Then place it precisely: compare it with the default behaviour, and with
   `max_fail_percentage`, which tolerates a threshold rather than demanding
   perfection. And work out what it does once combined with `serial`.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/any-errors-fatal/ (in French)

## 🎯 Challenge — Atomic deployment: prove `any_errors_fatal`

### ✅ Objective

Write `challenge/solution.yml`: a **two-step** deployment on the
2 webservers, with a **health check** between them that can fail
on a given host. The rule of the game: if the check fails on **a single**
host, **no** host must activate the release. This is exactly what
`any_errors_fatal: true` guarantees, and it is what the tests **prove**
by actually causing the failure.

### 🧩 Expected contract

The playbook targets `webservers`, with `become: true`, and declares a variable
`fail_host` valued `"none"` by default (overridden by the tests via
`-e fail_host=web1.lab` to simulate the incident).

| Step | Task | State produced |
| --- | --- | --- |
| 1 | Prepare the release | `/tmp/anyfatal-step1-{{ inventory_hostname }}.txt`, contains `step1 OK on <host>`, mode `0644` |
| 2 | Health check | `ansible.builtin.command: /bin/false` executed **only** when `inventory_hostname == fail_host` |
| 3 | Activate the release | `/tmp/anyfatal-release-{{ inventory_hostname }}.txt`, contains `release OK on <host>`, mode `0644` |

Behaviors that the tests check on the VMs:

1. **Incident run** (`-e fail_host=web1.lab`): the playbook exits in error,
   step 1 is laid down on both hosts, and the release file exists
   **neither on web1** (it failed) **nor on web2** (the play stopped
   everywhere). Without `any_errors_fatal: true`, web2 would have continued and laid down its
   release: the test fails.
2. **Nominal run** (without `-e`): the playbook succeeds and both hosts have
   step 1 **and** the release.
3. **Idempotence**: a second nominal run shows `changed=0` everywhere.

### 🧩 Skeleton

```yaml
---
- name: Déploiement atomique sur les webservers
  hosts: ???
  become: ???
  gather_facts: false
  ???: true                          # le mot-clé du lab, au niveau du play
  vars:
    fail_host: ???                   # aucun hôte ne doit matcher par défaut

  tasks:
    - name: Préparer la release (étape 1)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"

    - name: Contrôle de santé (échoue sur fail_host)
      ansible.builtin.command: /bin/false
      when: ???
      changed_when: false

    - name: Activer la release (étape 3)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
```

> 💡 **Traps**:
>
> - **Play-level keyword, not task-level**: `any_errors_fatal: true` goes
>   at the root of the play, at the same level as `hosts:` and `become:`.
> - **`{{ inventory_hostname }}` in `dest:`**: one file per host, otherwise
>   the 2 webservers overwrite each other.
> - **`when: inventory_hostname == fail_host`**: the check must only crash
>   on the designated host. With `fail_host=none`, nobody matches and the
>   play converges.
> - **`changed_when: false`** on the `command`: without it, `ansible-lint`
>   (the `no-changed-when` rule) refuses the playbook, and idempotence is wrong.

### 🚀 Launch

```bash
# Run incident : web1 échoue, PERSONNE ne doit poser la release
ansible-playbook labs/ecrire-code/any-errors-fatal/challenge/solution.yml \
    -e fail_host=web1.lab
ansible webservers -b -m ansible.builtin.command -a "ls /tmp/"  # pas de anyfatal-release-*

# Run nominal : tout le monde converge
ansible webservers -b -m ansible.builtin.shell -a "rm -f /tmp/anyfatal-*.txt"
ansible-playbook labs/ecrire-code/any-errors-fatal/challenge/solution.yml
```

🔍 On the incident run, the `PLAY RECAP` shows `failed=1` on web1 and
`failed=0` on web2: web2 crashed on nothing, so it is not marked failed. The
signature of `any_errors_fatal` lies elsewhere: web2 **stops anyway**, its
remaining tasks never run, and its `ok` counter stays below what a nominal
run would give. This is the
signature of `any_errors_fatal`.

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/any-errors-fatal/challenge/tests/
```

The tests replay the two runs themselves (incident then nominal) and
check the state of both VMs, positive **and** negative assertions.

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-any-errors-fatal
```

### 💡 Going further

- **Remove `any_errors_fatal: true`** and rerun the incident run: web2
  lays down its release even though web1 crashed. This is the "half the fleet"
  drift of the scenario, and it is why the tests forbid it.
- **`serial: 1` + `any_errors_fatal: true`**: on 10 hosts, a failure in
  batch 2 prevents batches 3 to 10 from starting.
- **`max_fail_percentage`**: percentage tolerance, where
  `any_errors_fatal` is zero tolerance (`max_fail_percentage: 0` is
  equivalent).
- **Lint**:

   ```bash
   ansible-lint --profile production labs/ecrire-code/any-errors-fatal/challenge/solution.yml
   ```
