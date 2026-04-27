# 🎯 Challenge — Démontrer la précédence avec un playbook

Vous avez vu que `ansible-inventory --host` résout correctement les variables. Le challenge consiste à **prouver dynamiquement** la résolution sur les 3 hôtes via un playbook qui pose un fichier marqueur contenant la valeur de `app_port` résolue pour cet hôte.

## ✅ Objectif

Écrire `solution.yml` qui :

1. Cible **tous les hôtes** (`hosts: all`)
2. Pose un fichier marqueur `/tmp/lab55-port-{{ inventory_hostname }}.txt` qui contient la valeur de `app_port` résolue pour l'hôte courant
3. Utilise le module `ansible.builtin.copy:` (avec `content:`)

L'inventaire à utiliser : **celui du lab parent** (`../inventory/hosts.yml`), pas celui du challenge.

## 🧩 Consignes

Squelette à compléter :

```yaml
---
- name: Challenge — démontrer la précédence des variables
  hosts: ???                            # tous les hôtes de l'inventaire
  become: ???
  gather_facts: false
  tasks:
    - name: Poser un marqueur par hôte avec la valeur de app_port résolue
      ansible.builtin.copy:
        dest: ???                       # /tmp/lab55-port-<inventory_hostname>.txt
        content: "port resolu pour {{ ??? }} : {{ ??? }}\n"
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **Précédence des variables** (de la plus faible à la plus forte) :
>   `group_vars/all` < `group_vars/<groupe>` < `host_vars/<hôte>`. Donc
>   sur web1, le `host_vars/web1.lab.yml` gagne sur `group_vars/webservers.yml`.
> - **Inventaire du challenge** : utilisez `-i inventory/hosts.yml` du lab
>   (pas l'inventaire racine du repo). Sinon les `group_vars` ne sont pas
>   chargées.
> - **`inventory_hostname`** : c'est le nom **dans l'inventaire**
>   (`web1.lab`), pas le hostname système. À privilégier dans les playbooks.
> - **`become: false`** suffit : `/tmp` est inscriptible par tous, et
>   l'utilisateur `ansible` peut écrire ses propres fichiers.

Lancez la solution depuis le **dossier du lab** :

```bash
cd labs/inventaires/group-vars-host-vars/
ansible-playbook -i inventory/hosts.yml challenge/solution.yml
```

Vérifier les fichiers sur chaque hôte :

   ```bash
   ssh ansible@web1.lab cat /tmp/lab55-port-web1.lab.txt
   ssh ansible@web2.lab cat /tmp/lab55-port-web2.lab.txt
   ssh ansible@db1.lab  cat /tmp/lab55-port-db1.lab.txt
   ```

   Sorties attendues :

   ```text
   port resolu pour web1.lab : 9090
   port resolu pour web2.lab : 8080
   port resolu pour db1.lab : 80
   ```

## 🧪 Validation

Le script `tests/test_precedence.py` vérifie automatiquement :

- Le fichier `/tmp/lab55-port-web1.lab.txt` existe sur `web1.lab` et contient `9090` (host_vars gagne).
- Le fichier `/tmp/lab55-port-web2.lab.txt` existe sur `web2.lab` et contient `8080` (group_vars/webservers gagne).
- Le fichier `/tmp/lab55-port-db1.lab.txt` existe sur `db1.lab` et contient `80` (group_vars/all gagne par défaut).

```bash
pytest -v challenge/tests/
```

## 🚀 Pour aller plus loin

- Ajoutez `app_port: 5555` dans `--extra-vars` à la ligne de commande et observez : la valeur **écrase** tout (priorité 22 sur 22).
- Ajoutez un dossier `group_vars/webservers/main.yml` au lieu d'un fichier `webservers.yml` : Ansible accepte les deux formats. Préférer le **dossier** si vous splittez en plusieurs fichiers (`main.yml`, `vault.yml`, `network.yml`).
- Créez un nouveau host `db2.lab` dans `dbservers` sans aucune variable spécifique : il hérite de `app_port: 80`.

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
make -C labs/inventaires/group-vars-host-vars/ clean
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
