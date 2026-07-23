# 🎯 Challenge — Déploiement atomique : prouver `any_errors_fatal`

## ✅ Objectif

Écrire `challenge/solution.yml` : un déploiement en **deux étapes** sur les
2 webservers, avec entre les deux un **contrôle de santé** qui peut échouer
sur un hôte donné. La règle du jeu : si le contrôle échoue sur **un seul**
hôte, **aucun** hôte ne doit activer la release. C'est exactement ce que
garantit `any_errors_fatal: true`, et c'est ce que les tests **prouvent**
en provoquant réellement l'échec.

## 🧩 Contrat attendu

Le playbook cible `webservers`, en `become: true`, et déclare une variable
`fail_host` valant `"none"` par défaut (surchargée par les tests via
`-e fail_host=web1.lab` pour simuler l'incident).

| Étape | Tâche | État produit |
| --- | --- | --- |
| 1 | Préparer la release | `/tmp/anyfatal-step1-{{ inventory_hostname }}.txt`, contient `step1 OK on <hôte>`, mode `0644` |
| 2 | Contrôle de santé | `ansible.builtin.command: /bin/false` exécutée **uniquement** quand `inventory_hostname == fail_host` |
| 3 | Activer la release | `/tmp/anyfatal-release-{{ inventory_hostname }}.txt`, contient `release OK on <hôte>`, mode `0644` |

Comportements que les tests vérifient sur les VMs :

1. **Run incident** (`-e fail_host=web1.lab`) : le playbook sort en erreur,
   l'étape 1 est posée sur les 2 hôtes, et le fichier release n'existe
   **ni sur web1** (il a échoué) **ni sur web2** (le play s'est arrêté
   partout). Sans `any_errors_fatal: true`, web2 aurait continué et posé sa
   release : le test échoue.
2. **Run nominal** (sans `-e`) : le playbook réussit et les 2 hôtes ont
   l'étape 1 **et** la release.
3. **Idempotence** : un second run nominal affiche `changed=0` partout.

## 🧩 Squelette

```yaml
---
- name: Déploiement atomique sur les webservers
  hosts: ???
  become: ???
  gather_facts: false
  ???: true                          # le mot-clé du lab, au niveau du play
  vars:
    fail_host: ???                   # aucun hôte ne doit matcher par défaut

  tasks:
    - name: Préparer la release (étape 1)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"

    - name: Contrôle de santé (échoue sur fail_host)
      ansible.builtin.command: /bin/false
      when: ???
      changed_when: false

    - name: Activer la release (étape 3)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **Mot-clé play-level, pas task-level** : `any_errors_fatal: true` se place
>   à la racine du play, au même niveau que `hosts:` et `become:`.
> - **`{{ inventory_hostname }}` dans `dest:`** : un fichier par hôte, sinon
>   les 2 webservers s'écrasent mutuellement.
> - **`when: inventory_hostname == fail_host`** : le contrôle ne doit planter
>   que sur l'hôte désigné. Avec `fail_host=none`, personne ne matche et le
>   play converge.
> - **`changed_when: false`** sur le `command` : sans lui, `ansible-lint`
>   (règle `no-changed-when`) refuse le playbook, et l'idempotence est fausse.

## 🚀 Lancement

```bash
# Run incident : web1 échoue, PERSONNE ne doit poser la release
ansible-playbook labs/ecrire-code/any-errors-fatal/challenge/solution.yml \
    -e fail_host=web1.lab
ansible webservers -b -m ansible.builtin.command -a "ls /tmp/"  # pas de anyfatal-release-*

# Run nominal : tout le monde converge
ansible webservers -b -m ansible.builtin.shell -a "rm -f /tmp/anyfatal-*.txt"
ansible-playbook labs/ecrire-code/any-errors-fatal/challenge/solution.yml
```

🔍 Sur le run incident, le `PLAY RECAP` affiche `failed=1` sur web1 et
`failed=0` sur web2 : web2 n'a planté sur aucune tâche, il n'est donc pas
marqué en échec. La signature de `any_errors_fatal` est ailleurs : web2
**s'arrête quand même**, ses tâches suivantes ne sont pas exécutées et son
compteur `ok` reste en deçà de ce qu'un run nominal donnerait.

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/any-errors-fatal/challenge/tests/
```

Les tests rejouent eux-mêmes les deux runs (incident puis nominal) et
vérifient l'état des deux VMs, assertions positives **et** négatives.

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-any-errors-fatal
```

## 💡 Pour aller plus loin

- **Retirez `any_errors_fatal: true`** et relancez le run incident : web2
  pose sa release alors que web1 a planté. C'est le drift « moitié du parc »
  du scénario, et c'est pour cela que les tests l'interdisent.
- **`serial: 1` + `any_errors_fatal: true`** : sur 10 hôtes, un échec dans le
  batch 2 empêche les batches 3 à 10 de démarrer.
- **`max_fail_percentage`** : tolérance en pourcentage, là où
  `any_errors_fatal` est tolérance zéro (`max_fail_percentage: 0` est
  équivalent).
- **Lint** :

   ```bash
   ansible-lint --profile production labs/ecrire-code/any-errors-fatal/challenge/solution.yml
   ```
