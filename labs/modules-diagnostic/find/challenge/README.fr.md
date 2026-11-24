# Nettoyer les logs obèses sans supprimer les utiles

## La situation

Une application de **db1.lab** déverse ses logs dans `/tmp` depuis des semaines,
et certains ont assez grossi pour menacer la partition. La règle retenue par
l'équipe est simple : au-delà d'une certaine taille, le log part ; en dessous, il
reste, parce que les petits sont justement ceux que l'on lit pour déboguer.
Personne ne veut d'un `rm` récité de mémoire à 2 h du matin sur une machine de
production. Vous pilotez le nettoyage depuis **control-node.lab**, et c'est
Ansible qui décide de ce qui part.

Votre mission :

1. Mettre en place le répertoire de travail et ses fichiers de log sur
   **db1.lab** : le terrain sur lequel ce nettoyage s'exécutera.
2. **Rechercher** dans ce répertoire les fichiers `.log` de **plus de 5 Mo**, en
   laissant le module de recherche faire le filtrage plutôt qu'une ligne de
   shell.
3. **Supprimer les seuls fichiers trouvés**, en itérant sur le résultat de la
   recherche : ce qui n'est pas dans la liste n'est pas touché.
4. Prouver le résultat : les petits logs survivent, les gros ont disparu.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-find/

## 🎯 Challenge — `find:` + cleanup automatique

### ✅ Objectif

Sur **db1.lab**, créer 5 fichiers `.log` de tailles diverses, puis utiliser
`find:` pour identifier ceux **> 5Mo** et les supprimer en boucle.

### 🧩 Étapes

1. Créer un dossier `/tmp/lab-find-cleanup/` (mode 0755).
2. Y créer **5 fichiers** `.log` :
   - `small1.log` (1Mo)
   - `small2.log` (3Mo)
   - `big1.log` (10Mo)
   - `big2.log` (15Mo)
   - `big3.log` (20Mo)
3. **`find:`** les `.log` de **plus de 5Mo** dans ce dossier.
4. **`file: state: absent`** en `loop:` sur le résultat.

À la fin, **seuls** `small1.log` et `small2.log` doivent rester.

### 🧩 Squelette

```yaml
---
- name: Challenge - find + cleanup
  hosts: db1.lab
  become: true

  tasks:
    - name: Creer le dossier de test
      ansible.builtin.file:
        path: ???
        state: directory
        mode: "0755"

    - name: Creer 5 fichiers .log
      ansible.builtin.shell: |
        cd /tmp/lab-find-cleanup
        dd if=/dev/zero of=small1.log bs=1M count=1 2>/dev/null
        dd if=/dev/zero of=small2.log bs=1M count=3 2>/dev/null
        dd if=/dev/zero of=big1.log bs=1M count=10 2>/dev/null
        dd if=/dev/zero of=big2.log bs=1M count=15 2>/dev/null
        dd if=/dev/zero of=big3.log bs=1M count=20 2>/dev/null
      args:
        creates: /tmp/lab-find-cleanup/small1.log

    - name: Trouver les .log > 5Mo
      ansible.builtin.find:
        paths: ???
        patterns: ???
        size: ???
      register: big_logs

    - name: Supprimer ces fichiers
      ansible.builtin.file:
        path: ???
        state: ???
      loop: ???
      loop_control:
        label: ???
```

> 💡 **Pièges** :
>
> - **`age: -7d`** (négatif) : fichiers **plus récents** que 7 jours.
>   `age: 7d` (positif) : fichiers **plus anciens**. Inversion classique.
> - **`recurse: true`** : descend dans les sous-dossiers. Sans, seul le
>   `paths:` direct est scanné.
> - **`size:` accepte unités** : `1m` (mega), `1g` (giga). Sans unité =
>   octets.
> - **`<var>.files`** = liste de dicts. Itérer avec `loop:` + `path:
>   "{{ item.path }}"` pour les supprimer.
> - **`patterns:`** : liste de globs (`*.log`, `*.tmp`). Pour regex :
>   `use_regex: true` + patterns regex.

### 🚀 Lancement

```bash
ansible-playbook labs/modules-diagnostic/find/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /tmp/lab-find-cleanup/"
```

### 🧪 Validation automatisée

```bash
pytest -v labs/modules-diagnostic/find/challenge/tests/
```

### 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/tmp/lab-find-cleanup state=absent"
```

### 💡 Pour aller plus loin

- **`age: 7d`** : ajouter un filtre temporel (logs > 5Mo **ET** > 7 jours).
- **`recurse: true`** : descendre dans les sous-dossiers.
- **`hidden: true`** : inclure les `.dotfiles`.
- **Pattern shell** : `find /tmp -name '*.log' -size +5M -delete` est plus
  rapide que `find:` + `loop:` sur des **dizaines de milliers** de fichiers
  — mais perd l'idempotence Ansible.
- **Lint** :

   ```bash
   ansible-lint labs/modules-diagnostic/find/challenge/solution.yml
   ```
