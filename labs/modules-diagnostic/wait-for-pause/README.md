# Lab 54 — Modules `wait_for:` et `pause:` (synchronisation)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.

## 🧠 Rappel

🔗 [**Modules wait_for et pause Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/wait-for-pause/)

Deux modules pour la **synchronisation temporelle** dans un play :

- **`ansible.builtin.wait_for:`** = attendre **une condition** (port ouvert,
  fichier créé, regex dans un fichier, machine SSH-prête). Sondage actif.
- **`ansible.builtin.pause:`** = attendre **un délai fixe** (secondes/minutes)
  ou demander une **confirmation interactive** à l'opérateur.

`wait_for:` est le **bon choix** dans 90% des cas — sondage actif jusqu'à
condition vraie. `pause:` est utile pour des **délais incompressibles** ou
des **confirmations humaines**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Attendre l'ouverture d'un port** TCP (cas le plus courant).
2. **Attendre la fermeture** d'un port (`state: stopped`).
3. **Attendre l'apparition d'un fichier** ou une **regex** dans un fichier.
4. **Pause** simple (`seconds:`) ou interactive (`prompt:`).
5. **Diagnostiquer** un timeout `wait_for:` (mauvais host, port firewallé).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/lab-waitfor-*"
```

## 📚 Exercice 1 — `wait_for: port:` (le plus courant)

Pattern n°1 : après démarrage d'un service, attendre que le port soit prêt
avant les tâches qui en dépendent.

```yaml
---
- name: Demo wait_for port
  hosts: db1.lab
  become: true
  tasks:
    - name: Demarrer chronyd (s il ne tourne pas)
      ansible.builtin.systemd_service:
        name: chronyd
        state: started

    - name: Attendre que le port chronyd 323 soit pret
      ansible.builtin.wait_for:
        port: 323
        host: 127.0.0.1
        timeout: 10
```

🔍 **Observation** : `wait_for:` polle (par défaut toutes les secondes) jusqu'à
ce que le port soit ouvert, ou échoue après `timeout:` secondes.

**`host:`** par défaut = `127.0.0.1`. Pour tester un port d'un autre host
depuis le managed node, spécifier `host: 10.10.20.21`.

## 📚 Exercice 2 — `state: stopped` (attendre la fermeture)

```yaml
- name: Verifier que le port 9999 est BIEN libre
  ansible.builtin.wait_for:
    port: 9999
    host: 127.0.0.1
    state: stopped
    timeout: 5
```

🔍 **Observation** : `state: stopped` = **succès si le port est libre**.
Pratique avant de démarrer un service — vérifier que rien d'autre n'utilise
le port.

**Cas d'échec** : si le port est occupé après `timeout`, la tâche **failed**.
Permet d'arrêter le play avant un conflit.

## 📚 Exercice 3 — `wait_for: path:` (apparition d'un fichier)

```yaml
- name: Lancer une commande qui crée un fichier (en arriere-plan)
  ansible.builtin.shell: |
    ( sleep 3 && touch /tmp/lab-waitfor-marker.txt ) &
    echo "lance en arriere-plan"
  changed_when: false

- name: Attendre que le fichier apparaisse
  ansible.builtin.wait_for:
    path: /tmp/lab-waitfor-marker.txt
    timeout: 10
```

🔍 **Observation** : `wait_for: path:` polle jusqu'à ce que le fichier
**existe**. Utile pour synchroniser avec un process asynchrone qui crée un
flag-file en fin de traitement.

## 📚 Exercice 4 — `wait_for: search_regex:` (chercher une regex)

```yaml
- name: Verifier qu un service a logge "Ready" dans son journal
  ansible.builtin.wait_for:
    path: /var/log/messages
    search_regex: 'systemd.*Started.*chronyd'
    timeout: 30
```

🔍 **Observation** : `wait_for:` lit le fichier et teste la regex à chaque
poll. Apparaît dans le contenu → succès. Timeout → failed.

**Cas d'usage** : attendre le log "Server ready" d'une app, "Database
initialized", etc.

**Limitation** : `wait_for: search_regex:` lit le fichier **à chaque poll** —
sur un log de plusieurs Go, c'est lent. Pour des logs très volumineux,
préférer `tail -F` + grep ou un module dédié.

## 📚 Exercice 5 — `pause:` simple (délai fixe)

```yaml
- name: Demarrer le service
  ansible.builtin.systemd_service:
    name: chronyd
    state: restarted

- name: Pause de 5 secondes pour stabilisation
  ansible.builtin.pause:
    seconds: 5

- name: Verifier la suite
  ansible.builtin.command: chronyc tracking
  register: chrony_status
  changed_when: false
