# Inventaire statique : écrire ses groupes de zéro

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -i inventory/hosts.yml -m ansible.builtin.ping
> ```

## 🧠 Rappel

🔗 [**Inventaire statique au format YAML**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/statiques-yaml/)
· [Version INI](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/statiques-ini/)
· [Vérifier son inventaire](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/verifier-inventaire/)

L'inventaire est le **point de départ** de tout ce qu'Ansible fait. Sans lui,
aucun playbook ne sait sur quelles machines agir. Les autres labs de cette
section vous fournissaient un inventaire déjà écrit ; ici, vous le construisez
vous-même. C'est l'objectif officiel EX294 « Create static host inventory
files », et la première tâche de l'examen blanc.

### Ce qu'un inventaire statique déclare

Un inventaire statique est un simple fichier (YAML ou INI) qui répond à trois
questions :

1. **Quels hôtes ?** La liste des machines gérées.
2. **Regroupés comment ?** Des **groupes** (`webservers`, `dbservers`), et des
   **groupes parents** qui agrègent d'autres groupes via `children`.
3. **Avec quelles variables ?** Des **variables de groupe** qui s'appliquent à
   tous les hôtes d'un groupe, et sont héritées par les groupes enfants.

### Format YAML

C'est le format moderne, celui qu'utilise tout ce dépôt. Sa structure suit
toujours le même squelette :

```yaml
---
all:
  vars:                     # variables communes à TOUS les hôtes
    ansible_user: ansible
  children:                 # les groupes vivent sous `children`
    webservers:
      hosts:
        web1.lab:
        web2.lab:
      vars:                 # variable propre au groupe webservers
        web_role: frontend
    dbservers:
      hosts:
        db1.lab:
    datacenter:             # groupe PARENT : aucun hôte en propre
      children:             # il agrège deux groupes
        webservers:
        dbservers:
      vars:                 # héritée par web1, web2 ET db1
        site: paris
```

Points de vigilance :

- Un hôte se déclare `web1.lab:` (deux-points final), **pas** `- web1.lab`. La
  forme liste est réservée à d'autres contextes.
- Un **groupe parent** (`datacenter`) ne contient pas de `hosts:`, il contient
  des `children:`. Ses variables descendent vers les hôtes de ses enfants.
- Les **variables de groupe** peuvent vivre en ligne sous `vars:` (comme
  ci-dessus) ou dans un dossier `group_vars/<nom-du-groupe>.yml` à côté de
  l'inventaire. Les deux sont équivalents ; ce lab utilise la forme en ligne.

### Le même inventaire au format INI

Le format INI reste très courant, y compris à l'examen. Le même contenu s'écrit :

```ini
[webservers]
web1.lab
web2.lab

[dbservers]
db1.lab

[datacenter:children]
webservers
dbservers

[webservers:vars]
web_role=frontend

[datacenter:vars]
site=paris
```

Un groupe parent se déclare `[<parent>:children]`, les variables de groupe
`[<groupe>:vars]`. Ce lab exige le **YAML** (le standard du dépôt et de la
résolution SSH ci-dessous), mais savoir traduire de l'un à l'autre est attendu
à l'EX294.

### Pas d'IP en dur : la connexion passe par le ssh_config

Les adresses des VMs sont attribuées dynamiquement par Terraform : les figer
dans l'inventaire les rendrait fausses au premier reprovisionnement. On délègue
donc la résolution au `ssh_config` généré par dsoxlab, en le passant à Ansible
par `ansible_ssh_common_args`. Le compte de connexion est **`ansible`**, le
compte de service que dsoxlab provisionne sur les VMs (clé SSH et sudo sans mot
de passe) ; `student` reste le compte humain sur le control node. Ce bloc de
connexion vous est fourni dans le challenge : votre travail pédagogique porte
sur les groupes et les variables.

### Prouver son inventaire, ne pas le supposer

Un inventaire « qui a l'air correct » ne suffit pas. On demande à Ansible ce
qu'il en résout :

```bash
# La structure résolue : groupes, enfants, hôtes.
ansible-inventory -i inventory/hosts.yml --graph
ansible-inventory -i inventory/hosts.yml --list

# Les variables effectives d'un hôte (group_vars fusionnées).
ansible-inventory -i inventory/hosts.yml --host web1.lab

# La preuve ultime : joindre exactement les bons hôtes.
ansible webservers -i inventory/hosts.yml -m ansible.builtin.ping   # web1 + web2
ansible dbservers  -i inventory/hosts.yml -m ansible.builtin.ping   # db1
ansible datacenter -i inventory/hosts.yml -m ansible.builtin.ping   # les 3
```

Si `webservers` joint db1, ou si `datacenter` ne joint que deux hôtes sur trois,
l'inventaire est faux, même s'il se lit bien. C'est exactement ce que vérifient
les tests de ce lab.

Rendez-vous dans `challenge/README.md` pour l'énoncé.
