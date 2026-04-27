# Lab 25 — `ignore_errors:` (usage légitime vs anti-pattern)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo (cf.
> [README racine](../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**ignore_errors Ansible : usage légitime vs anti-pattern**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/ignore-errors/)

`ignore_errors: true` permet à une tâche d'**échouer** sans **arrêter le play**. La
tâche reste marquée `failed`, mais Ansible passe à la suivante. C'est l'**équivalent
du `try: ... except: pass`** Python — pratique mais souvent un anti-pattern parce
qu'il **masque les vraies erreurs**.

Dans 99% des cas, **`failed_when:`** (lab 24) ou **`block/rescue`** (lab 23) sont
préférables. `ignore_errors:` reste utile dans **3 cas légitimes** spécifiques.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Comprendre** l'effet de `ignore_errors: true` sur le PLAY RECAP.
2. **Identifier** les **3 cas légitimes** où `ignore_errors` est acceptable.
3. **Préférer** `failed_when:` ou `block/rescue` dans tous les autres cas.
4. **Combiner** `ignore_errors:` avec `register:` pour conditionner la suite.
5. **Diagnostiquer** un playbook qui masque silencieusement des erreurs.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
```

## 📚 Exercice 1 — Le comportement par défaut (sans `ignore_errors:`)

Créez `lab.yml` :

```yaml
---
- name: Demo sans ignore_errors
  hosts: db1.lab
  become: true
  tasks:
    - name: Tache 1 - OK
      ansible.builtin.debug:
        msg: "tache 1"

    - name: Tache 2 - echec garanti
      ansible.builtin.command: /bin/false

    - name: Tache 3 - jamais executee
      ansible.builtin.debug:
        msg: "tache 3"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/ignore-errors/lab.yml
```

🔍 **Observation** : la **tâche 2 plante**, le play **s'arrête**, **tâche 3 jamais
exécutée**. PLAY RECAP : `failed=1`. C'est le comportement standard.

## 📚 Exercice 2 — Avec `ignore_errors: true`

Modifiez la tâche 2 :

```yaml
- name: Tache 2 - echec mais on continue
  ansible.builtin.command: /bin/false
  ignore_errors: true
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/ignore-errors/lab.yml
```

🔍 **Observation** :

- Sortie console : `TASK [Tache 2 - echec mais on continue] : FAILED!` puis
  `...ignoring`.
- **Tâche 3 s'exécute**.
- PLAY RECAP : **`failed=0` mais `ignored=1`**.

C'est le **silencement contrôlé** : l'erreur est loguée mais n'arrête pas le play.
Le PLAY RECAP affiche `ignored=1` pour visibilité.

## 📚 Exercice 3 — Cas légitime n°1 : nettoyage opportuniste

Pattern : supprimer un fichier qui peut ou non exister, sans condition `stat:` préalable.

```yaml
- name: Nettoyer un eventuel lock orphelin
  ansible.builtin.file:
    path: /var/run/myapp.lock
    state: absent
  ignore_errors: true
```

🔍 **Observation** : si `/var/run/myapp.lock` existe → supprimé. S'il n'existe pas
→ tâche `ok` (pas d'erreur). **Si le module échoue pour une autre raison** (permission,
filesystem read-only), `ignore_errors:` masque cette erreur. **Mauvais usage**.

**Mieux** : utiliser `state: absent` directement sur le module `file:` (qui est
**idempotent** et ne fail pas sur fichier absent). **Pas besoin de `ignore_errors:`**.

→ Ce cas n'est en fait **pas légitime** parce que le module gère déjà l'absence.

## 📚 Exercice 4 — Cas légitime n°2 : audit / collecte d'info

Pattern : un play d'**audit** où on collecte de l'info sur N hôtes, et on accepte
que certains soient injoignables ou aient des facts manquants.

```yaml
- name: Audit des services
  hosts: all
  tasks:
    - name: Tester si nginx est installe
      ansible.builtin.command: rpm -q nginx
      register: nginx_check
      ignore_errors: true
      changed_when: false

    - name: Marquer le statut nginx
      ansible.builtin.debug:
        msg: "nginx sur {{ inventory_hostname }} : {{ 'installe' if nginx_check.rc == 0 else 'absent' }}"
```

🔍 **Observation** : `rpm -q` retourne `rc=1` si le paquet n'est pas installé. Avec
`ignore_errors: true`, on capture le rc dans `register:` et on l'utilise plus tard.

**Mais !** Cette tâche serait mieux écrite avec `failed_when: false` (équivalent
fonctionnel mais sémantiquement plus clair pour un audit) :

```yaml
- name: Tester si nginx est installe (audit-style)
  ansible.builtin.command: rpm -q nginx
  register: nginx_check
  failed_when: false
  changed_when: false
