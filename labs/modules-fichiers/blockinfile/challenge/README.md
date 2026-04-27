# 🎯 Challenge — Bloc d'aliases shell avec `blockinfile`

## ✅ Objectif

Sur **db1.lab**, créer le fichier **`/etc/profile.d/aliases-rhce.sh`** et y
ajouter un **bloc d'aliases délimité par des markers**, idempotent.

## 🧩 Sortie attendue

Le fichier doit ressembler à :

```bash
# BEGIN ALIASES RHCE
alias ll='ls -lah'
alias gs='git status'
alias ports='ss -tulpn'
# END ALIASES RHCE
```

Si on relance le playbook, **le bloc reste unique** (pas de duplication).
C'est le grand atout de `blockinfile` vs `lineinfile` : il gère un **bloc
complet** au lieu d'une ligne.

## 🧩 Module à utiliser : `ansible.builtin.blockinfile`

Options clés :

| Option | Effet |
| --- | --- |
| `path:` | Fichier à modifier. |
| `create: true` | Crée le fichier s'il n'existe pas (défaut : false). |
| `block:` | Le contenu du bloc (multi-lignes via `\|`). |
| `marker:` | Format du marker. **Doit contenir `{mark}`** qui sera remplacé par `BEGIN` ou `END`. |
| `mode:` | Permissions du fichier. |

## 🧩 Squelette

```yaml
---
- name: Challenge - blockinfile (aliases shell)
  hosts: db1.lab
  become: true

  tasks:
    - name: Bloc d'aliases dans /etc/profile.d/aliases-rhce.sh
      ansible.builtin.blockinfile:
        path: ???
        create: ???
        mode: "0644"
        marker: "# {mark} ALIASES RHCE"
        block: |
          ???
          ???
          ???
```

> 💡 **Pièges** :
>
> - **`marker:`** définit les balises de début/fin du bloc. Par défaut
>   `# {mark} ANSIBLE MANAGED BLOCK` où `{mark}` = `BEGIN`/`END`. Si
>   vous appelez 2 fois `blockinfile` sur le même fichier sans changer
>   `marker:`, le 2ᵉ remplace le 1ᵉʳ.
> - **`marker:` custom** : `marker: "# {mark} aliases-rhce"` pour gérer
>   plusieurs blocs distincts dans le même fichier.
> - **`create: true`** : crée le fichier s'il n'existe pas. Sans, échec
>   si fichier absent.
> - **`block:`** accepte une chaîne multi-lignes (`|`) ou une liste de
>   strings. Le contenu est inséré tel quel entre les marqueurs.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-fichiers/blockinfile/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/profile.d/aliases-rhce.sh"
```

🔍 **Test idempotence** :

```bash
ansible-playbook labs/modules-fichiers/blockinfile/challenge/solution.yml
# Au 2e run : changed=0 (le bloc est déjà conforme)
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-fichiers/blockinfile/challenge/tests/
```

Le test vérifie en particulier que le marker `# BEGIN ALIASES RHCE` apparaît
**exactement une fois** dans le fichier (preuve d'idempotence).

## 🧹 Reset

```bash
make -C labs/modules-fichiers/blockinfile clean
```

## 💡 Pour aller plus loin

- **Plusieurs blocs dans un même fichier** : utilisez **des markers
  différents** pour ne pas qu'ils s'écrasent (`# {mark} BLOC_A`,
  `# {mark} BLOC_B`).
- **`insertafter:` / `insertbefore:`** : place le bloc relativement à un motif
  existant. Ex: `insertafter: '^# Custom config'`.
- **Suppression du bloc** : `state: absent` enlève le bloc proprement
  (markers compris).
- **Lint** :

   ```bash
   ansible-lint labs/modules-fichiers/blockinfile/challenge/solution.yml
   ```
