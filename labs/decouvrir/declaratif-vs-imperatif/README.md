# Lab 01 — Déclaratif vs impératif (pourquoi Ansible n'est pas du Bash)

> ⚠️ **Premier lab — vérifiez que vos 4 VMs tournent avant de commencer.**
>
> Tous les labs s'exécutent sur **4 VMs AlmaLinux** provisionnées localement
> via libvirt/KVM (`control-node`, `web1`, `web2`, `db1`). Si vous arrivez
> sur ce repo pour la première fois, vous devez les créer **une seule fois** :
>
> ```bash
> cd <ansible-training>          # racine du repo
> make bootstrap                 # installe Ansible + libvirt + outils (~3 min, 1×)
> make provision                 # crée les 4 VMs + prépare les managed nodes (~5 min)
> make hosts-add                 # ajoute web1.lab/web2.lab/db1.lab dans /etc/hosts (sudo)
> make ssh-config-add            # 'ssh ansible@web1.lab' utilise la clé du repo
> make verify-conn               # → 4 "pong" attendus (validation finale)
> ```
>
> Vérification rapide à tout moment :
>
> ```bash
> ansible all -m ansible.builtin.ping
> # control-node.lab | SUCCESS => {"ping": "pong"}
> # web1.lab         | SUCCESS => {"ping": "pong"}
> # web2.lab         | SUCCESS => {"ping": "pong"}
> # db1.lab          | SUCCESS => {"ping": "pong"}
> ```
>
> | Action | Commande |
> | --- | --- |
> | Voir l'état des VMs | `virsh list --all` |
> | Voir l'état des hostnames du lab | `make hosts-status` |
> | Snapshot avant un lab risqué | `make snapshot` |
> | Restaurer le snapshot | `make restore` |
> | Détruire toutes les VMs (après formation) | `make destroy` |
> | Retirer les hostnames de `/etc/hosts` | `make hosts-remove` |
> | État de la config SSH du lab | `make ssh-config-status` |
> | Retirer la config SSH du lab | `make ssh-config-remove` |
>
> Pour les détails (topologie réseau, ressources requises, troubleshooting),
> voir [README racine](../../README.md) sections « Topologie du lab » et
> « Pré-requis poste de travail ».

## 🧠 Rappel et lecture recommandée

> 📖 **Avant de pratiquer, lisez le guide blog associé** — il pose le contexte
> théorique (histoire d'Ansible, Push vs Pull, idempotence) que ce lab vient
> illustrer concrètement :
>
> 🔗 [**Déclaratif vs impératif : la même tâche, deux philosophies**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/declaratif-vs-imperatif/)
>
> ⏱ Temps de lecture : ~10 min. Le guide explique le **pourquoi**, ce lab vous
> fait sentir le **comment** dans la pratique. Les deux ensemble = déclic
> mental garanti.

### En 30 secondes

**Impératif** = vous décrivez **les étapes** (« installe nginx, ajoute cette ligne, démarre le service »). À chaque relance, le script refait toutes les étapes — et **dérive** si l'une d'elles n'est pas idempotente (ex. ajouter une ligne).

**Déclaratif** = vous décrivez **l'état désiré** (« nginx présent, page d'accueil contenant cette ligne, service démarré »). Ansible compare avec l'état actuel et **n'agit que si nécessaire**. Au second passage, plus rien à faire — c'est le signal `changed=0` du `PLAY RECAP`.

C'est le **déclic mental** de la formation : sans cette différence comprise, on écrit du Bash en YAML et on passe à côté de l'apport d'Ansible.

## 🎯 Objectifs

À la fin de ce lab, vous aurez **vu de vos yeux** :

1. Un script Bash naïf qui **dérive** à chaque exécution sur la même cible.
2. Un playbook Ansible qui réalise le même objectif et **converge** vers l'état désiré.
3. La différence concrète entre **idempotent** et **non-idempotent**.
4. Le signal `changed=0` au second passage — la preuve mécanique de l'idempotence.

## 🔧 Préparation

Vérifiez que les VMs du lab tournent et que `web1.lab` répond :

```bash
cd /home/bob/Projets/ansible-training
ansible web1.lab -m ping
```

