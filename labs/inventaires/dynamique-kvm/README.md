# Lab 57 — Inventaire dynamique KVM avec community.libvirt.libvirt

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

**Limite** : le plugin retourne le **nom** de chaque VM, mais **pas son IP** (libvirt ne la connaît qu'après que la VM ait demandé une IP DHCP). Pour la connexion SSH, on combine donc le plugin avec un **fichier statique** qui mappe `nom → IP`.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Configurer** le plugin `community.libvirt.libvirt` avec `qemu:///system`.
2. **Créer des groupes logiques** via `groups:` Jinja (`webservers`, `dbservers`).
3. **Filtrer** les VMs par état (`state: running`) avec `keyed_groups`.
4. **Combiner** le plugin avec un fichier statique pour ajouter les IPs et les paramètres SSH.
5. **Démontrer** qu'une nouvelle VM créée via `virsh` apparaît automatiquement dans l'inventaire.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/inventaires/dynamique-kvm
```

## ⚙️ Arborescence cible

```text
labs/inventaires/dynamique-kvm/
├── README.md           ← ce fichier
├── inventory/
│   ├── 01-libvirt.yml  ← plugin community.libvirt.libvirt
│   └── 02-overrides.yml ← ajout IPs et paramètres SSH (statique)
└── challenge/
    ├── README.md
    ├── solution.yml    ← playbook qui ping toutes les VMs running
    └── tests/
        └── test_dynamic.py
```

## 📚 Exercice 1 — Configurer le plugin libvirt

Le fichier `inventory/01-libvirt.yml` :

```yaml
---
plugin: community.libvirt.libvirt
uri: qemu:///system
inventory_hostname: name

groups:
  lab_vms: inventory_hostname in ['control-node', 'web1', 'web2', 'db1']
  webservers: inventory_hostname in ['web1', 'web2']
  dbservers: inventory_hostname == 'db1'
  control: inventory_hostname == 'control-node'

keyed_groups:
  - prefix: state
    key: state
```

🔍 **Observation** :

- **`plugin:`** au top-level dit à Ansible que ce fichier est une config de plugin (pas un inventaire YAML classique).
- **`uri:`** indique le socket libvirt — `qemu:///system` pour KVM root, `qemu:///session` pour user-mode.
- **`groups:`** crée des groupes logiques basés sur des conditions Jinja évaluées **par VM**.
- **`keyed_groups:`** crée un groupe par **valeur** d'une variable (ici `state` → `state_running`, `state_shut_off`).

## 📚 Exercice 2 — Lister les VMs

```bash
ansible-inventory -i inventory/01-libvirt.yml --graph 2>/dev/null
```

Vous voyez **toutes les VMs** du système — celles du lab plus toutes les autres. C'est le comportement attendu du plugin : il interroge libvirt, libvirt retourne tout.

```bash
ansible-inventory -i inventory/01-libvirt.yml --graph 2>/dev/null | grep -A 5 "@lab_vms:"
```

Le groupe `lab_vms` contient les **4 VMs du lab** uniquement (filtre Jinja).

## 📚 Exercice 3 — Inspecter les variables d'une VM

```bash
ansible-inventory -i inventory/01-libvirt.yml --host web1 2>/dev/null | grep -E "state|guest_info" | head -5
```

Le plugin retourne **plein de facts** sur chaque VM : `state` (running/shut_off), `guest_info` (CPU, mémoire, OS si l'agent QEMU est installé), `xml_desc` (la config XML libvirt complète). Vous pouvez les utiliser dans des conditionnels `when:` ou des templates.

## 📚 Exercice 4 — Ajouter les paramètres SSH

Le plugin libvirt ne sait **pas comment se connecter en SSH** à une VM. Il faut compléter avec un fichier statique. Voir `inventory/02-overrides.yml` :

```yaml
all:
  vars:
    ansible_user: ansible
    ansible_ssh_private_key_file: "{{ inventory_dir }}/../../../ssh/id_ed25519"
    ansible_python_interpreter: /usr/bin/python3.12
  hosts:
    web1:
      ansible_host: 10.10.20.21
      ansible_connection: ssh   # override de libvirt_qemu
    web2:
      ansible_host: 10.10.20.22
      ansible_connection: ssh
    db1:
      ansible_host: 10.10.20.31
      ansible_connection: ssh
    control-node:
      ansible_host: 10.10.20.10
      ansible_connection: ssh
```

🔍 **Observation critique** : le plugin libvirt **force `ansible_connection: community.libvirt.libvirt_qemu`** (connexion via API libvirt, pas SSH). Pour utiliser SSH classique, il faut **override `ansible_connection: ssh` au niveau host** (pas dans `all.vars` — le plugin gagne sinon par précédence).

## 📚 Exercice 5 — Combiner les deux inventaires

```bash
ansible-inventory -i inventory/ --graph 2>/dev/null | head -20
```

Ansible lit **tous les fichiers** du dossier `inventory/` (alphabétiquement) et fusionne. Résultat : on a la **liste dynamique** depuis libvirt + les **paramètres SSH** depuis le statique.

```bash
ansible web1 -i inventory/ -m ansible.builtin.ping
```

Sortie :

```text
web1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

🔍 **Observation** : Ansible utilise SSH (grâce à l'override) avec l'IP du fichier statique, mais c'est le plugin libvirt qui a ajouté `web1` à l'inventaire au départ.

## 📚 Exercice 6 — Démontrer le côté dynamique

C'est ici que la **magie** opère. Créez une nouvelle VM (manuellement, ou via Terraform, ou via un autre playbook). Sans toucher à `inventory/01-libvirt.yml`, relancez :

```bash
# Démo simple : démarrer une VM existante qui était arrêtée
virsh start argocd-cp1   # remplacer par une de vos VMs en shut_off

ansible-inventory -i inventory/01-libvirt.yml --graph 2>/dev/null | grep argocd-cp1
```

**La VM apparaît immédiatement** dans `state_running` — pas besoin de modifier l'inventaire.

```bash
virsh shutdown argocd-cp1   # rétablir l'état initial après la démo
```

🔍 **Observation** : c'est la **promesse** des inventaires dynamiques. Toute nouvelle VM (créée par Terraform, Packer, virt-install, OpenStack, etc.) est **automatiquement** disponible pour Ansible — zéro maintenance d'inventaire.

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible les VMs libvirt du réseau lab-ansible ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Le plugin libvirt retourne **toutes** les VMs de l'host. Si vous avez 30 VMs personnelles non gérées par Ansible, comment les **exclure** proprement ?

2. Pourquoi mettre `ansible_connection: ssh` au niveau **host** et non `all.vars` ?

3. Comment valider qu'un **playbook tourne uniquement sur les VMs running** ?

4. Si vous changez l'IP d'une VM, le plugin le détecte-t-il automatiquement ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande d'écrire un playbook qui pose un fichier marqueur **uniquement sur les VMs running du lab** (`lab_vms:&state_running`). Tests automatisés via `pytest+testinfra` :

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Créer une nouvelle VM via virt-install + cloud-init**, puis vérifier qu'Ansible la voit immédiatement (scénario provisioning end-to-end).
- **Filtrer par état** via un wrapper script qui lit `ansible-inventory --list` et filtre sur `state == 'running'` — le plugin natif ne fournit pas de groupe `state_running` exploitable directement.
- **Ajouter un `compose:` Jinja** dans le plugin pour calculer dynamiquement des variables (par ex. `ansible_host` depuis `virsh domifaddr`).
- **Cache plugin** (`ansible.cfg`) pour éviter de re-interroger libvirt à chaque commande.
- **Comparer avec Proxmox** : `community.general.proxmox_kvm` retourne aussi VM + IP en une seule API call.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/inventaires/dynamique-kvm/lab.yml
ansible-lint labs/inventaires/dynamique-kvm/challenge/solution.yml
ansible-lint --profile production labs/inventaires/dynamique-kvm/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
