# Lab 57 : Inventaire dynamique KVM avec community.libvirt.libvirt

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis pour ce lab :
>
> - Les 4 VMs du lab tournent sous **libvirt/KVM** (pas d'autre hyperviseur).
> - Le **plugin Python `libvirt`** est installé dans l'environnement Ansible.
> - L'utilisateur courant a accès à `qemu:///system`.
>
> Test d'avant-démarrage :
>
> ```bash
> virsh -c qemu:///system list                       # liste des VMs visibles
> python3 -c "import libvirt; print('OK')"           # bindings Python OK
> ansible-galaxy collection list community.libvirt   # collection installée
> ```
>
> Si les bindings manquent : `pipx inject ansible libvirt-python`.

## 🧠 Rappel

🔗 [**Inventaire dynamique pour KVM**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/dynamiques/plugin-libvirt-kvm/)

Le plugin **`community.libvirt.libvirt`** interroge l'**API libvirt** locale et génère un inventaire **à chaque exécution** d'Ansible. Plus besoin de maintenir manuellement la liste des hôtes : créez une VM, elle apparaît immédiatement dans l'inventaire.

**Limite** : le plugin retourne le **nom du domaine** libvirt et son **état**, mais **pas d'IP exploitable**. Il expose bien `interface_addresses` et `guest_info`, mais ces deux variables exigent l'**agent QEMU** (`qemu-guest-agent`) installé dans la VM et le canal `org.qemu.guest_agent.0` configuré. Ce n'est pas le cas ici : les deux ne contiennent qu'une erreur.

```bash
ansible-inventory -i inventory/ --host web1.lab 2>/dev/null | grep -A2 interface_addresses
```

```json
"interface_addresses": {
    "error": "argument unsupported: QEMU guest agent is not configured"
},
```

Pour la connexion SSH, on combine donc le plugin avec des **variables statiques** qui disent **comment** joindre les VMs. Attention : **pas en y écrivant des IP**. Terraform les attribue et les change à chaque reprovisionnement ; une IP figée dans un inventaire est une IP fausse dès le lendemain. On délègue la résolution au **`ssh_config` généré par dsoxlab**, qui porte les adresses réelles, l'utilisateur et la clé.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Configurer** le plugin `community.libvirt.libvirt` avec `qemu:///system`.
2. **Créer des groupes logiques** via `groups:` Jinja (`webservers`, `dbservers`).
3. **Filtrer par état** avec `keyed_groups` pour obtenir `state_running`.
4. **Combiner** le plugin avec des variables statiques pour les paramètres SSH, en comprenant la **précédence** qui décide qui gagne.
5. **Démontrer** que l'inventaire reflète l'état du parc **au moment du run**.

## 🔧 Préparation

```bash
cd $ANSIBLE_TRAINING/labs/inventaires/dynamique-kvm
```

## ⚙️ Arborescence cible

```text
labs/inventaires/dynamique-kvm/
├── README.md                    ← ce fichier
├── inventory/
│   ├── 01-libvirt.yml           ← plugin community.libvirt.libvirt
│   ├── group_vars/
│   │   └── lab_vms.yml          ← paramètres SSH communs (via ssh_config)
│   └── host_vars/
│       ├── control-node.lab.yml ← override ansible_connection (précédence hôte)
│       ├── web1.lab.yml
│       ├── web2.lab.yml
│       └── db1.lab.yml
└── challenge/
    ├── README.md
    ├── solution.yml             ← à écrire : marque les VMs running du lab
    └── tests/
        └── test_functional.py
```

## 📚 Exercice 1 : configurer le plugin libvirt

Le fichier `inventory/01-libvirt.yml` :

```yaml
---
plugin: community.libvirt.libvirt
uri: qemu:///system
inventory_hostname: name
strict: false

groups:
  lab_vms: inventory_hostname in ['control-node.lab', 'web1.lab', 'web2.lab', 'db1.lab']
  webservers: inventory_hostname in ['web1.lab', 'web2.lab']
  dbservers: inventory_hostname == 'db1.lab'
  control: inventory_hostname == 'control-node.lab'

keyed_groups:
  - prefix: state
    key: info.state
```

🔍 **Observation** :

- **`plugin:`** au top-level dit à Ansible que ce fichier est une config de plugin (pas un inventaire YAML classique).
- **`uri:`** indique le socket libvirt : `qemu:///system` pour KVM root, `qemu:///session` pour user-mode.
- **`inventory_hostname: name`** fait porter à l'hôte le **nom du domaine libvirt**, celui qu'affiche `virsh list --all`. Ici les domaines s'appellent `web1.lab`, `db1.lab`… : c'est ce nom, et lui seul, que voient les filtres. Un filtre écrit sur `web1` ne matcherait **rien**, en silence.
- **`groups:`** crée des groupes logiques par condition Jinja évaluée **par VM**.
- **`keyed_groups:`** crée un groupe par **valeur** d'une variable : `state_running`, `state_shutoff`…
- **`strict: false`** (le défaut) : une condition qui référence une variable absente écarte l'hôte du groupe au lieu de faire échouer tout le run. C'est ce qui rend l'inventaire tolérant aux VMs que libvirt refuse de détailler (« domain is not running »).

⚠️ **Le piège de `keyed_groups`** : la clé est **`info.state`**, pas `state`. Le plugin range l'état du domaine dans un dictionnaire `info`. Avec `key: state`, la variable n'existe pas, `strict: false` avale l'erreur, le groupe `state_running` n'est **jamais créé**, et un play qui cible `lab_vms:&state_running` ne matche personne. Ansible sort alors en `rc=0` sur un `skipping: no hosts matched` : **un échec parfaitement silencieux**.

## 📚 Exercice 2 : lister les VMs

```bash
ansible-inventory -i inventory/01-libvirt.yml --graph 2>/dev/null
```

Vous voyez **toutes les VMs** du système : celles du lab plus toutes les autres (vos VMs personnelles, celles d'autres formations…). C'est le comportement attendu du plugin : il interroge libvirt, libvirt retourne tout.

```bash
ansible-inventory -i inventory/ --graph lab_vms 2>/dev/null
```

Le groupe `lab_vms` ne contient que les **4 VMs du lab** (filtre Jinja) :

```text
@lab_vms:
  |--control-node.lab
  |--db1.lab
  |--web1.lab
  |--web2.lab
```

C'est **le** point qui rend ce lab sûr : `lab_vms` est une **liste blanche explicite**. Un playbook qui ciblerait `all` irait écrire sur vos machines personnelles.

## 📚 Exercice 3 : inspecter les variables d'une VM

```bash
ansible-inventory -i inventory/ --host web1.lab 2>/dev/null | head -20
```

Le plugin retourne des facts sur chaque VM :

- **`info`** : l'état (`info.state` → `running`/`shutoff`), la mémoire, les vCPU, le temps CPU.
- **`xml_desc`** : la config XML libvirt complète (réseau, disques, UUID).
- **`guest_info`** et **`interface_addresses`** : CPU, OS, IP… **si l'agent QEMU est installé**. Ici, une erreur.

Vous pouvez les utiliser dans des conditionnels `when:`, des `groups:` ou des templates.

## 📚 Exercice 4 : ajouter les paramètres SSH (et comprendre la précédence)

Le plugin ne sait **pas comment se connecter en SSH**. Pire, il impose son propre mode de connexion :

```bash
ansible-inventory -i inventory/01-libvirt.yml --host web1.lab 2>/dev/null | grep ansible_connection
```

```json
"ansible_connection": "community.libvirt.libvirt_qemu",
```

Le plugin **force `ansible_connection: community.libvirt.libvirt_qemu`** sur chaque hôte : il veut passer par l'API libvirt et l'agent QEMU. Comme l'agent n'est pas là, il faut repasser en SSH classique. C'est ici que la **précédence des variables** décide de tout.

Rappel de l'ordre Ansible (du plus faible au plus fort) :

| Rang | Source |
| --- | --- |
| 5 | variables de **groupe** d'inventaire (`group_vars/`) |
| 7 | variables d'**hôte** posées par l'**inventaire** (← le plugin est ici) |
| 8 | variables d'**hôte** en fichier (`host_vars/`) |

Conséquence directe, et c'est **la** leçon du lab :

- `ansible_connection` doit être posé dans **`host_vars/`** (rang 8) pour battre le plugin (rang 7). Dans `group_vars/` (rang 5), il **perdrait**, sans un mot d'avertissement.
- Tout le reste (`ansible_user`, la clé, le `ssh_config`) n'est posé par personne d'autre : le **groupe** suffit, et évite de répéter quatre fois les mêmes lignes.

`inventory/host_vars/web1.lab.yml` ne contient donc qu'une ligne utile :

```yaml
---
ansible_connection: ssh
```

Et `inventory/group_vars/lab_vms.yml` porte le reste :

```yaml
---
ansible_user: ansible
ansible_ssh_common_args: >-
  -F {{ lookup('env', 'HOME') }}/.cache/dsoxlab/ansible-training/ssh_config
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
ansible_ssh_private_key_file: "{{ inventory_dir }}/../../../../ssh/id_ed25519"
ansible_python_interpreter: /usr/bin/python3.9
```

🔍 **Observation critique** : il n'y a **aucun `ansible_host`**, donc **aucune IP**. Ansible se connecte au nom `web1.lab`, et c'est **OpenSSH** qui le résout via le `ssh_config` généré par dsoxlab :

```text
Host web1.lab
  HostName 10.10.20.12
  User ansible
  IdentityFile .../ssh/id_ed25519
```

Le nom du domaine libvirt est **aussi** le nom du bloc `Host` : ce que remonte le plugin se connecte donc sans aucune table de traduction. Coder les IP ici les rendrait fausses au premier `dsoxlab provision`.

## 📚 Exercice 5 : combiner les deux inventaires

```bash
ansible-inventory -i inventory/ --graph 2>/dev/null | head -20
```

Ansible lit **tout le dossier** `inventory/` (les `*.yml` par ordre alphabétique, plus `group_vars/` et `host_vars/`) et fusionne. Résultat : la **liste dynamique** depuis libvirt, plus les **paramètres SSH** depuis le statique.

```bash
ansible web1.lab -i inventory/ -m ansible.builtin.ping
```

Sortie :

```text
web1.lab | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

🔍 **Observation** : Ansible utilise SSH (grâce à l'override de `host_vars/`) et l'adresse du `ssh_config`, mais c'est le plugin libvirt qui a ajouté `web1.lab` à l'inventaire au départ.

## 📚 Exercice 6 : démontrer le côté dynamique

C'est ici que la **magie** opère. L'inventaire reflète l'état **au moment du run**, sans cache par défaut :

```bash
ansible-inventory -i inventory/ --graph state_running 2>/dev/null   # web2.lab est là
virsh -c qemu:///system shutdown web2.lab
ansible-inventory -i inventory/ --graph state_running 2>/dev/null   # web2.lab a disparu
ansible-inventory -i inventory/ --graph state_shutoff 2>/dev/null   # il est ici
```

Sans avoir touché une ligne de `01-libvirt.yml`, la VM a changé de groupe. Rétablissez l'état initial :

```bash
virsh -c qemu:///system start web2.lab
```

🔍 **Observation** : c'est la **promesse** des inventaires dynamiques. Toute VM créée par Terraform, Packer, `virt-install` ou OpenStack est **automatiquement** disponible pour Ansible, et toute VM éteinte sort d'elle-même des cibles. Zéro maintenance d'inventaire.

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court : `ansible-lint --profile
  production` le vérifie.
- **Jamais d'IP en dur** : la connexion passe par le `ssh_config` généré par
  dsoxlab. C'est vrai dans tous les labs de cette formation.
- **Reset isolé** : `dsoxlab clean inventaires-dynamique-kvm` désinstalle
  proprement ce que la solution a posé, pour rejouer le scénario.

## 🤔 Questions de réflexion

1. Le plugin libvirt retourne **toutes** les VMs de l'hyperviseur. Si vous avez 30 VMs personnelles non gérées par Ansible, comment les **exclure** proprement ?

2. Pourquoi `ansible_connection: ssh` doit-il être dans `host_vars/` et non dans `group_vars/` ? Que se passe-t-il exactement si vous le déplacez ?

3. Comment valider qu'un **playbook tourne uniquement sur les VMs running** ?

4. Le plugin détecte-t-il un changement d'IP automatiquement ? Et si la VM n'a pas l'agent QEMU ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande d'écrire un playbook qui pose un fichier marqueur **uniquement sur les VMs running du lab** (`lab_vms:&state_running`). Tests automatisés via `pytest+testinfra` :

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Filtrer sur le réseau plutôt que sur une liste de noms** : la liste blanche
  de `lab_vms` reste une liste à maintenir. Les 4 VMs du lab ont ceci de commun
  qu'elles sont sur le réseau libvirt `lab-ansible`, et cette information est
  dans `xml_desc`. Un groupe `lab_vms: "'lab-ansible' in xml_desc"` survivrait à
  l'ajout d'une 5e VM. Peser le pour et le contre : moins de maintenance, mais
  un filtre par sous-chaîne XML est moins lisible et moins prévisible qu'une
  liste explicite, ce qui compte quand un faux positif écrit sur une machine
  personnelle.
- **Ajouter un `compose:` Jinja** pour calculer `ansible_host` depuis
  `interface_addresses` (utile **seulement** si l'agent QEMU est installé).
- **Installer `qemu-guest-agent`** dans une VM, puis comparer `guest_info` avant
  et après : c'est la différence entre un plugin qui devine et un plugin qui sait.
- **Cache plugin** (`ansible.cfg`) pour éviter de réinterroger libvirt à chaque
  commande, et mesurer ce qu'on perd en fraîcheur.
- **Comparer avec Proxmox** : `community.general.proxmox` retourne VM + IP en un
  seul appel d'API.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `challenge/solution.yml`
avec **`ansible-lint`** :

```bash
ansible-lint labs/inventaires/dynamique-kvm/challenge/solution.yml
ansible-lint --profile production labs/inventaires/dynamique-kvm/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
