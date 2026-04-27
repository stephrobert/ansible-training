# 🎯 Challenge — Template MOTD avec `if` + `for`

## ✅ Objectif

Générer **`/etc/motd-challenge`** sur **db1.lab** depuis un template Jinja2,
avec un bloc conditionnel et une boucle.

## 🧩 Fichiers à créer

### 1) `challenge/templates/motd.j2`

Le template doit utiliser :

- **`{{ inventory_hostname }}`** pour interpoler le nom de l'hôte
- **`{% if host_role == "DB" %}` … `{% endif %}`** pour afficher conditionnellement
  une ligne `Profil : DB`
- **`{% for s in services %}` … `{% endfor %}`** pour itérer sur la liste des
  services
- **Whitespace control** : utilisez `{%- ... -%}` ou `{%- ... %}` pour éviter
  les lignes vides parasites

Squelette :

```jinja
==========================================
  Bienvenue sur {{ ??? }}
==========================================
{% if ??? %}
Profil : DB
{% endif %}
Services :
{% for ??? in ??? %}
  - {{ ??? }}
{% endfor %}
```

### 2) `challenge/solution.yml`

Squelette :

```yaml
---
- name: Challenge - Jinja2 base
  hosts: db1.lab
  become: true

  vars:
    host_role: DB
    services:
      - postgresql
      - chronyd
      - firewalld

  tasks:
    - name: Générer /etc/motd-challenge depuis le template
      ansible.builtin.template:
        src: ???
        dest: ???
        mode: "0644"
```

## 🧩 Sortie attendue

```text
==========================================
  Bienvenue sur db1.lab
==========================================
Profil : DB
Services :
  - postgresql
  - chronyd
  - firewalld
```

> 💡 **Pièges** :
>
> - **`{{ ... }}` vs `{% ... %}`** : `{{ }}` évalue et affiche, `{% %}`
>   contrôle (if, for, set). Confusion classique : utiliser `{{ if }}`
>   au lieu de `{% if %}`.
> - **`{% for ... %}` ajoute des newlines** : utiliser `{%- for -%}`
>   (avec tirets) pour supprimer les sauts de ligne autour. Attention au
>   formatage du fichier produit.
> - **`| default(...)`** : indispensable pour rendre un template
>   réutilisable. Sans, une variable absente fait planter le templating.
> - **Chemin du template** : relatif à `<role>/templates/` pour un rôle,
>   ou `templates/` à côté du playbook sinon. **Pas** `template:
>   src: /chemin/absolu`.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/jinja2-base/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/motd-challenge"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/jinja2-base/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/jinja2-base clean
```

## 💡 Pour aller plus loin

- **`trim_blocks` et `lstrip_blocks`** : options du template qui contrôlent les
  espaces autour des balises `{%- %}`. Activez-les sur le module pour un rendu
  plus prévisible :

  ```yaml
  ansible.builtin.template:
    trim_blocks: true
    lstrip_blocks: true
  ```

- **Variables conditionnelles** : `{{ var | default('default_value') }}` dans
  le template, pour éviter `is undefined` partout.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/jinja2-base/challenge/solution.yml
   ```
