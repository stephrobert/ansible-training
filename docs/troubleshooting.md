# Dépannage du lab Ansible

## `make bootstrap` — outils Python manquants

### `mise` introuvable

Le bootstrap exige `mise`. Installation officielle :

```bash
curl https://mise.run | sh
echo 'eval "$(mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
```

### `pipx` introuvable

```bash
sudo dnf install -y pipx        # Fedora / RHEL / AlmaLinux
sudo apt-get install -y pipx    # Debian / Ubuntu
pipx ensurepath
```

## `make provision` — VMs ne démarrent pas

### `libvirtd` inactif

```bash
sudo systemctl enable --now libvirtd
sudo usermod -aG libvirt,kvm "${USER}"
# Se reconnecter pour prendre en compte les groupes
```

### Réseau `lab-ansible` qui n'existe pas

Recréer manuellement :

```bash
virsh net-list --all       # Vérifier l'absence
sudo virsh net-define <(cat <<EOF
<network>
  <name>lab-ansible</name>
  <forward mode='nat'/>
  <bridge name='virbr-ansible' stp='on' delay='0'/>
  <ip address='10.10.20.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='10.10.20.100' end='10.10.20.200'/>
    </dhcp>
  </ip>
</network>
EOF
)
sudo virsh net-start lab-ansible
sudo virsh net-autostart lab-ansible
```

### Image AlmaLinux 10 corrompue ou incomplète

```bash
sudo rm /var/lib/libvirt/images/AlmaLinux-10-GenericCloud-latest.x86_64.qcow2
make provision
```

## `make verify-conn` — `Connection timed out during banner exchange`

### Symptôme

`ansible all -m ping` retourne `UNREACHABLE` sur les 4 hôtes alors que `nmap -p 22 10.10.20.10 -Pn` montre le port 22 ouvert et que les VMs sont bien `running`.

### Cause typique : `~/.ssh/config` qui détourne `10.*`

Beaucoup de postes ont une règle de type :

```sshconfig
Host 10.*
    ProxyJump bastion.example.com
    User outscale
    IdentityFile ~/.ssh/id_ed25519
```

pour atteindre des VMs cloud via un bastion. Cette règle matche aussi `10.10.20.0/24` du lab et redirige tout SSH vers le bastion — qui ne connaît pas le lab.

### Fix

Créer un fichier `~/.ssh/config.d/lab-ansible.conf` qui surcharge la règle générique pour la plage du lab :

```sshconfig
Host 10.10.20.*
    User ansible
    IdentityFile ~/Projets/lab-ansible/ssh/id_ed25519
    ProxyJump none
    ProxyCommand none
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

`ssh` applique la directive la plus spécifique — `10.10.20.*` est plus précise que `10.*`, donc le ProxyJump est désactivé pour le lab uniquement.

### Vérifier que le fix marche

```bash
ssh -vvv ansible@10.10.20.10 true 2>&1 | grep "Connecting to"
# Attendu : Connecting to 10.10.20.10 [10.10.20.10] port 22.
# (et pas l'IP du bastion)
```

## `make verify-conn` — Ansible ne ping pas (autres causes)

### Cloud-init pas terminé

Au premier provisionnement, cloud-init prend ~2-3 minutes (paquets, reboot). Patienter et relancer `make verify-conn`. Pour observer :

```bash
ssh -i ssh/id_ed25519 ansible@10.10.20.10 'sudo cloud-init status --wait'
```

### Clé SSH refusée

Vérifier que la clé publique a bien été injectée :

```bash
ssh -i ssh/id_ed25519 -o StrictHostKeyChecking=no ansible@10.10.20.10 'cat ~/.ssh/authorized_keys'
```

Si vide, la VM a été provisionnée avant la création de la clé. Rejouer :

```bash
make destroy
make bootstrap   # créera la clé si absente
make provision
```

### Python introuvable côté managed nodes

L'inventaire pointe vers `/usr/bin/python3.12`. Vérifier sur la VM :

```bash
ssh -i ssh/id_ed25519 ansible@10.10.20.21 'ls -la /usr/bin/python3*'
```

Si python3.12 n'existe pas mais python3 oui, ajuster `inventory/hosts.yml` :

```yaml
ansible_python_interpreter: /usr/bin/python3
```

## `make test-all` retourne vert mais labs/ est vide

C'est l'état attendu en phase 0 : le script `scripts/test-all.sh` détecte
qu'aucun `Makefile` unitaire n'est présent et sort en succès. Les labs unitaires
sont créés au fur et à mesure que les pages de la formation sont rédigées
(phases 1+).

## Snapshots libvirt qui ne se restaurent pas

Les snapshots avec backing file QCOW2 fonctionnent uniquement sur le disque
parent. Si tu as utilisé `virsh snapshot-create-as` sur un disque créé avec
`-b ALMA_BASE`, vérifier :

```bash
qemu-img info /var/lib/libvirt/images/control-node.qcow2
# La sortie doit afficher "backing file: AlmaLinux-10-GenericCloud..."
```

Si ce backing manque, le snapshot ne fonctionnera pas. Recréer la VM proprement :

```bash
./infra/virt-install/destroy.sh
./infra/virt-install/provision.sh
```
