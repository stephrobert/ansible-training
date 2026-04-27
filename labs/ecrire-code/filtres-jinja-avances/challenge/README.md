# 🎯 Challenge — 4 filtres Jinja2 avancés

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** pose
`/tmp/filtres-avances.txt` contenant **4 lignes**, chacune produite par un
filtre Jinja2 avancé.

## 🧩 Données d'entrée

```yaml
fqdn: "web1.lab.example.com"
secret: "admin:secret"
nested: [[1, 2], [3, [4, 5]]]
to_hash: "foobar"
```

## 🧩 Sortie attendue

```text
prefix=web
b64=YWRtaW46c2VjcmV0
flat=[1, 2, 3, 4, 5]
sha256=c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2
```

## 🧩 4 filtres à utiliser

| Filtre | Effet |
| --- | --- |
| `regex_search('motif')` | Retourne la 1ère sous-chaîne qui matche le motif |
| `b64encode` | Encode en Base64 (utile pour des `Authorization: Basic`) |
| `flatten` | Aplatit récursivement une liste de listes |
| `hash('sha256')` | Empreinte SHA256 hexadécimale d'une string |

## 🧩 Squelette

```yaml
---
- name: Challenge - 4 filtres avancés
  hosts: db1.lab
  become: true

  vars:
    fqdn: "web1.lab.example.com"
    secret: "admin:secret"
    nested: [[1, 2], [3, [4, 5]]]
    to_hash: "foobar"

  tasks:
    - name: Poser /tmp/filtres-avances.txt
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          prefix={{ fqdn | regex_search(???) }}
          b64={{ secret | ??? }}
          flat={{ nested | ??? }}
          sha256={{ to_hash | ???(???) }}
```

> 💡 **Indice regex** : pour extraire **uniquement** le préfixe `web` de
> `web1.lab.example.com`, utilisez le motif `^([a-z]+)` (ancré au début, ne
> capture que des lettres minuscules).

**Pièges** :

> - **`regex_search` retourne `None`** si pas de match — `default(...)`
>   pour fallback. `regex_findall` retourne une liste (vide si pas de
>   match).
> - **`b64encode`** : la sortie reste **string** (pas bytes). Pour décoder,
>   `b64decode`. Important : ce **n'est pas du chiffrement** (juste
>   encodage).
> - **`flatten`** : aplatit une liste de listes. Niveau de profondeur
>   par défaut = 1. Pour aplatir totalement, `flatten(levels=99)`.
> - **`hash`** filter : SHA1 par défaut. Pour SHA256 :
>   `to_hash | hash('sha256')`. Pour MD5 :  `'md5'`. Ne **jamais**
>   utiliser `hash` sur un secret : c'est un hash, pas une auth.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/filtres-jinja-avances/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/filtres-avances.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/filtres-jinja-avances/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/filtres-jinja-avances clean
```

## 💡 Pour aller plus loin

- **`hash('md5')` / `hash('sha1')` / `hash('sha512')`** : autres algos. Sur
  les versions récentes d'Ansible, `password_hash('sha512')` génère un hash de
  password style `/etc/shadow`.
- **`b64decode`** : décode du Base64 (typiquement pour lire un secret venant
  d'un Vault/Kubernetes Secret).
- **`from_yaml` / `from_json`** : parser une string YAML/JSON en dict.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/filtres-jinja-avances/challenge/solution.yml
   ```
