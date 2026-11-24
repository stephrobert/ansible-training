# La staging qui fuit dans la config de production

## La situation

Le catalogue de services tient dans une seule liste : nom, port, tier. Quatre
entrées aujourd'hui, quarante au prochain trimestre. Le fichier qui alimente
la supervision de production est maintenu à la main depuis cette liste, et la
dernière mise à jour y a discrètement glissé un port de staging. Personne ne
l'a vu jusqu'à ce que la supervision réveille quelqu'un à 3 heures du matin
pour une base de dev. Le catalogue va bien : c'est la recopie manuelle qui
échoue. Depuis **control-node.lab**, vous générez la vue production depuis le
catalogue lui-même.

Votre mission :

1. Déclarer le catalogue sur `db1.lab` sous forme de **liste de dicts**, chaque
   entrée portant son nom, son port et son tier.
2. Générer `/tmp/services-production.txt` ne contenant **que** le tier
   `production`, un `<nom>:<port>` par ligne.
3. Filtrer **dans la donnée**, pas à la main : les entrées staging et dev ne
   doivent jamais atteindre le fichier, quel que soit l'ordre du catalogue.
4. Vérifier que le résultat tient en exactement les deux lignes attendues, et
   rien d'autre, en accédant aux champs imbriqués pour composer chaque ligne.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/types-collections/

## 🎯 Challenge — Filtrer une liste de dicts avec `selectattr`

### ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Déclare dans `vars:` une **liste de dicts** `services` (4 services).
2. Pose `/tmp/services-production.txt` qui contient **uniquement** les services
   du tier `production`, au format `<name>:<port>` (un par ligne).

### 🧩 Données d'entrée

À copier dans le `vars:` du play :

```yaml
services:
  - { name: api, port: 8080, tier: production }
  - { name: web, port: 80, tier: staging }
  - { name: cache, port: 6379, tier: production }
  - { name: dev-db, port: 5432, tier: dev }
```

### 🧩 Sortie attendue

Le fichier `/tmp/services-production.txt` doit contenir **exactement** :

```text
api:8080
cache:6379
```

Les services `web` (staging) et `dev-db` (dev) sont **exclus**.

### 🧩 Outils Jinja2 à connaître

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

### 🧩 Squelette

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

### 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/types-collections/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/services-production.txt"
```

### 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/types-collections/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-types-collections
```

### 💡 Pour aller plus loin

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
