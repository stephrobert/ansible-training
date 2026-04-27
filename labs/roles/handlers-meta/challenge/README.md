# 🎯 Challenge — Handlers et meta du rôle webserver

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** utilise le rôle
`webserver` avec un **port custom** pour démontrer que :

1. Les **3 handlers** (`Restart nginx`, `Reload nginx`, `Notify deployment`)
   sont bien déclenchés au déploiement.
2. Le `meta/main.yml` du rôle est correctement lu (vérifiable via
   `ansible-galaxy role list`).

## 🧩 Indices

Le rôle accepte des variables (override des `defaults/`) :

| Variable | Défaut | À surcharger ? |
| --- | --- | --- |
| `webserver_listen_port` | `80` | ✅ → **`8080`** (le test attend ce port) |
| `webserver_index_content` | `<h1>Hello…</h1>` | ✅ → message custom incluant `inventory_hostname` |

Le challenge vérifie via les tests :

- `nginx` est `running` et écoute sur **port 8080**
- `/var/log/webserver-deploy.log` existe et contient `db1.lab`
- `/var/log/deploy-notification.log` existe et contient `Deployment completed`,
  `db1.lab`, et **`8080`** (preuve que le handler a bien lu la variable
  surchargée)

## 🧩 Squelette

```yaml
---
- name: Challenge - handlers déclenchés sur db1
  hosts: ???
  become: ???

  roles:
    - role: webserver
      vars:
        webserver_listen_port: ???           # 8080
        webserver_index_content: "{{ ??? }}"  # message custom avec inventory_hostname
```

> 💡 **Pièges** :
>
> - **Override au niveau rôle** : `vars:` sous `- role: webserver` cible
>   uniquement ce rôle (priorité 13). Pour overrider partout, utiliser
>   `vars:` au niveau play.
> - **3 handlers attendus** : `Restart nginx`, `Reload nginx`, `Notify
>   deployment`. Le `meta/main.yml` ne peut pas définir de handler — ça
>   reste dans `roles/<role>/handlers/main.yml`.
> - **Lecture des variables côté handler** : `webserver_listen_port` doit
>   être lisible dans le handler (qui tourne en fin de play). Si vous
>   utilisez `{{ webserver_listen_port }}` dans le handler, il **lit la
>   valeur courante** (post-override) — c'est ce qu'on veut.
> - **Idempotence** : le handler `Notify deployment` écrit dans le journal
>   à chaque run où le template change. Au 2ème run identique, `changed=0`
>   et le handler ne tourne pas.

## 🚀 Lancement

```bash
ansible-playbook labs/roles/handlers-meta/challenge/solution.yml
```

🔍 **Sortie attendue** : 3 bandeaux `RUNNING HANDLER` (pour Restart, Reload,
Notify deployment) au 1er run.

```bash
# Vérifications
ssh ansible@db1.lab 'sudo ss -tlnp | grep 8080'
ssh ansible@db1.lab 'sudo cat /var/log/deploy-notification.log'
```

## 🧪 Validation automatisée

```bash
pytest -v labs/roles/handlers-meta/challenge/tests/
```

Le test vérifie sur db1 :

- `nginx` running.
- `/var/log/webserver-deploy.log` contient `db1.lab`.
- `/var/log/deploy-notification.log` contient `Deployment completed` + `db1.lab` + `8080`.
- `nginx` écoute sur `:8080`.

## 🧹 Reset

```bash
make -C labs/roles/handlers-meta clean
```

## 💡 Pour aller plus loin

- **`ansible-galaxy role list`** : valide que le `meta/main.yml` est lisible.
  Si vous obtenez une erreur de parsing, c'est un problème de YAML.
- **Inspection du rôle** :

  ```bash
  ansible-doc -t role labs/roles/handlers-meta/roles/webserver
  # Affiche les variables documentées + plateformes supportées
  ```

- **Lint** :

  ```bash
  ansible-lint --profile production labs/roles/handlers-meta/
  ```

  Le profil `production` vérifie en particulier que `meta/main.yml` contient
  bien `galaxy_info`, `platforms`, et `min_ansible_version`.
