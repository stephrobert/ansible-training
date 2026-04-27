# 🎯 Challenge — Combinaison de 3 lookups

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** pose
`/tmp/lookups-challenge.txt` contenant **3 valeurs** lues sur le **control
node** (pas sur le managed node) via 3 plugins lookup différents.

## 🧩 Préparation : créer le fichier source

Les `lookup('file', ...)` cherchent un fichier **côté control node** (relatif
au répertoire du playbook). Préparez-le :

```bash
mkdir -p labs/ecrire-code/lookups/challenge/files
echo "MAGIC-TOKEN-RHCE-2026" > labs/ecrire-code/lookups/challenge/files/api-token.txt
```

## 🧩 3 lookups à utiliser

| Lookup | Rôle | Exemple |
| --- | --- | --- |
| `file` | Lit le contenu d'un fichier local (control node) | `lookup('file', 'files/api-token.txt')` |
| `env` | Lit une variable d'environnement du control node | `lookup('env', 'HOME')` |
| `pipe` | Exécute une commande shell sur le control node, retourne stdout | `lookup('pipe', 'hostname -s')` |

> ⚠️ Tous les lookups s'exécutent **sur le control node**, **pas** sur le
> managed node — c'est ce qui fait leur intérêt (pousser un secret local sur
> les hôtes distants).

## 🧩 Sortie attendue

`/tmp/lookups-challenge.txt` (côté db1) doit contenir :

```text
token=MAGIC-TOKEN-RHCE-2026
home=/home/<vous>
host_local=<hostname court de votre poste>
```

## 🧩 Squelette

```yaml
---
- name: Challenge - 3 lookups (file, env, pipe)
  hosts: ???
  become: ???

  tasks:
    - name: Poser /tmp/lookups-challenge.txt avec 3 lookups
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          token={{ lookup('???', '???') }}
          home={{ lookup('???', '???') }}
          host_local={{ lookup('???', '???') }}
```

> 💡 **Pièges** :
>
> - **Côté control node** : les 3 lookups s'exécutent **localement**, pas
>   sur `db1.lab`. Quand vous lisez `lookup('env', 'HOME')`, vous lisez
>   la home de **votre poste**, pas celle d'`ansible@db1.lab`.
> - **`lookup('file', ...)`** : chemin relatif au **playbook** (pas au
>   CWD ni au lab). Dans votre cas, `solution.yml` est dans `challenge/`
>   donc `lookup('file', 'files/api-token.txt')` cherche
>   `challenge/files/api-token.txt`.
> - **Erreur "input file not found"** : si vous oubliez de créer
>   `files/api-token.txt`, l'erreur arrive **au moment du templating**, pas
>   en pré-check. Vérifiez bien la commande `echo` de la préparation.
> - **`lookup('pipe', '...')`** : la commande tourne via `/bin/sh -c`. Pas
>   d'expansion de variables shell — passer une commande complète et
>   simple (`hostname -s`, pas `echo $USER`).

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/lookups/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/lookups-challenge.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/lookups/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/lookups clean
```

## 💡 Pour aller plus loin

- **`lookup('vars', 'nom')`** : récupère la valeur d'une variable Ansible par
  son nom (utile en programmation dynamique).
- **`lookup('first_found', [...])`** : retourne le premier fichier trouvé dans
  une liste — pattern fréquent pour des configs OS-specific.
- **Différence `lookup` vs `query`** : `lookup` retourne **toujours une
  string** (jointe). `query` (ou `q()`) retourne une **liste**. Préférez
  `query` quand vous traitez plusieurs valeurs.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/lookups/challenge/solution.yml
   ```
