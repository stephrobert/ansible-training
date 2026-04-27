# 🎯 Challenge — 6 filtres Jinja2 dans un fichier marqueur

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** pose
`/tmp/filtres-result.txt` contenant **6 lignes**, chacune démontrant un filtre
Jinja2 essentiel.

## 🧩 Données d'entrée

Mettez ces variables dans `vars:` du play :

```yaml
raw_input: "  HELLO World  "
pkgs_a: ["nginx", "redis", "postgres"]
pkgs_b: ["redis", "memcached"]
services:
  - { name: api, port: 8080, env: prod }
  - { name: web, port: 80, env: staging }
  - { name: cache, port: 6379, env: prod }
base_config:
  app: api
  port: 80
tls_overrides:
  port: 443
  tls: true
```

## 🧩 Sortie attendue

```text
trimmed=hello world
union=memcached,nginx,postgres,redis
prod_services=api,cache
merged=app=api port=443 tls=True
default_value=fallback-OK
yaml_safe=hello: world
```

## 🧩 6 filtres à utiliser

| Ligne | Filtres | Effet |
| --- | --- | --- |
| `trimmed` | `trim`, `lower` | Espaces enlevés + minuscules |
| `union` | `+`, `unique`, `sort`, `join(',')` | Concaténation de listes, dédup, tri, join |
| `prod_services` | `selectattr('env', 'equalto', 'prod')`, `map(attribute='name')`, `sort`, `join(',')` | Filtre + extraction + tri + join |
| `merged` | `combine(...)` puis sérialisation `key=value` triée | Fusion de dicts |
| `default_value` | `default('fallback-OK')` | Valeur par défaut sur variable inexistante |
| `yaml_safe` | `to_yaml`, `trim` | Rendu YAML inline |

## 🧩 Squelette

```yaml
---
- name: Challenge - 6 filtres Jinja2
  hosts: db1.lab
  become: true

  vars:
    # ... copier les 5 variables ci-dessus ...

  tasks:
    - name: Poser /tmp/filtres-result.txt
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          trimmed={{ raw_input | ??? | ??? }}
          union={{ ??? }}
          prod_services={{ ??? }}
          merged={{ ??? }}
          default_value={{ ??? }}
          yaml_safe={{ {'hello': 'world'} | ??? | trim }}
```

> 💡 **Indice pour `merged`** : `(base_config | combine(tls_overrides)).items()`
> renvoie une liste de tuples `(clé, valeur)`. Vous pouvez ensuite
> `map('join', '=')` pour transformer chaque tuple en `clé=valeur`, puis
> `sort | join(' ')` pour ordonner et concaténer.

**Pièges** :

> - **`combine`** est récursif (deep merge) seulement avec
>   `recursive=true`. Sinon il fait un merge plat (le dict de droite
>   écrase complètement le dict de gauche).
> - **`map('attribute=...')`** vs **`map('extract', dict)`** : le premier
>   extrait un attribut de chaque élément, le second extrait par clé.
>   Confusion classique.
> - **`| default([])`** sur une liste : indispensable avant `length` ou
>   itération si la variable peut être absente.
> - **`to_yaml` / `to_json` / `to_nice_yaml`** : sortie YAML/JSON. La
>   version `nice` ajoute indentation et sauts de ligne (pour produire un
>   fichier lisible).

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/filtres-jinja-essentiels/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/filtres-result.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/filtres-jinja-essentiels/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/filtres-jinja-essentiels clean
```

## 💡 Pour aller plus loin

- **`difference` / `intersect` / `symmetric_difference`** : opérations
  ensemblistes sur des listes (au-delà de `union`).
- **`regex_replace`** : substituer un motif. Exemple : `{{ "v1.2.3" |
  regex_replace('^v', '') }}` → `1.2.3`.
- **`to_nice_json` / `to_nice_yaml`** : sérialisation indentée pour des
  fichiers plus lisibles.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/filtres-jinja-essentiels/challenge/solution.yml
   ```
