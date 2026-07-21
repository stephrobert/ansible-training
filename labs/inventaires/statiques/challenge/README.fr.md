# 🎯 Challenge — Écrire un inventaire statique de zéro

Aucun inventaire ne vous est fourni. Vous partez d'une page blanche et vous
écrivez `inventory/hosts.yml` à la main, comme à la tâche 1 de l'examen.

## ✅ Objectif

Créer le fichier `inventory/hosts.yml` (à la racine du lab) déclarant :

1. Un groupe **`webservers`** contenant **web1.lab** et **web2.lab**.
2. Un groupe **`dbservers`** contenant **db1.lab**.
3. Un groupe parent **`datacenter`** qui agrège `webservers` et `dbservers` via
   **`children`** (aucun hôte en propre).
4. Une variable de groupe **`web_role: frontend`** portée par `webservers`.
5. Une variable de groupe **`db_role: database`** portée par `dbservers`.
6. Une variable **`site: paris`** portée par le **parent** `datacenter`, donc
   héritée par les trois hôtes.

**Aucune adresse IP** dans le fichier : la connexion passe par le `ssh_config`
de dsoxlab, le compte de connexion est `ansible` (le compte de service que
dsoxlab provisionne sur les VMs).

## 🧩 Consignes

Le **bloc de connexion** (spécifique à dsoxlab) vous est donné : recopiez-le tel
quel sous `all.vars`, puis complétez `children` avec vos groupes.

```yaml
---
all:
  vars:
    ansible_user: ansible
    ansible_ssh_common_args: >-
      -F {{ lookup('env', 'HOME') }}/.cache/dsoxlab/ansible-training/ssh_config
      -o StrictHostKeyChecking=no
      -o UserKnownHostsFile=/dev/null
    ansible_ssh_private_key_file: "{{ inventory_dir }}/../../../../ssh/id_ed25519"
    ansible_python_interpreter: /usr/bin/python3
  children:
    webservers:
      hosts:
        ???
        ???
      vars:
        ???
    dbservers:
      hosts:
        ???
      vars:
        ???
    datacenter:
      children:
        ???
        ???
      vars:
        ???
```

> 💡 **Pièges** :
>
> - **Un hôte, pas une liste** : `web1.lab:` (deux-points), pas `- web1.lab`.
> - **Un groupe parent n'a pas de `hosts:`** : il n'a que `children:`. Si vous
>   remettez les hôtes directement dans `datacenter`, ce n'est plus un parent,
>   c'est un troisième groupe plat.
> - **La variable du parent doit descendre** : `site` se déclare une seule fois,
>   sur `datacenter`, et web1/web2/db1 en héritent. La recopier sur chaque hôte
>   « marche » à l'affichage mais rate l'objectif.
> - **Le bloc de connexion est obligatoire** : sans lui, `ansible -m ping`
>   n'atteint aucune VM et les tests échouent sur la connexion, pas sur vos
>   groupes.

## 🔎 Vérifiez vous-même avant de lancer les tests

```bash
cd labs/inventaires/statiques/

ansible-inventory -i inventory/hosts.yml --graph
# Attendu : @datacenter contient @webservers (web1, web2) et @dbservers (db1).

ansible webservers -i inventory/hosts.yml -m ansible.builtin.ping   # 2 pong
ansible datacenter -i inventory/hosts.yml -m ansible.builtin.ping   # 3 pong

ansible-inventory -i inventory/hosts.yml --host db1.lab
# Attendu : db_role=database ET site=paris, mais PAS de web_role.
```

## 🧪 Validation

```bash
pytest -v challenge/tests/
```

Les tests interrogent l'inventaire **résolu par Ansible** (`ansible-inventory
--list` / `--host`) et joignent les hôtes par **ping** : ils prouvent l'état,
pas le texte du fichier.

## 🚀 Pour aller plus loin

- Réécrivez le même inventaire au **format INI** (`inventory/hosts.ini`) et
  vérifiez que `ansible-inventory --graph` rend le même graphe.
- Sortez `web_role` en ligne vers un fichier `group_vars/webservers.yml` à côté
  de l'inventaire : Ansible le résout de la même façon.
- Ajoutez un second parent `production` qui agrège `datacenter`, et observez
  l'héritage en cascade de `site` avec `ansible-inventory --host web1.lab`.

## 🧹 Reset

Le livrable de ce lab est un fichier local (`inventory/`, gitignoré) : il n'y a
rien à nettoyer sur les VMs. Pour repartir de zéro, supprimez simplement votre
inventaire :

```bash
rm -rf labs/inventaires/statiques/inventory/
```