```

→ Ce cas est **un cas où `failed_when: false` est préférable à `ignore_errors:`**.

## 📚 Exercice 5 — Cas légitime n°3 : tâche optionnelle non critique

Pattern : envoyer une notification Slack en fin de deploy. Si Slack est down, le
deploy est quand même un succès.

```yaml
- name: Notifier Slack (best effort)
  ansible.builtin.uri:
    url: https://hooks.slack.com/services/...
    method: POST
    body: '{"text": "Deploy OK"}'
    body_format: json
  ignore_errors: true
```

🔍 **Observation** : si Slack répond `500` ou est injoignable, le play continue.
C'est légitime parce que la notification n'est **pas critique**.

**Variante préférable** : `block/rescue` qui **log le fail** dans un fichier sans
arrêter le play.

```yaml
block:
  - name: Notifier Slack
    ansible.builtin.uri: ...
rescue:
  - name: Logger l echec de notification
    ansible.builtin.lineinfile:
      path: /tmp/notification-failures.log
      line: "Slack notification failed at {{ ansible_date_time.iso8601 }}"
      create: true
```

→ Ce cas est **acceptable avec `ignore_errors:`** mais `block/rescue` est plus
visible et permet de tracer l'échec.

## 📚 Exercice 6 — Le danger : `ignore_errors:` masque tout

```yaml
# ❌ TRES dangereux
- name: Configurer la base de donnees
  ansible.builtin.shell: |
    /opt/app/setup-db.sh
  ignore_errors: true
```

🔍 **Observation** : si `setup-db.sh` plante (SQL invalide, password incorrect, disque
plein), Ansible **continue** le play comme si tout allait bien. La suite du déploiement
peut **réussir** alors que la **base de données est cassée**.

C'est l'**anti-pattern n°1** d'Ansible : `ignore_errors:` sur des opérations critiques
**masque** des erreurs majeures.

**Mitigation** :

- **Préférer `failed_when:`** avec une expression précise sur ce qui constitue un échec
  acceptable.
- **Utiliser `block/rescue`** pour rattraper et logger.
- **Ne jamais `ignore_errors:`** sur une opération qui modifie des données.

## 🔍 Observations à noter

- **`ignore_errors: true`** ne masque **pas** l'erreur — elle est dans `failed=N` du
  PLAY RECAP en mode standard, mais comptée en `ignored=N` avec ignore_errors.
- **3 cas légitimes** (et tous mieux servis par d'autres outils) :
  1. Nettoyage opportuniste → utiliser `state: absent` du module (idempotent par défaut).
  2. Audit / collecte → utiliser `failed_when: false` (sémantique plus claire).
  3. Notification non critique → utiliser `block/rescue` pour logger l'échec.
- **Anti-pattern** : `ignore_errors:` sur des opérations critiques (DB, deploy, secrets).
- **`register:` + `ignore_errors:`** = pattern d'audit classique mais à remplacer par `failed_when:`.

## 🤔 Questions de réflexion

1. Vous voyez `ignore_errors: true` 30 fois dans un repo legacy. Quelle est votre
   **première action** : remplacer par quoi, et dans quel ordre de priorité ?

2. Pourquoi `ignored=1` dans le PLAY RECAP est **plus dangereux** que `failed=1` ?
   (indice : penser à un opérateur qui scanne le PLAY RECAP en mode rapide).

3. Un collègue dit "j'utilise `ignore_errors: true` parce que c'est plus court que
   `failed_when: false`". Quels sont les **3 arguments** pour le faire changer
   d'avis ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`any_errors_fatal: true`** au niveau du play (lab 25) : à l'inverse de
  `ignore_errors`, force l'échec du play entier dès la première erreur — utile
  pour les opérations cluster qui doivent être atomiques.
- **`failed_when: false`** (lab 23) : équivalent fonctionnel de `ignore_errors:`
  mais plus expressif (on indique **explicitement** qu'on ne considère pas l'erreur
  comme un échec).
- **`block/rescue`** (lab 23) : la **vraie** alternative pour rattraper et **agir**
  sur l'erreur (notification, rollback, log).
- **Ansible Lint rule `ignore-errors`** : règle qui flag tous les `ignore_errors: true`
  comme **warning**. À activer en CI pour forcer une review humaine.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/ignore-errors/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/ignore-errors/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/ignore-errors/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