Réponse attendue : `web1.lab | SUCCESS => {"ping": "pong"}`. Si vous obtenez `UNREACHABLE`, lancez `make provision` à la racine du repo.

> 💡 **Note** : ce lab est livré clé en main (`playbook.yml` + `Makefile` + script Bash). Vous n'avez **rien à écrire** — vous allez **observer** la différence. Les labs suivants à partir du 04 vous demanderont, eux, d'écrire le code.

## ⚙️ Arborescence du lab

```text
labs/decouvrir/declaratif-vs-imperatif/
├── README.md                           ← ce fichier
├── Makefile                            ← orchestre le scénario complet
├── playbook.yml                        ← l'équivalent Ansible déclaratif
├── scripts/
│   └── install-nginx-impératif.sh      ← le script Bash naïf
└── challenge/
    └── tests/
        └── test_*.py                   ← pytest+testinfra qui valide la convergence
```

## 📚 Exercice 1 — Lire le script Bash impératif

Ouvrez le script et lisez-le **avant de l'exécuter** :

```bash
cat labs/decouvrir/declaratif-vs-imperatif/scripts/install-nginx-impératif.sh
```

Repérez les 3 étapes : (1) installer nginx, (2) **ajouter une ligne** `Servi par <hostname>` à `index.html`, (3) démarrer nginx.

🔍 **Observation à anticiper** : l'étape (2) utilise `echo "..." >> index.html` — un **append**. Rien ne vérifie si la ligne est déjà là. À chaque relance, on ajoute une ligne en plus.

## 📚 Exercice 2 — Voir le script Bash dériver

Le `Makefile` du lab joue le script **3 fois** d'affilée :

```bash
cd labs/decouvrir/declaratif-vs-imperatif
make run-bash
```

🔍 **Observation** — sortie attendue :

```text
--- Run #1 ---
OK : nginx déployé. Occurrences de 'Servi par' dans la page : 1
--- Run #2 ---
OK : nginx déployé. Occurrences de 'Servi par' dans la page : 2
--- Run #3 ---
OK : nginx déployé. Occurrences de 'Servi par' dans la page : 3
```

À chaque run, **le compteur grimpe d'une ligne** — c'est la dérive. Vérifiez sur le managed node :

```bash
ssh ansible@web1.lab 'sudo grep -n "Servi par" /usr/share/nginx/html/index.html'
```

Vous voyez **3 lignes** `<p>Servi par web1.lab</p>` accumulées. C'est la **dérive** typique du modèle impératif : le script ne vérifie pas l'état, il `tee -a` aveuglément à chaque appel.

> 💡 **Détail technique** : `/usr/share/nginx/html/index.html` est en fait un **lien symbolique** vers `/usr/share/testpage/index.html` (un fichier livré par le paquet `almalinux-logos-httpd`, partagé avec Apache). Le `tee -a` modifie donc le **vrai fichier** pointé par le lien — et c'est lui qui persiste entre les runs si le `setup` ne le purge pas. Le `make setup` du lab fait précisément ce nettoyage via `sed -i '/<p>Servi par /d' ...`.

## 📚 Exercice 3 — Voir le playbook Ansible converger

Réinitialisez l'état (le `Makefile` désinstalle nginx et nettoie le fichier) puis lancez **3 fois** le playbook :

```bash
make setup
make run-ansible
```

🔍 **Observation** : à chaque run, `index.html` contient **toujours 1 ligne**. Vérifiez :

```bash
ssh ansible@web1.lab 'sudo cat /usr/share/nginx/html/index.html'
```

Le playbook a comparé l'état actuel à l'état désiré, vu qu'il était déjà conforme, et **n'a rien fait**. Regardez aussi le `PLAY RECAP` du second run — `changed=0` partout. C'est l'**idempotence** en action.

## 📚 Exercice 4 — Comparer le `playbook.yml` et le script

Ouvrez les deux fichiers côte à côte :

```bash
cat labs/decouvrir/declaratif-vs-imperatif/playbook.yml
cat labs/decouvrir/declaratif-vs-imperatif/scripts/install-nginx-impératif.sh
```

🔍 **Observation** :

