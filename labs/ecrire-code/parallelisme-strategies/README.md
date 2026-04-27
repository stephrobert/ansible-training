# Lab 09 — Parallélisme et stratégies (`serial:`, `forks:`, `strategy:`)

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

🔗 [**Parallélisme et stratégies Ansible : forks, serial, throttle, strategy**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/parallelisme-strategies/)

Par défaut, Ansible exécute une **tâche à la fois** sur **`forks` hôtes en parallèle**
(défaut 5). `serial:` change ce comportement par **batches successifs** — pratique pour
les **rolling updates** (mettre à jour 1 hôte, valider, passer au suivant). `strategy:`
change la philosophie : `linear` (défaut) attend que tous les hôtes finissent une tâche
avant de passer à la suivante ; `free` laisse chaque hôte avancer indépendamment.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Distinguer** `forks:` (parallélisme global) de `serial:` (taille de batch).
2. **Lancer** un rolling update sur les `webservers` avec `serial: 1`.
3. **Comparer** les stratégies `linear` (défaut) et `free` sur un play réaliste.
4. **Limiter** une seule tâche avec `throttle:` (rate-limit ciblé sans toucher au play).
5. **Choisir** la bonne combinaison `forks` / `serial` / `strategy` selon le scénario.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible webservers -m ping
# Doit lister web1.lab et web2.lab en SUCCESS
```

Nettoyer les marqueurs des runs précédents :

```bash
ansible webservers -b -m file -a "path=/tmp/serial-timestamp.txt state=absent"
ansible webservers -b -m file -a "path=/tmp/free-timestamp.txt state=absent"
```

## 📚 Exercice 1 — `serial: 1` (rolling update strict)

Créez `lab.yml` :

```yaml
---
- name: Demo serial 1 sur webservers
  hosts: webservers
  become: true
  serial: 1
  tasks:
    - name: Marquer le timestamp
      ansible.builtin.shell: |
        date --iso-8601=ns > /tmp/serial-timestamp.txt
      changed_when: true

    - name: Pause realiste avant le suivant (2s)
      ansible.builtin.pause:
        seconds: 2
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/lab.yml
```

🔍 **Observation** : web1 traite ses 2 tâches **complètement** avant que web2 commence.
Vérifiez les timestamps :

```bash
ansible webservers -b -m command -a "cat /tmp/serial-timestamp.txt"
```

Le timestamp de web2 doit être **postérieur d'au moins 2 secondes** à celui de web1.
C'est l'intérêt du `serial: 1` : si web1 plante, web2 n'est jamais touché.

## 📚 Exercice 2 — `serial: ["20%", "50%"]` (rolling progressif)

Sur 2 hôtes, `serial: ["20%", "50%"]` revient à 1 puis 1 (`max(1, 20% × 2)` = 1).
Pour démontrer le pattern, on simule 4 hôtes virtuels via `--limit` et le pattern de batches.

Modifiez le play pour ajouter un **second batch** explicite :

```yaml
serial:
  - 1
  - "100%"  # Tous les restants
```

🔍 **Observation** : Ansible affiche `PLAY [Demo serial 1 sur webservers]` deux fois — une
fois pour le **batch 1** (web1 seul), une fois pour le **batch 2** (web2 seul, ou tous
les autres si vous aviez 10 hôtes). Le `serial: ["10%", "50%", "100%"]` est le pattern
classique du **canary deploy** : 10% en premier (canari), 50% si OK, le reste à la fin.

## 📚 Exercice 3 — `strategy: free` vs `linear`

Créez `lab-strategy.yml` :

```yaml
---
- name: Demo strategy free
  hosts: webservers
  become: true
  strategy: free
  tasks:
    - name: Tache rapide (1s)
      ansible.builtin.pause:
        seconds: 1

    - name: Tache lente (5s)
      ansible.builtin.shell: |
        sleep 5
        date --iso-8601=ns > /tmp/free-timestamp.txt
      changed_when: true
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/lab-strategy.yml
```

🔍 **Observation** : avec `strategy: free`, **chaque hôte avance à son propre rythme**.
Les timestamps `/tmp/free-timestamp.txt` sur web1 et web2 sont **proches** (les hôtes
ont commencé la tâche lente en parallèle, pas en attendant que tous aient fini la
rapide).

**Comparez** avec `strategy: linear` (défaut) — modifiez à `strategy: linear` :

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/lab-strategy.yml
```

