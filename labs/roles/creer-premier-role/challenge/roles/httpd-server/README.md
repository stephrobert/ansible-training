# Rôle `httpd-server`

Variante du rôle `webserver` qui installe **Apache httpd** au lieu de nginx.

## Variables

| Variable | Défaut | Description |
|---|---|---|
| `httpd_state` | `present` | État du paquet httpd |

## Exemple

```yaml
- hosts: dbservers
  become: true
  roles:
    - role: httpd-server
```
