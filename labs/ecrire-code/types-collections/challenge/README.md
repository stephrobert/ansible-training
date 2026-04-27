# 🎯 Challenge — Filtrer une liste de dicts avec `selectattr`

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Déclare dans `vars:` une **liste de dicts** `services` (4 services).
2. Pose `/tmp/services-production.txt` qui contient **uniquement** les services
   du tier `production`, au format `<name>:<port>` (un par ligne).

## 🧩 Données d'entrée

À copier dans le `vars:` du play :

```yaml
services:
  - { name: api, port: 8080, tier: production }
  - { name: web, port: 80, tier: staging }
  - { name: cache, port: 6379, tier: production }
  - { name: dev-db, port: 5432, tier: dev }
```

## 🧩 Sortie attendue

Le fichier `/tmp/services-production.txt` doit contenir **exactement** :

```text
api:8080
cache:6379
```

Les services `web` (staging) et `dev-db` (dev) sont **exclus**.

## 🧩 Outils Jinja2 à connaître

Trois filtres à combiner pour traiter une liste de dicts :

| Filtre | Effet |
| --- | --- |
| `selectattr('attr', 'equalto', 'value')` | Garde les éléments dont `attr == value` |
| `map(attribute='name')` | Extrait le champ `name` de chaque élément |
| `join(',')` | Concatène une liste en chaîne |

> 💡 Ici on cherche à **filtrer** sur `tier == "production"`, puis à itérer
> dans un template `content:` pour produire `<name>:<port>` ligne par ligne.
> Vous pouvez le faire avec une **boucle Jinja2** (`{% for ... %}`) directement
> dans la chaîne `content:`.

## 🧩 Squelette

```yaml
---
- name: Challenge - filtrer services production
  hosts: ???
  become: ???

  vars:
    services:
      # ... copier la liste ci-dessus ...

  tasks:
    - name: Poser /tmp/services-production.txt (production seulement)
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          {% for s in services | ??? %}
          {{ s.??? }}:{{ s.??? }}
          {% endfor %}
```

> 💡 **Pièges** :
>
> - **Boucle Jinja2 dans `content:`** : utilisez `{% for ... %}` (avec `%`,
>   pas `{{ }}` qui sert à l'évaluation simple).
> - **`selectattr` retourne un generator**, pas une liste — bien chaîner
>   avec `| list` si vous voulez `length` ou indexer.
> - **Indentation YAML** : le `content: |` (block scalar) préserve la
>   structure brute. Les `{% for %}` peuvent rester en début de ligne, ce
>   qui est lisible mais introduit un saut de ligne entre items. C'est OK
>   pour ce challenge.
> - **Test exact** : la sortie doit contenir `api:8080` ET `cache:6379`,
>   et **PAS** `web:80` ni `dev-db:5432`. Vérifiez bien la syntaxe
>   `selectattr('tier', 'equalto', 'production')`.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/types-collections/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/services-production.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/types-collections/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/types-collections clean
```

## 💡 Pour aller plus loin

- **Sans `selectattr`** : reproduire le filtre avec un `for` + `if`
  (`{% for s in services if s.tier == "production" %}`). C'est plus verbeux
  mais utile quand on a plusieurs conditions complexes.
- **Tri** : ajoutez un `| sort(attribute='port')` après `selectattr` pour trier
  par numéro de port croissant.
- **Lookup `dict2items`** : pour itérer sur un dict de dicts plutôt que sur
  une liste de dicts.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/types-collections/challenge/solution.yml
   ```
