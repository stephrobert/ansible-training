# 🎯 Challenge — Synthèse des facts via `hostvars`

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** pose un fichier
`/tmp/facts-summary.txt` contenant 5 informations agrégées **depuis 2 hôtes
différents** : facts locaux de db1 + IP de web1 lue via `hostvars`.

Contenu attendu :

```text
db1_hostname=db1.lab
db1_os=AlmaLinux
db1_memory=<entier>
webservers_count=2
web1_ip=10.10.20.21
```

## 🧩 Pièce-clé : `hostvars`

`hostvars` est un dictionnaire **global** qui contient les variables (et facts)
de **tous** les hôtes que Ansible a déjà *gathered* dans le run courant.

> ⚠️ **Pour lire `hostvars['web1.lab'].ansible_default_ipv4.address`**, il faut
> que web1 ait été **gathered au préalable**. Sinon, `hostvars['web1.lab']`
> ne contient que les vars statiques de l'inventaire — pas les facts.

## 🧩 Pattern à utiliser : 2 plays

Le solution.yml contient **deux plays consécutifs** :

```yaml
---
# Play 1 : pre-gather sur web1 (rend ses facts visibles dans hostvars)
- name: Pre-gather web1
  hosts: web1.lab
  gather_facts: true
  tasks: []

# Play 2 : synthèse sur db1
- name: Synthèse sur db1
  hosts: db1.lab
  become: true
  gather_facts: true
  tasks:
    - name: Poser /tmp/facts-summary.txt
      ansible.builtin.copy:
        dest: /tmp/facts-summary.txt
        mode: "0644"
        content: |
          db1_hostname={{ ??? }}
          db1_os={{ ??? }}
          db1_memory={{ ??? }}
          webservers_count={{ ??? }}
          web1_ip={{ ??? }}
```

## 🧩 Variables magiques à utiliser

| Champ | Variable Ansible |
| --- | --- |
| `db1_hostname` | `inventory_hostname` (variable magique, le nom court depuis l'inventaire) |
| `db1_os` | `ansible_distribution` (fact, ex: `AlmaLinux`) |
| `db1_memory` | `ansible_memtotal_mb` (fact, entier) |
| `webservers_count` | `groups['webservers'] \| length` (variable magique : liste des hôtes du groupe) |
| `web1_ip` | `hostvars['web1.lab'].ansible_default_ipv4.address` |

> 💡 **Pièges** :
>
> - **`gather_facts: true`** obligatoire pour utiliser `ansible_*`. S'il
>   est `false`, les facts sont absents et le templating crash sur
>   `'ansible_distribution' is undefined`.
> - **`hostvars[...]`** : pour accéder aux facts d'un autre hôte, l'autre
>   hôte doit déjà avoir gather_facts. Si pas dans le play actuel,
>   utiliser `delegate_to: <hôte>` + `delegate_facts: true` au préalable.
> - **`groups[]`** retourne une **liste**, pas un dict. `length` filtre
>   pour compter, `[0]` pour prendre le premier.
> - **`ansible_default_ipv4.address`** vs `ansible_all_ipv4_addresses` :
>   le premier est l'IP de la route par défaut, le second la liste
>   complète. Choisir selon le contexte.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/facts-summary.txt"
```

🔍 Vérifiez que les 5 lignes sont présentes avec les bonnes valeurs.

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/facts-magic-vars/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/facts-magic-vars clean
```

## 💡 Pour aller plus loin

- **Cache des facts** : si vous avez configuré un fact cache (`fact_caching:
  jsonfile` dans `ansible.cfg` — c'est le cas dans ce repo), le pre-gather de
  web1 n'est plus nécessaire au 2ème run, les facts sont **lus depuis le
  cache**. Démontrez-le en supprimant le 1er play et en relançant.
- **`magic_variables`** : `ansible_play_hosts`, `play_hosts`, `groups['all']`,
  `inventory_hostname_short`. Inspectez-les avec `debug: var=...`.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/facts-magic-vars/challenge/solution.yml
   ```
