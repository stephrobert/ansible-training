# Context — Stop copy-pasting the same web server playbook

Your team ships web servers by copy-pasting the same twenty tasks into every new
playbook. Last week a firewall rule was fixed in one copy and forgotten in the
four others, and a host went live with HTTP closed. The lead has had enough:
anything reusable now ships as a **role**. A `webserver` role (nginx) already
exists as a model and was handed to you ready-made, and a new internal app
needs a web server on **db1.lab**. This time you write the role yourself.

Your mission, from **control-node.lab**:

1. Scaffold an **`nginx-server` role** with the standard layout: `tasks/`,
   `defaults/`, `handlers/`, `meta/` and a `README.md`.
2. Have it install **nginx**, start and enable it, and open HTTP in firewalld
   **persistently**, without sacrificing idempotence.
3. Expose an overridable default in `defaults/main.yml` and wire a
   **`Restart nginx`** handler triggered by `notify:`.
4. Call the role from a playbook targeting **db1.lab** only.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/creer-premier-role/