```

🔍 **Observation** : **`pause: seconds:`** = sleep en début de play. Simple
mais **pas adaptatif** (5s même si le service est prêt en 1s). Préférer
`wait_for:` quand une condition précise existe.

**Quand préférer `pause:` à `wait_for:`** :

- Pas de condition précise mesurable.
- Délai imposé par un système externe (cool-down API).
- Test de configurations qui doivent prendre effet dans un temps fixé.

## 📚 Exercice 6 — `pause: prompt:` (confirmation interactive)

```yaml
- name: Confirmation manuelle avant migration BDD
  ansible.builtin.pause:
    prompt: |
      Vous allez lancer la migration de la base de production.
      Tapez ENTER pour continuer, Ctrl+C pour annuler.
```

🔍 **Observation** : Ansible **bloque** le play en attendant une touche. Cas
d'usage : opérations critiques où un humain doit valider.

**Pattern CI/CD** : ajouter `pause: + when: confirm_required | bool` pour
n'avoir la confirmation **qu'en mode interactif**.

```yaml
- ansible.builtin.pause:
    prompt: "Confirmer la migration ? "
  when: confirm_required | default(false) | bool
```

En CI : `--extra-vars "confirm_required=false"` saute la pause.
En manuel : on demande confirmation.

## 📚 Exercice 7 — Le piège : `wait_for:` qui plante au démarrage

Ansible peut **lancer** un service via `systemd_service:` et **passer
immédiatement** à `wait_for: port:` — sans attendre que systemd ait
réellement démarré le binaire.

```yaml
# ❌ Race condition possible
- ansible.builtin.systemd_service:
    name: myapp
    state: started

- ansible.builtin.wait_for:
    port: 8080
    timeout: 30
  # Si myapp met 35s a demarrer → wait_for failed
```

🔍 **Observation** : la **race** se produit si la VM est lente ou si l'app
prend du temps à initialiser ses sockets. Ansible ne sait **pas** distinguer
"systemd a accepté de start" de "le service écoute".

**Mitigation** :

- **Augmenter `timeout:`** : si l'app peut prendre 60s, mettre `timeout: 90`.
- **`pause:` minimum** avant le `wait_for:` : laisser au moins quelques
  secondes au service pour démarrer son réseau.
- **Combiner avec `until:` sur `uri:`** : tester un endpoint HTTP plutôt qu'un
  port TCP brut (lab 50).

## 📚 Exercice 8 — `delay:` pour des sondages plus espacés

```yaml
- name: Attendre un service lent (poll moins frequent)
  ansible.builtin.wait_for:
    port: 8080
    timeout: 300
    delay: 10        # Attendre 10s avant le 1er sondage
    sleep: 5         # 5s entre chaque sondage
```

🔍 **Observation** : par défaut, `wait_for:` sonde **toutes les secondes** dès
le départ. Sur un service très lent (Docker registry, base de données), c'est
trop. **`delay:`** retarde le 1er sondage. **`sleep:`** espace les sondages
suivants.

## 🔍 Observations à noter

- **`wait_for:`** = sondage actif jusqu'à condition vraie.
- **`port:`** + `state: started/stopped` = test de port le plus courant.
- **`path:`** = attendre l'apparition d'un fichier.
- **`search_regex:`** = chercher une chaîne dans un fichier (lent sur gros logs).
- **`pause: seconds:`** = sleep simple, **non adaptatif**.
- **`pause: prompt:`** = confirmation interactive humaine.
- **`timeout:`** sur `wait_for:` = à dimensionner avec marge (× 2 ou × 3 du
  temps attendu).

## 🤔 Questions de réflexion

1. Vous démarrez `nginx` qui peut prendre 2s à 30s selon la charge. Quelle
   combinaison `systemd + wait_for` (avec quels paramètres) garantit le moins
   de risque sans trop d'attente ?

2. Différence entre `wait_for: port:` (test TCP brut) et `uri: until:` (test
   HTTP avec status code) ? Quand préférer chaque ?

3. Vous voulez **bloquer le play** entre 2 batchs `serial: 1` pour vérifier
   manuellement le 1er hôte avant de toucher au 2e. Quel pattern ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`active_connection_states:`** : lister les états TCP acceptés (`ESTABLISHED`,
  `LISTEN`, `SYN_SENT`, etc.). Avancé.
- **`exclude_hosts:`** : `wait_for:` distribué sur plusieurs hôtes — exclure
  certains.
- **Module `community.general.timeout`** : décorateur pour limiter une tâche
  arbitraire dans le temps.
- **`uri: + until:`** (lab 50) : alternative à `wait_for: port:` qui teste
  aussi l'**applicatif** (HTTP 200 + body OK), pas juste le port TCP.
- **Lab 50 (`uri:`)** + **Lab 53 (`assert:`)** : combinaison `wait_for + uri +
  assert` pour des healthchecks robustes.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-diagnostic/wait-for-pause/lab.yml
ansible-lint labs/modules-diagnostic/wait-for-pause/challenge/solution.yml
ansible-lint --profile production labs/modules-diagnostic/wait-for-pause/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
