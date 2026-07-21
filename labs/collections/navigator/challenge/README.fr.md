# 🎯 Challenge — Découvrir, utiliser et valider avec `ansible-navigator`

## ✅ Objectif

Écrire `challenge/solution.yml` (play ciblant `db1.lab`) qui utilise l'**Automation
content navigator** pour toute la boucle et laisse l'état suivant.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Preuve d'exploration | `/tmp/lab-navigator-doc.txt`, `0644`, owner `root`, contient `ansible.posix.sysctl` |
| État kernel | `vm.swappiness = 42`, en live **et** écrit dans `/etc/sysctl.d/70-navigator-lab.conf` |
| Preuve d'inventaire | `/tmp/lab-navigator-inventory.txt`, `0644`, owner `root`, contient `db1.lab` et le groupe `webservers` |
| Idempotence | Un second passage annonce `changed=0` |

`ansible-navigator` tourne sur le **control node** : appelez-le avec
`delegate_to: localhost` et `become: false`. Passez
`--mode stdout --execution-environment false` pour qu'il reste scriptable et ne
tire pas d'image d'EE.

## 🧩 Indices

### (a) Découvrir le module et déposer la preuve

```yaml
- name: Découvrir le module sysctl avec ansible-navigator doc
  ansible.builtin.command: >-
    ansible-navigator doc ??? --mode stdout --execution-environment false
  register: nav_doc
  changed_when: false
  delegate_to: localhost
  become: false

- name: Déposer la preuve d'exploration sur db1.lab
  ansible.builtin.copy:
    dest: /tmp/lab-navigator-doc.txt
    content: "{{ nav_doc.stdout }}\n"
    owner: root
    group: root
    mode: "0644"
```

> 💡 Le FQCN que vous passez à `doc` est celui qui doit apparaître dans le fichier
> de preuve. Trouvez-le avec `ansible-navigator collections` ou
> `ansible-navigator doc -l` si vous ne savez pas quelle collection fournit le
> module `sysctl`.

### (b) Utiliser le module découvert (état vérifiable)

```yaml
- name: Appliquer le module découvert
  ansible.posix.sysctl:
    name: vm.swappiness
    value: "42"
    sysctl_set: ???        # ← change aussi la valeur LIVE
    state: present
    reload: true
    sysctl_file: /etc/sysctl.d/70-navigator-lab.conf
```

### (c) Valider un inventaire avec le navigator

```yaml
- name: Écrire un inventaire à valider (control node)
  ansible.builtin.copy:
    dest: /tmp/lab-navigator-inventory-src.yml
    mode: "0644"
    content: |
      all:
        children:
          webservers:
            hosts:
              db1.lab:
                ansible_host: 127.0.0.1
  delegate_to: localhost
  become: false

- name: Valider l'inventaire avec ansible-navigator inventory --list
  ansible.builtin.command: >-
    ansible-navigator inventory -i /tmp/lab-navigator-inventory-src.yml --list \
      --mode stdout --execution-environment false
  register: nav_inventory
  changed_when: false
  delegate_to: localhost
  become: false

- name: Déposer la preuve d'inventaire sur db1.lab
  ansible.builtin.copy:
    dest: /tmp/lab-navigator-inventory.txt
    content: "{{ nav_inventory.stdout }}\n"
    owner: root
    group: root
    mode: "0644"
```

> 💡 **Pièges** :
>
> - Sans `--mode stdout`, `ansible-navigator` ouvre sa **TUI** et bloque tout
>   script ou test.
> - Sans `--execution-environment false`, il tente de **tirer une image d'EE** et
>   de tourner dans un conteneur : lourd et dépendant du réseau pour cet exercice.
> - Un `command:` qui invoque le navigator est en **lecture seule** : mettez
>   `changed_when: false` ou votre playbook ne sera jamais idempotent.

## 🚀 Lancement

```bash
ansible-playbook labs/collections/navigator/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/navigator/challenge/tests/
```

Le test pytest+testinfra valide :

- la preuve d'exploration existe (`0644`, root) et cite `ansible.posix.sysctl` ;
- `vm.swappiness` vaut `42` en live sur `db1.lab` et est persisté sous
  `/etc/sysctl.d/` ;
- la preuve d'inventaire résout `db1.lab` et le groupe `webservers` ;
- la solution est **idempotente** (critère RHCE).

## 🧹 Reset

```bash
dsoxlab clean collections-navigator
```
