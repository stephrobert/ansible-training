# Une bannière de connexion qui ment sur la machine

## La situation

Chaque hôte vous accueille avec une bannière tapée à la main il y a des
années. La moitié annonce encore un service décommissionné depuis deux
réorganisations, l'une vous souhaite la bienvenue sur un hostname qui n'existe
plus, et toutes sont truffées de lignes vides parasites laissées par une
précédente tentative de génération. L'exploitation veut une seule bannière :
générée, juste sur chaque hôte, et lisible.

Vous commencez par **db1.lab**, depuis **control-node.lab**.

Votre mission :

1. Générer `/etc/motd-challenge` depuis un **template Jinja2**, l'hôte se
   nommant lui-même depuis l'inventaire plutôt que par une chaîne en dur.
2. N'afficher la ligne de rôle **que si** l'hôte porte réellement ce rôle : une
   condition dans le template, pas deux templates côte à côte.
3. Lister les services de l'hôte avec une **boucle** pilotée par une variable,
   un par ligne.
4. Supprimer les lignes vides parasites avec le **whitespace control** : c'est
   toute la différence entre une bannière générée et une bannière qui a l'air
   générée.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/jinja2-base/

## 🎯 Challenge — Template MOTD avec `if` + `for`

### ✅ Objectif

Générer **`/etc/motd-challenge`** sur **db1.lab** depuis un template Jinja2,
avec un bloc conditionnel et une boucle.

### 🧩 Fichiers à créer

#### 1) `challenge/templates/motd.j2`

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

#### 2) `challenge/solution.yml`

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

### 🧩 Sortie attendue

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

### 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/jinja2-base/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/motd-challenge"
```

### 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/jinja2-base/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-jinja2-base
```

### 💡 Pour aller plus loin

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
