# 🎯 Challenge — `systemd_service` + unit file custom

## ✅ Objectif

Sur **web1.lab**, gérer le service standard **`chronyd`** ET créer un
**unit file custom** `lab-marker.service` (oneshot) qui touche un fichier
flag au démarrage.

> 💡 **Pourquoi `chronyd` et pas `httpd`/`nginx` ?** Les ports 80/443 sont
> déjà occupés sur `web1.lab` par un lab précédent. `chronyd` (NTP, port 123
> UDP) ne crée pas de conflit.

## 🧩 4 étapes

1. **Installer** `chrony` via `dnf`.
2. **Démarrer + activer** `chronyd` au boot via `systemd_service:`.
3. **Créer** le fichier `/etc/systemd/system/lab-marker.service` via
   `copy: content:` avec un unit file inline.
4. **Recharger systemd** (`daemon_reload: true`) ET activer/démarrer
   `lab-marker`.

## 🧩 Contenu attendu de `lab-marker.service`

```ini
[Unit]
Description=Lab Marker Service
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/touch /var/run/lab-marker.flag
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

> 💡 **`Type=oneshot` + `RemainAfterExit=yes`** : le service exécute son
> `ExecStart` une fois puis reste marqué `active` (sinon il serait `inactive`
> dès la fin du `touch`). Pattern classique pour des services « init » non
> daemon.

## 🧩 Squelette

```yaml
---
- name: Challenge - systemd_service avec unit file custom
  hosts: web1.lab
  become: true

  tasks:
    - name: Installer chrony
      ansible.builtin.dnf:
        name: ???
        state: present

    - name: Démarrer et activer chronyd
      ansible.builtin.systemd_service:
        name: ???
        state: ???
        enabled: ???

    - name: Créer le unit file lab-marker.service
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          [Unit]
          Description=Lab Marker Service
          After=network.target

          [Service]
          Type=oneshot
          ExecStart=/bin/touch /var/run/lab-marker.flag
          RemainAfterExit=yes

          [Install]
          WantedBy=multi-user.target

    - name: Recharger systemd, activer et démarrer lab-marker
      ansible.builtin.systemd_service:
        name: ???
        daemon_reload: ???
        enabled: ???
        state: ???
```

> 💡 **Pièges** :
>
> - **`daemon_reload: true`** est obligatoire **après avoir modifié** une
>   unit file. Sinon systemd ignore les changements (cache).
> - **`state:`** = `started`, `stopped`, `restarted`, `reloaded`. Utiliser
>   `restarted` dans **handlers**, pas dans tasks (sinon non-idempotent
>   par défaut).
> - **`enabled: true`** = au boot. Pas équivalent à `started: true`
>   (running maintenant). Pour les deux ensemble : `state: started` +
>   `enabled: true`.
> - **Pas de `.service` dans `name:`** : juste `httpd`, pas
>   `httpd.service`. Sauf pour disambiguer (timer, socket).

## 🚀 Lancement

```bash
ansible-playbook labs/modules-services/systemd/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "systemctl is-active chronyd lab-marker"
ansible web1.lab -m ansible.builtin.command -a "ls -la /var/run/lab-marker.flag"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-services/systemd/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/modules-services/systemd clean
```

## 💡 Pour aller plus loin

- **`state: restarted`** vs **`state: reloaded`** : `restarted` est
  destructif (downtime), `reloaded` envoie `SIGHUP` (sans downtime, mais
  uniquement si le service le supporte).
- **`scope: user`** : gérer un service systemd **utilisateur**
  (`~/.config/systemd/user/`) au lieu d'un service système.
- **`masked: true`** : empêche le démarrage manuel ou automatique d'un
  service (renvoie vers `/dev/null`).
- **Lint** :

   ```bash
   ansible-lint labs/modules-services/systemd/challenge/solution.yml
   ```
