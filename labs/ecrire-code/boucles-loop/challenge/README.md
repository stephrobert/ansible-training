# 🎯 Challenge — Create 3 users, 2 of them active (`loop` + `when` + `loop_control`)

## ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**:

1. Iterates over a list of 3 users.
2. Creates **only** those that have `enabled: true` (filter via `when:` on
   the item).
3. Lays down a summary file `/tmp/loop-result.txt` listing the active
   users (comma-separated, alphabetical order).

## 🧩 Input data

```yaml
challenge_users:
  - { name: chal_alice, shell: /bin/bash, enabled: true }
  - { name: chal_bob, shell: /bin/zsh, enabled: false }
  - { name: chal_charlie, shell: /bin/bash, enabled: true }
```

Expected result:

- Users `chal_alice` and `chal_charlie` created.
- User `chal_bob` **not** created.
- `/tmp/loop-result.txt` contains `chal_alice,chal_charlie`.

## 🧩 Model of a conditional loop

```yaml
- name: Faire qqch sur certains items seulement
  ansible.builtin.<module>:
    param: "{{ item.???  }}"
  loop: "{{ ma_liste }}"
  loop_control:
    label: "{{ item.??? }}"   # affichage console plus lisible
  when: item.???              # filtre sur l'item courant
```

## 🧩 Skeleton

```yaml
---
- name: Challenge - loop + when + loop_control
  hosts: db1.lab
  become: true

  vars:
    challenge_users:
      # ... 3 users (cf. ci-dessus) ...

  tasks:
    # Optionnel mais conseillé : nettoyer chal_bob s'il a été créé par erreur
    - name: S'assurer que chal_bob n'existe pas
      ansible.builtin.user:
        name: chal_bob
        state: absent
        remove: true

    - name: Créer les users actifs uniquement
      ansible.builtin.user:
        name: ???
        shell: ???
        state: present
      loop: ???
      loop_control:
        label: ???
      when: ???

    - name: Récapitulatif des users créés
      ansible.builtin.copy:
        dest: /tmp/loop-result.txt
        mode: "0644"
        content: "{{ challenge_users | selectattr(???) | map(attribute='???') | sort | join(',') }}\n"
```

> 💡 **`selectattr(...)` without a 2nd argument**: by default, `selectattr('attr')`
> keeps the elements where `attr` is **truthy** (equivalent to `if item.attr`).

**Traps**:

> - **`loop:`** is modern (Ansible 2.5+). Avoid `with_items`
>   (deprecated). See lab 22 for the migration.
> - **`item`** is the default variable in a loop. To rename it:
>   `loop_control: { loop_var: user_data }`.
> - **`label:`** in `loop_control`: controls what is shown in the
>   Ansible output (`label: "{{ item.name }}"` instead of showing the whole
>   dict).
> - **`selectattr` returns a generator**. Chain `| list` if you
>   want `length` or to index (`[0]`).

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/boucles-loop/challenge/solution.yml
```

🔍 Check:

```bash
ansible db1.lab -m ansible.builtin.command -a "id chal_alice chal_charlie"
ansible db1.lab -m ansible.builtin.command -a "id chal_bob" || echo "chal_bob absent (OK)"
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/loop-result.txt"
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/boucles-loop/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-boucles-loop
```

Removes the 3 users + the marker file.

## 💡 Going further

- **`with_items` (deprecated)**: old syntax equivalent to `loop:`.
  Avoid it in new code: `ansible-lint` flags it.
- **`loop_control: pause: 2`**: adds a delay between each iteration
  (useful to avoid overloading a third-party API).
- **`loop_control: extended: true`**: exposes `ansible_loop.index`,
  `ansible_loop.first`, `ansible_loop.last` (counter, first, last).
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/boucles-loop/challenge/solution.yml
   ```