🔍 **Observation** : en `linear`, Ansible **attend** que tous les hôtes aient fini la
tâche rapide avant de lancer la lente. Si un hôte est plus lent que les autres (réseau,
charge), tout le play est ralenti.

**À retenir** : `linear` simplifie le debug et garantit l'ordre. `free` maximise le
débit mais brouille les logs.

## 📚 Exercice 4 — `throttle:` (rate-limit ciblé)

Vous avez un play sur 50 hôtes, `forks: 50`, mais **une seule tâche** appelle un
endpoint externe qui plafonne à 5 req/s. Inutile de mettre tout le play à `forks: 5`.

```yaml
- name: Tache qui appelle une API rate-limitee
  ansible.builtin.uri:
    url: https://api.example.com/register
    method: POST
  throttle: 5
```

`throttle: 5` limite **uniquement cette tâche** à 5 hôtes en parallèle, le reste du
play continue à `forks: 50`.

🔍 **Observation** : `throttle:` est local à la tâche. Pas besoin de modifier la config
globale d'Ansible.

## 📚 Exercice 5 — Le piège : `serial:` + handlers

Quand `serial: 1` est en place, les **handlers** se déclenchent **par batch**, pas à
la fin du play global. Cela peut surprendre.

Créez `lab-handlers.yml` :

```yaml
---
- name: Demo serial + handlers
  hosts: webservers
  become: true
  serial: 1
  tasks:
    - name: Modifier un fichier
      ansible.builtin.copy:
        content: "Modif au {{ ansible_date_time.iso8601 }}\n"
        dest: /tmp/lab-handler-trigger.txt
      notify: Recharger un service

  handlers:
    - name: Recharger un service
      ansible.builtin.debug:
        msg: "Handler tourne sur {{ inventory_hostname }} a {{ ansible_date_time.iso8601 }}"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/lab-handlers.yml
```

🔍 **Observation** : le handler `Recharger un service` tourne **2 fois** : une fois
après web1 (fin du batch 1), une fois après web2 (fin du batch 2). En **rolling update**,
c'est exactement ce que vous voulez (recharger nginx sur web1 avant de toucher à web2).
En **non-serial**, le handler aurait tourné **une seule fois** à la fin sur les deux hôtes
en parallèle.

## 🔍 Observations à noter

- **`forks:`** = parallélisme global (défaut 5, configurable dans `ansible.cfg`).
- **`serial:`** = taille de batch — divise le play en "vagues" séquentielles.
- **`serial:` accepte une liste** (`[1, 5, "100%"]`) pour des batches progressifs (canary deploy).
- **`strategy: linear`** synchronise les hôtes tâche par tâche. **`strategy: free`** laisse chacun avancer.
- **`throttle:`** rate-limit une tâche précise sans toucher au reste du play.
- **Handlers + `serial:`** = handlers déclenchés à chaque fin de batch (utile en rolling).

## 🤔 Questions de réflexion

1. Vous gérez 100 webservers et vous voulez déployer une nouvelle config nginx avec
   **rolling update**, en s'arrêtant si plus de 5% échouent. Quelles options du play
   utilisez-vous ? (combinaison de `serial:`, `max_fail_percentage:`, et stratégie).

2. Pourquoi `strategy: free` peut-il **accélérer un play** sur des hôtes hétérogènes
   (mix VMs lentes / rapides), mais **ralentir** sur des hôtes homogènes ?

3. Un collègue propose de mettre `forks: 200` dans `ansible.cfg` "pour aller plus vite".
   Quels sont les **3 risques** que vous identifiez avant d'accepter ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`max_fail_percentage:`** : tolère un % d'échecs par batch avant d'aborter. Combiné
  à `serial:`, c'est le pattern **rolling avec circuit-breaker**.
- **`any_errors_fatal:`** : à l'inverse, abort dès le premier échec — voir lab 25.
- **`run_once: true`** : exécuter une tâche **une seule fois** dans un play multi-hôtes
  (utile pour notifier un load-balancer externe). Voir lab 11 (delegation).
- **Mythe à casser** : augmenter `forks:` ne **multiplie pas** la vitesse. Bottleneck
  fréquent = la **fact gathering** sur trop d'hôtes en parallèle saturent le control node.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/parallelisme-strategies/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/parallelisme-strategies/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/parallelisme-strategies/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
