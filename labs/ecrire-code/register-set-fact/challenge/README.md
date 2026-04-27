# 🎯 Challenge — `register` puis `set_fact` pour calculer un identifiant

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Récupère 2 informations système via `ansible.builtin.command` + `register`.
2. Combine ces 2 informations dans un **fact runtime** via `set_fact`.
3. Pose le résultat dans `/tmp/system-id.txt` (format `system_id=<hostname>:<kernel>`).

## 🧩 Pattern register → set_fact

C'est un schéma très courant en production : on **lit** plusieurs valeurs avec
`command:`, on les **assemble** avec `set_fact:`, puis on les **utilise** dans
les tâches suivantes (template, copy, debug…).

### Squelette

```yaml
---
- name: Challenge - register puis set_fact
  hosts: db1.lab
  become: true
  gather_facts: false   # on prouve qu'on peut tout faire sans gather

  tasks:
    - name: Récupérer le hostname court
      ansible.builtin.command: ???      # commande shell qui retourne le hostname court
      register: ???
      changed_when: false               # cmd lecture-seule, donc never changed

    - name: Récupérer la version du noyau
      ansible.builtin.command: ???      # commande shell qui retourne la version du kernel
      register: ???
      changed_when: false

    - name: Construire system_id
      ansible.builtin.set_fact:
        system_id: "{{ ???.stdout }}:{{ ???.stdout }}"

    - name: Poser /tmp/system-id.txt
      ansible.builtin.copy:
        dest: /tmp/system-id.txt
        content: "system_id={{ system_id }}\n"
        mode: "0644"
```

### Indices commandes

- Hostname court : la commande `hostname -s` (Linux) retourne `db1` (sans le
  domaine `.lab`).
- Version noyau : la commande `uname -r` retourne quelque chose comme
  `5.14.0-503.40.1.el10_1.x86_64`.

### Indices Ansible

- **`register: var_name`** capture le résultat d'une tâche dans une variable.
  Le résultat contient `stdout`, `rc`, `start`, `end`, etc.
- **`changed_when: false`** : indispensable sur des `command:` lecture-seule,
  sinon Ansible marque la tâche comme `changed` à chaque run (`command:` n'est
  pas idempotent par défaut).
- **`set_fact:`** crée une variable de niveau **18** dans la précédence
  (au-dessus de `vars:` du play, sous `--extra-vars`).

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/register-set-fact/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/system-id.txt"
# Doit afficher : system_id=db1:5.14.0-...el10_x.x86_64
```

> 💡 **Pièges** :
>
> - **`register:`** capture `stdout`, `rc`, `failed`, `changed`, etc.
>   Pour le contenu utile : `<var>.stdout` (string brute), `.stdout_lines`
>   (liste).
> - **`set_fact:`** crée une variable persistante au niveau du play (pas
>   du tout cas). Utile pour transformer un `register:` en variable
>   propre.
> - **`changed_when: false`** sur `command:` / `shell:` lecture-seule —
>   sinon ils sont marqués `changed=1` à chaque run, brisant
>   l'idempotence. Pour un `hostname`, `uname`, etc.
> - **`set_fact` est niveau 18**, plus haut que `vars:` du play (14)
>   mais sous `--extra-vars` (22). Donc un `--extra-vars` peut écraser
>   un `set_fact`.

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/register-set-fact/challenge/tests/
```

Le test vérifie sur db1 :

- `/tmp/system-id.txt` existe.
- Contient `system_id=db1:` (preuve hostname capturé).
- Contient `.el10` ou `.x86_64` (preuve kernel capturé).

## 🧹 Reset

```bash
make -C labs/ecrire-code/register-set-fact clean
```

## 💡 Pour aller plus loin

- **Utiliser `ansible_facts`** au lieu de `command:` : `ansible_facts.hostname`
  et `ansible_facts.kernel` sont déjà collectés par `gather_facts`. Comparez
  les deux approches en termes de simplicité.
- **Multi-host** : sur un play qui cible plusieurs hôtes, `set_fact` est
  **par-hôte**. Démontrez-le en ciblant `webservers` et en posant un fichier
  par hôte (`/tmp/system-id-{{ inventory_hostname }}.txt`).
- **`cacheable: yes`** sur `set_fact` : la valeur est mise en cache (utile si
  fact_caching est activé).
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/register-set-fact/challenge/solution.yml
   ```
