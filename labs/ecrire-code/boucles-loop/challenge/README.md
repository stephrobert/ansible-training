# 🎯 Challenge — Créer 3 users dont 2 actifs (`loop` + `when` + `loop_control`)

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Itère sur une liste de 3 users.
2. Crée **uniquement** ceux qui ont `enabled: true` (filtre via `when:` sur
   l'item).
3. Pose un fichier récapitulatif `/tmp/loop-result.txt` listant les users
   actifs (séparés par virgule, ordre alphabétique).

## 🧩 Données d'entrée

```yaml
challenge_users:
  - { name: chal_alice, shell: /bin/bash, enabled: true }
  - { name: chal_bob, shell: /bin/zsh, enabled: false }
  - { name: chal_charlie, shell: /bin/bash, enabled: true }
```

Résultat attendu :

- Users `chal_alice` et `chal_charlie` créés.
- User `chal_bob` **non** créé.
- `/tmp/loop-result.txt` contient `chal_alice,chal_charlie`.

## 🧩 Modèle d'une boucle conditionnelle

```yaml
- name: Faire qqch sur certains items seulement
  ansible.builtin.<module>:
    param: "{{ item.???  }}"
  loop: "{{ ma_liste }}"
  loop_control:
    label: "{{ item.??? }}"   # affichage console plus lisible
  when: item.???              # filtre sur l'item courant
```

## 🧩 Squelette

```yaml
---
- name: Challenge - loop + when + loop_control
  hosts: db1.lab
  become: true

  vars:
    challenge_users:
      # ... 3 users (cf. ci-dessus) ...

  tasks:
    # Optionnel mais conseillé : nettoyer chal_bob s'il a été créé par erreur
    - name: S'assurer que chal_bob n'existe pas
      ansible.builtin.user:
        name: chal_bob
        state: absent
        remove: true

    - name: Créer les users actifs uniquement
      ansible.builtin.user:
        name: ???
        shell: ???
        state: present
      loop: ???
      loop_control:
        label: ???
      when: ???

    - name: Récapitulatif des users créés
      ansible.builtin.copy:
        dest: /tmp/loop-result.txt
        mode: "0644"
        content: "{{ challenge_users | selectattr(???) | map(attribute='???') | sort | join(',') }}\n"
```

> 💡 **`selectattr(...)` sans 2ᵉ argument** : par défaut, `selectattr('attr')`
> garde les éléments où `attr` est **truthy** (équivalent à `if item.attr`).

**Pièges** :

> - **`loop:`** est moderne (Ansible 2.5+). Évitez `with_items`
>   (déprécié). Cf. lab 22 pour la migration.
> - **`item`** est la variable par défaut dans une boucle. Pour la
>   renommer : `loop_control: { loop_var: user_data }`.
> - **`label:`** dans `loop_control` : contrôle ce qui s'affiche dans la
>   sortie Ansible (`label: "{{ item.name }}"` au lieu d'afficher tout
>   le dict).
> - **`selectattr` retourne un generator**. Chainer `| list` si vous
>   voulez `length` ou indexer (`[0]`).

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/boucles-loop/challenge/solution.yml
```

🔍 Vérifiez :

```bash
ansible db1.lab -m ansible.builtin.command -a "id chal_alice chal_charlie"
ansible db1.lab -m ansible.builtin.command -a "id chal_bob" || echo "chal_bob absent (OK)"
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/loop-result.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/boucles-loop/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/boucles-loop clean
```

Supprime les 3 users + le fichier marqueur.

## 💡 Pour aller plus loin

- **`with_items` (deprecated)** : ancienne syntaxe équivalente à `loop:`.
  Évitez-la dans le code neuf — `ansible-lint` la signale.
- **`loop_control: pause: 2`** : ajoute un délai entre chaque itération
  (utile pour ne pas surcharger une API tierce).
- **`loop_control: extended: true`** : expose `ansible_loop.index`,
  `ansible_loop.first`, `ansible_loop.last` (compteur, premier, dernier).
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/boucles-loop/challenge/solution.yml
   ```
