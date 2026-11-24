# Trois comptes demandés, un déjà révoqué

## La situation

Les RH ont envoyé la liste : trois comptes à créer sur **db1.lab**, chacun
avec son shell. Entre la demande et aujourd'hui, l'un d'eux a été révoqué : la
personne n'a jamais rejoint l'entreprise. La liste porte toujours les trois,
avec un drapeau qui dit lesquels sont actifs, parce que cette liste est la
source de vérité et que personne n'a le droit de la tailler à la main. Votre
playbook doit lire le drapeau, pas la longueur.

Vous l'écrivez depuis **control-node.lab**.

Votre mission :

1. Itérer sur la liste des comptes et ne créer **que ceux marqués actifs**,
   chacun avec le shell qu'il réclame.
2. Garantir que le compte révoqué **n'existe pas** sur l'hôte, même si un run
   antérieur l'avait créé avant la révocation.
3. Garder la console lisible : quarante comptes affichés en dicts bruts, c'est
   un mur de bruit. **Étiquetez** chaque itération par son nom.
4. Écrire un récapitulatif listant les comptes actifs, par ordre alphabétique
   et séparés par des virgules, dérivé de cette même liste plutôt que ressaisi.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-loop/

## 🎯 Challenge — Créer 3 users dont 2 actifs (`loop` + `when` + `loop_control`)

### ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Itère sur une liste de 3 users.
2. Crée **uniquement** ceux qui ont `enabled: true` (filtre via `when:` sur
   l'item).
3. Pose un fichier récapitulatif `/tmp/loop-result.txt` listant les users
   actifs (séparés par virgule, ordre alphabétique).

### 🧩 Données d'entrée

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

### 🧩 Modèle d'une boucle conditionnelle

```yaml
- name: Faire qqch sur certains items seulement
  ansible.builtin.<module>:
    param: "{{ item.???  }}"
  loop: "{{ ma_liste }}"
  loop_control:
    label: "{{ item.??? }}"   # affichage console plus lisible
  when: item.???              # filtre sur l'item courant
```

### 🧩 Squelette

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

### 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/boucles-loop/challenge/solution.yml
```

🔍 Vérifiez :

```bash
ansible db1.lab -m ansible.builtin.command -a "id chal_alice chal_charlie"
ansible db1.lab -m ansible.builtin.command -a "id chal_bob" || echo "chal_bob absent (OK)"
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/loop-result.txt"
```

### 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/boucles-loop/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-boucles-loop
```

Supprime les 3 users + le fichier marqueur.

### 💡 Pour aller plus loin

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
