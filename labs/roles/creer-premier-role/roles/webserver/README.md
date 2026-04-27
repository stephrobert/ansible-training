# Rôle `stephrobert.webserver`

Installe et configure **nginx** sur RHEL 9/10 et AlmaLinux 9/10.

C'est le **rôle fil rouge** de la formation Ansible RHCE 2026. Il s'enrichit progressivement au fil des labs 58 → 64.

## Variables

| Variable | Défaut | Description |
|---|---|---|
| `webserver_state` | `present` | État du paquet (`present` ou `absent`) |
| `webserver_service_state` | `started` | État du service |
| `webserver_service_enabled` | `true` | Démarrage auto au boot |

## Exemple d'utilisation

```yaml
- hosts: webservers
  become: true
  roles:
    - role: webserver
```

## Tests

```bash
pytest -v challenge/tests/
```

## Licence

MIT
