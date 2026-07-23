# 🎯 Challenge — Écrire son propre rôle et le déployer sur db1.lab

Vous avez déployé le rôle `webserver` sur `web1.lab`, mais ce rôle vous était **fourni tout fait**. Le challenge consiste à **créer vous-même un rôle** `nginx-server` sur le même modèle structurel, et à le déployer sur `db1.lab`.

L'objectif : pratiquer la **création d'un rôle from scratch**, du `ansible-galaxy role init` jusqu'à l'appel depuis un playbook. Le logiciel déployé ne change pas : c'est la structure du rôle qui est le sujet.

## ✅ Objectif

Écrire `solution.yml` qui :

1. Cible **`db1.lab`** uniquement.
2. Appelle un rôle `nginx-server` **que vous allez créer** avec :
   - `roles/nginx-server/tasks/main.yml` qui installe **nginx**, le démarre, ouvre HTTP firewalld
   - `roles/nginx-server/defaults/main.yml` avec au moins `nginx_state: present`
   - `roles/nginx-server/handlers/main.yml` avec `Restart nginx`
   - `roles/nginx-server/meta/main.yml` minimal (galaxy_info)
   - `roles/nginx-server/README.md` minimal

## 🧩 Consignes

### 1. Créer la structure du rôle

```bash
cd labs/roles/creer-premier-role/
ansible-galaxy role init challenge/roles/nginx-server
ls challenge/roles/nginx-server/      # 9 sous-dossiers générés (tasks, defaults, handlers, meta…)
```

### 2. Compléter `tasks/main.yml`

```yaml
---
- name: Installer nginx
  ansible.builtin.dnf:
    name: ???
    state: ???

- name: Démarrer + activer nginx
  ansible.builtin.systemd_service:
    name: ???
    state: ???
    enabled: ???

- name: Ouvrir HTTP dans firewalld (persistant + immédiat)
  ansible.posix.firewalld:
    service: ???                  # service standard (pas un port en dur)
    permanent: ???
    immediate: ???
    state: ???
```

### 3. Compléter `defaults/main.yml`

```yaml
---
nginx_state: ???                   # paquet 'present' par défaut
```

### 4. Compléter `handlers/main.yml`

```yaml
---
- name: Restart nginx
  ansible.builtin.systemd_service:
    name: nginx
    state: ???                     # restarted
```

### 5. Écrire `solution.yml` (squelette à compléter)

```yaml
---
- name: "Challenge : déployer nginx via un rôle"
  hosts: ???
  become: ???
  roles:
    - role: ???                    # nom du dossier sous challenge/roles/
```

### 6. Lancer depuis la racine du repo

```bash
ANSIBLE_ROLES_PATH=labs/roles/creer-premier-role/challenge/roles \
ansible-playbook \
    -i labs/roles/creer-premier-role/inventory/hosts.yml \
    labs/roles/creer-premier-role/challenge/solution.yml
```

> 💡 **Pièges** :
>
> - **`ANSIBLE_ROLES_PATH`** est une **variable d'environnement** Ansible,
>   pas un `-e` Ansible (qui set des extra-vars de play, pas des configs).
>   Ne pas confondre.
> - **Idempotence** du rôle : `state: started` (et non `restarted`) dans
>   `tasks/`. Le `restarted` ne va que dans le `handlers/` (déclenché
>   conditionnellement par un `notify`).
> - **`firewalld`** : `service: http` plutôt que `port: 80/tcp`. C'est
>   plus lisible et plus portable (le service est défini dans
>   `/usr/lib/firewalld/services/`).
> - **`ansible-galaxy role init`** crée 9 sous-dossiers — vous n'avez pas
>   besoin de tous les remplir. `defaults/`, `tasks/`, `handlers/`, `meta/`
>   suffisent ici.

### 7. Tester

   ```bash
   curl http://db1.lab/
   ```

   Sortie attendue : la page d'accueil par défaut de nginx.

## 🧪 Validation

Le test pytest vérifie automatiquement :

- Le paquet `nginx` est installé sur `db1.lab`.
- Le service `nginx` est `running` et `enabled`.
- Le port 80 est ouvert dans firewalld.
- Une requête HTTP `http://db1.lab/` retourne **200**.

```bash
pytest -v challenge/tests/
```

## 🚀 Pour aller plus loin

- Refactorer le rôle pour qu'il accepte un paramètre `nginx_listen_port` et template `nginx.conf` en conséquence. Attention : un port non standard demande une étiquette SELinux. C'est le sujet du **lab 59** (variables).
- Comparer les sorties `ansible-playbook` avec `--check --diff` avant le run réel.
- Étendre le rôle pour installer aussi `php-fpm` en dépendance — sujet du **lab 71** (dependencies).

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
dsoxlab clean roles-creer-premier-role
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