- Le script Bash **enchaîne des commandes**, sans état mémorisé.
- Le playbook **déclare** un état (`state: present`, `state: started`, contenu exact via `copy:` + `content:`). Le module `copy:` **compare le checksum** avant d'écrire — pas d'écriture si identique.
- Le playbook est **plus court** parce qu'il s'appuie sur l'idempotence native des modules `dnf`, `copy`, `systemd`.

## 📚 Exercice 5 — Vérifier l'idempotence par les tests

```bash
make verify
```

Cette cible :

1. Lance la suite `pytest+testinfra` (vérifie que nginx est installé/running, qu'`index.html` contient **exactement** une ligne `Servi par`).
2. Relance le playbook une fois de plus et **grep** `changed=0` dans la sortie — preuve d'idempotence stricte.

🔍 **Observation** : si vous aviez accidentellement écrit le playbook avec une tâche `shell:` non idempotente, le test `changed=0` échouerait. C'est la garantie automatique qu'on construit toute la formation autour.

## 📚 Exercice 6 — Nettoyer

```bash
make clean
```

Désinstalle nginx, retire la règle firewalld, supprime `index.html`. Le lab est prêt à être rejoué from scratch.

## 🔍 Observations à noter

- **Impératif** = suite d'étapes ; le résultat dépend du **nombre de fois** où on lance.
- **Déclaratif** = état désiré ; le résultat dépend uniquement de la **cible décrite**.
- Un module est dit **idempotent** si le second run ne change rien. La quasi-totalité des modules `ansible.builtin.*` le sont — sauf `shell:` et `command:` (qui ré-exécutent à chaque fois).
- Le `PLAY RECAP` final affiche `changed=0` : c'est le **signal mécanique** d'un playbook idempotent. C'est le critère qu'on cherchera à tous les labs suivants.
- `creates:` / `removes:` permettent de rendre un `shell:` idempotent (il ne s'exécute que si le marqueur de fichier est absent / présent).

## 🤔 Questions de réflexion

1. Imaginez un script Bash qui doit ajouter `PermitRootLogin no` à `/etc/ssh/sshd_config`. Comment le rendre idempotent **sans** Ansible ? Quels pièges (regex, ligne déjà commentée, ligne avec espaces différents) ?

2. Le playbook utilise `copy:` + `content:` pour poser `index.html`. Pourquoi est-ce idempotent même si `index.html` existait déjà ? Que compare le module ?

3. Si une équipe livre 200 serveurs et que chacun reçoit ce lab, le **résultat final** est-il identique à 1 ou 200 runs du playbook ? Et avec le script Bash ?

## 🚀 Pour aller plus loin

- **Rendez le script Bash idempotent** : ajoutez `grep -q "Servi par" /usr/share/nginx/html/index.html || echo "..." >>` pour ne plus dériver. Constatez : c'est faisable, mais on a réinventé l'idempotence à la main pour **une seule** ligne. Imaginez sur 50 fichiers.
- **Remplacez `copy:` par `lineinfile:`** dans `playbook.yml`. Comparez : `copy:` est idempotent par checksum (le fichier entier), `lineinfile:` par regex (une ligne). Quand préférer l'un ou l'autre ?
- **Ajoutez `creates: /var/lib/nginx-installed.flag`** sur une fausse tâche `ansible.builtin.shell:` puis observez le `skipped` au second run — c'est le pont entre `shell:` et idempotence.

## 🔍 Linter avec `ansible-lint`

Ce lab est livré clé en main — pas de `lab.yml` ni de `challenge/solution.yml`
à écrire. Vous pouvez tout de même linter le `playbook.yml` du lab pour voir
à quoi ressemble une sortie `ansible-lint` propre :

```bash
ansible-lint labs/decouvrir/declaratif-vs-imperatif/playbook.yml
ansible-lint --profile production labs/decouvrir/declaratif-vs-imperatif/playbook.yml
```

Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

> 💡 **À retenir** : `ansible-lint --profile production` est le standard
> RHCE 2026. Il vérifie FQCN, `name:` sur chaque tâche, modes quotés,
> idempotence, modules non dépréciés. Adoptez-le dès vos premiers playbooks.
