# 🎯 Challenge — Module `template:` avec `backup`

## ✅ Objectif

Générer **`/etc/banner.txt`** sur **db1.lab** depuis un template, avec
**backup** activé et **mode 0644**.

## 🧩 Fichiers à créer

### 1) `challenge/templates/banner.txt.j2`

Doit produire :

```text
====================
Bienvenue !
====================
Generated: 2026-04-25
Owner: ops-team
```

Indices Jinja2 :

- `{{ motd_text }}` interpole une variable.
- `{% for k, v in metadata.items() %}` itère sur un dict (couples clé-valeur).
- `{{ k | capitalize }}` met la première lettre en majuscule (`generated` →
  `Generated`).

Squelette :

```jinja
====================
{{ ??? }}
====================
{% for ???, ??? in metadata.items() %}
{{ ??? | capitalize }}: {{ ??? }}
{% endfor %}
```

### 2) `challenge/solution.yml`

Squelette :

```yaml
---
- name: Challenge - module template avec backup
  hosts: db1.lab
  become: true

  vars:
    motd_text: "Bienvenue !"
    metadata:
      generated: "2026-04-25"
      owner: "ops-team"

  tasks:
    - name: Générer /etc/banner.txt depuis le template
      ansible.builtin.template:
        src: ???
        dest: ???
        mode: "0644"
        backup: ???
```

## 🧩 Options à connaître sur `template:`

| Option | Effet |
| --- | --- |
| `src:` | Chemin **relatif au playbook** ou absolu. Convention : `templates/<nom>.j2`. |
| `dest:` | Chemin **sur le managed node**. |
| `mode: "0644"` | Permissions Unix (en chaîne, pas en octal nu). |
| `backup: true` | Sauvegarde la version précédente en `<dest>.<timestamp>~` avant écrasement. |
| `validate: 'cmd %s'` | Valide la syntaxe avant écriture (ex: `nginx -t -c %s`). |
| `trim_blocks: true` | Supprime le `\n` après `{% %}`. |
| `lstrip_blocks: true` | Supprime les espaces de début de ligne avant `{% %}`. |

> 💡 **Pièges** :
>
> - **`backup: true`** crée un backup `<dest>.<timestamp>~` avant
>   écraser. Indispensable pour les configs critiques. Au 1er run, pas de
>   backup (rien à sauvegarder).
> - **`validate:`** : commande pour valider le fichier **avant** de
>   l'écrire. Si elle échoue, le fichier d'origine reste intact. Format :
>   `validate: 'sshd -t -f %s'` (le `%s` est remplacé par un fichier
>   temporaire).
> - **`trim_blocks` + `lstrip_blocks`** : indispensables pour des
>   templates lisibles. Sans, vos `{% if %}` laissent des lignes vides
>   et des espaces parasites.
> - **`mode:` toujours quoté** : `mode: "0644"` (pas `mode: 0644` qui est
>   octal puis décimal = mode 420).

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/module-template/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/banner.txt"
ansible db1.lab -m ansible.builtin.command -a "ls -la /etc/banner.txt*"
```

🔍 Au **2e run après modif** du template, vous verrez `/etc/banner.txt.<ts>~`
apparaître (preuve de `backup: true`).

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/module-template/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/module-template clean
```

## 💡 Pour aller plus loin

- **`validate:`** : ajoutez `validate: 'echo %s'` pour voir Ansible passer le
  fichier temporaire à la commande de validation. Sur un nginx.conf, ce serait
  `nginx -t -c %s`. Si la validation échoue, le fichier d'origine reste
  intact.
- **`force: false`** : empêche l'écrasement si le fichier existe déjà
  (l'opposé du défaut).
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/module-template/challenge/solution.yml
   ```
