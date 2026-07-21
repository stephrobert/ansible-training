# 🎯 Challenge — Le rôle webserver déclare ses prérequis, db1 le prouve

## ✅ Objectif

Le rôle `webserver` livré dans `roles/` a deux prérequis structurels que ses
appelants oublient sans cesse : SELinux dans le bon mode, et un pare-feu
démarré avec les bons ports. Votre travail se joue à deux endroits :

1. **`roles/webserver/meta/main.yml`** : déclarer les `dependencies:` pour
   que `selinux_setup` puis `firewall_setup` s'exécutent **avant** le rôle,
   avec leurs variables.
2. **`challenge/solution.yml`** : un play qui consomme **uniquement** le rôle
   `webserver` (via `roles:`) sur db1.lab, avec `webserver_listen_port: 8081`.
   Personne n'appelle les dépendances : c'est le rôle qui les impose.

Les tests ne lisent pas `meta/main.yml` : ils vérifient **l'état de db1.lab**.
Chaque rôle du lab consigne son passage dans `/tmp/deps-order.txt` : ce
fichier est la preuve de l'ordre d'exécution réel.

## 🧩 Contrat attendu (état de db1.lab)

| Preuve | État attendu |
| --- | --- |
| Ordre d'exécution | `/tmp/deps-order.txt` contient exactement `selinux_setup`, `firewall_setup`, `webserver`, dans cet ordre |
| Dépendance 1 exécutée | `getenforce` répond `Enforcing` (var `selinux_setup_state: enforcing` passée par la dépendance) |
| Dépendance 2 exécutée | `firewalld` démarré **et** activé, port **443/tcp** ouvert (var `firewall_setup_open_ports` passée par la dépendance) |
| Rôle parent exécuté | nginx installé, démarré, activé, à l'écoute sur **8081**, port 8081/tcp ouvert, page d'accueil en place |

## 🧩 Squelettes

`roles/webserver/meta/main.yml` (partie à compléter) :

```yaml
dependencies:
  - role: ???
    vars:
      selinux_setup_state: ???
  - role: ???
    vars:
      firewall_setup_open_ports:
        - ???
```

`challenge/solution.yml` :

```yaml
---
- name: Déployer webserver (les prérequis suivent tout seuls)
  hosts: ???
  become: ???
  gather_facts: false
  roles:
    - role: ???
      vars:
        webserver_listen_port: ???
```

> 💡 **Pièges** :
>
> - **`ANSIBLE_ROLES_PATH=labs/roles/dependencies/roles`** au lancement :
>   les rôles ne sont pas à côté de `solution.yml` (pytest le fait pour vous).
> - **L'ordre des dépendances est celui de la déclaration** : déclarez
>   `selinux_setup` avant `firewall_setup`, sinon `/tmp/deps-order.txt`
>   racontera une autre histoire et le test le verra.
> - **Le play ne doit PAS lister les dépendances** dans `roles:` : si vous
>   les appelez à la main, vous avez recréé le problème du scénario (chaque
>   appelant doit y penser). Tout le sens de `dependencies:` est que le rôle
>   les impose lui-même.
> - **`443/tcp`** au format firewalld, avec les quotes.

## 🚀 Lancement

```bash
ANSIBLE_ROLES_PATH=labs/roles/dependencies/roles \
  ansible-playbook labs/roles/dependencies/challenge/solution.yml
```

🔍 Dans la sortie, les tâches préfixées `selinux_setup :` et
`firewall_setup :` apparaissent **avant** celles du rôle `webserver`, alors
que le play ne les mentionne nulle part.

## 🧪 Validation

```bash
pytest -v labs/roles/dependencies/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean roles-dependencies
```

## 💡 Pour aller plus loin

- **Le diamant** : ajoutez un rôle `common` dont dépendent `selinux_setup`
  ET `firewall_setup`. Relancez : `common` n'apparaît qu'une fois dans
  `/tmp/deps-order.txt` (déduplication), sauf si les deux le référencent
  avec des `vars:` différentes.
- **`allow_duplicates: true`** dans le `meta/main.yml` du rôle dépendance :
  il tourne alors à chaque référence.
- **`ansible-lint --profile production labs/roles/dependencies/challenge/solution.yml`** :
  sortie attendue `Passed: 0 failure(s), 0 warning(s)`.
