# 🎯 Challenge — Migrer des boucles `with_*` vers `loop:`

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** utilise **uniquement la
forme moderne `loop:`** (jamais `with_items:` ni `with_dict:`) pour deux
itérations différentes :

| Itération | Source | Sortie attendue |
| --- | --- | --- |
| Liste simple | `[apple, banana, cherry]` | 3 fichiers `/tmp/withitems-<fruit>.txt` |
| Dict (clé→valeur) | `{nginx: 80, redis: 6379}` | `/tmp/withdict-nginx.txt` (contenu `80`), `/tmp/withdict-redis.txt` (contenu `6379`) |

## 🧩 Indices

### Boucle sur liste simple

```yaml
loop:
  - element1
  - element2
```

L'item courant est accessible via `{{ item }}`.

### Boucle sur dict

Un dict ne s'itère pas directement. Il faut le **convertir en liste de paires**
avec le filtre **`dict2items`** :

```yaml
loop: "{{ mon_dict | dict2items }}"
```

Chaque item devient un dict `{ key: ..., value: ... }`. Vous accédez aux deux
champs via `{{ item.key }}` et `{{ item.value }}`.

## 🧩 Squelette

```yaml
---
- name: "Challenge - migration with_* vers loop:"
  hosts: db1.lab
  become: true

  vars:
    ports:
      nginx: 80
      redis: 6379

  tasks:
    - name: Itération sur liste simple (loop:)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      loop:
        - apple
        - banana
        - cherry

    - name: Itération sur dict via dict2items
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      loop: ???
      loop_control:
        label: "{{ item.key }}"
```

> ⚠️ **Quote le `name:`** quand il contient `loop:` à la fin (sinon YAML le
> lit comme un mapping clé-valeur). D'où les guillemets dans le squelette.

**Pièges supplémentaires** :

> - **`with_items`** est **déprécié** depuis Ansible 2.5 mais fonctionne
>   encore. À l'EX294, utilisez **`loop:`** (lab 21).
> - **`with_dict`** convertit un dict en liste de dicts `{key, value}`.
>   Migration vers `loop:` : `dict | dict2items` puis `item.key` /
>   `item.value`.
> - **`with_subelements`** : pour itérer sur une sous-liste de chaque dict.
>   Migration vers `loop:` : `subelements()` filter.
> - **Pas de double-loop** : `loop:` n'accepte qu'une dimension. Pour 2
>   dimensions, utiliser `subelements` ou `product` filter.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml
```

🔍 Vérifiez :

```bash
ansible db1.lab -m ansible.builtin.command -a "ls /tmp/withitems-*.txt /tmp/withdict-*.txt"
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/withdict-nginx.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/boucles-with-deprecated/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/boucles-with-deprecated clean
```

## 💡 Pour aller plus loin

- **`with_items` → `loop`** (1-to-1) ; **`with_dict` → `loop: dict | dict2items`** ;
  **`with_subelements` → `subelements` filter**. La doc Ansible liste toutes
  les conversions [ici](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_loops.html#migrating-from-with-x-to-loop).
- **`loop_control: index_var: i`** : exposer l'index courant.
- **Lint** : `ansible-lint` signale `with_items` comme `deprecation`.

   ```bash
   ansible-lint labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml
   ```
