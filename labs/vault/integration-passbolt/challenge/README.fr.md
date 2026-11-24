# Le tableur partagé des mots de passe doit disparaître

## La situation

Vos playbooks tirent leurs secrets d'infrastructure d'un vrai serveur dédié. Les
humains, non. Les comptes SaaS, les clés d'API tierces, les passphrases de
certificats et le login d'administration que tout le monde utilise vivent dans un
tableur sur un partage réseau, parce que l'équipe a besoin de les lire avec ses
yeux, pas seulement depuis un playbook. Ces secrets méritent un toit qui serve les
deux : une interface web qu'un humain utilisera vraiment, et une interface
qu'Ansible sait interroger.

Votre mission, depuis le répertoire du projet :

1. Monter une instance **Passbolt locale** avec sa base de données, puis créer le
   compte d'administration et la **clé OpenPGP** qui vous identifie auprès d'elle.
2. Faire récupérer un secret par un playbook via la collection dédiée, en vous
   authentifiant par votre clé privée et sa passphrase, avec **aucune valeur
   secrète en dur** dans le YAML.
3. Museler les tâches sensibles pour que le secret n'apparaisse ni dans la sortie
   ni dans les journaux, quelle que soit la verbosité.
4. Positionner l'outil face à un serveur de type HashiCorp : son modèle
   d'identité, c'est une clé par humain, pas un token par machine. Dire quels
   secrets vont où.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/integration-passbolt/

## 🎯 Challenge — Passbolt : récupérer un secret, et le prouver

### ✅ Objectif

Écrire `challenge/solution.yml` : un playbook qui s'authentifie auprès de
votre Passbolt local avec **votre clé OpenPGP**, récupère le secret
**`lab83-demo`** via la collection `anatomicjc.passbolt`, et dépose une
preuve **dérivée** (la longueur du mot de passe, jamais sa valeur) dans un
fichier local.

⚠️ **Ce lab a une part manuelle irréductible.** Passbolt authentifie des
humains par clé OpenPGP : la création du compte admin, la génération de la
clé et la création du secret passent par l'interface web. Les tests le
savent : tant que le serveur ne répond pas, que la clé n'est pas exportée
ou que la passphrase n'est pas dans l'environnement, ils se mettent en
**`skip` avec la marche à suivre**. Ils ne passent jamais « à vide ».

### 🔧 Pré-requis (les étapes manuelles, une seule fois)

```bash
cd labs/vault/integration-passbolt/
dsoxlab run vault-integration-passbolt   # Passbolt CE + MariaDB, admin créé
```

Puis, via l'interface (`https://localhost:8443`, certificat self-signed) :

1. Terminer l'inscription admin avec le lien affiché par `register_user`.
2. Générer la clé OpenPGP du compte pendant l'inscription.
3. Créer une ressource nommée **`lab83-demo`** avec un mot de passe.
4. Exporter la clé privée du compte dans
   `labs/vault/integration-passbolt/.passbolt-private.asc` (mode `0600`,
   le fichier est ignoré par Git).

Enfin, côté shell :

```bash
ansible-galaxy collection install -r $ANSIBLE_TRAINING/requirements.yml
mise install   # py-passbolt voyage avec ansible-core
export PASSBOLT_PASSPHRASE='<votre passphrase>'
```

### 🧩 Contrat attendu

| Élément | Attente |
| --- | --- |
| Cible | `localhost`, `gather_facts: false`, sans `become` |
| URL | env `PASSBOLT_URL`, défaut `https://localhost:8443`, `verify_ssl` désactivé (dev, self-signed) |
| Clé privée | lue depuis `.passbolt-private.asc` du lab (lookup `file`) |
| Passphrase | env `PASSBOLT_PASSPHRASE`, jamais dans le YAML |
| Secret | ressource `lab83-demo`, via la lookup `anatomicjc.passbolt.passbolt` |
| Preuve | `/tmp/lab83-passbolt-lookup.txt`, mode `0600`, contenu `Secret length: <n>` |
| Silence | `no_log: true` sur toute tâche qui manipule le secret |

### 🧩 Squelette

```yaml
---
- name: Récupérer un secret Passbolt et en déposer la preuve
  hosts: ???
  gather_facts: false
  become: false                        # ansible.cfg l'active globalement : pas ici

  vars:
    ansible_ssh_private_key_file: null   # localhost n'a pas besoin de la clé SSH du lab
    passbolt_uri: "{{ lookup('env', 'PASSBOLT_URL') | default('???', true) }}"
    passbolt_private_key: "{{ lookup('file', '???') }}"
    passbolt_passphrase: "{{ lookup('env', '???') }}"

  tasks:
    - name: Récupérer le secret lab83-demo
      ansible.builtin.set_fact:
        demo_secret: "{{ lookup('anatomicjc.passbolt.passbolt',
                                '???',
                                uri=passbolt_uri,
                                private_key=passbolt_private_key,
                                passphrase=passbolt_passphrase,
                                verify_ssl=false).password }}"
      no_log: ???

    - name: Déposer la preuve (longueur, jamais la valeur)
      ansible.builtin.copy:
        dest: ???
        content: "Secret length: {{ ??? }}\n"
        mode: ???
```

> 💡 **Pièges** :
>
> - **La clé privée est un fichier, pas une variable en dur** : un YAML qui
>   embarque un bloc PGP est un YAML qui finit dans Git.
> - **`no_log: true`** sur le `set_fact` : sans lui, `-v` affiche le secret.
> - **Chemin de la clé** : `solution.yml` est joué depuis la racine du repo
>   par pytest ; utilisez un chemin relatif à `playbook_dir` ou absolu.
> - **`verify_ssl=false`** uniquement parce que le certificat de dev est
>   self-signed. En production, jamais.
> - **`ansible_ssh_private_key_file: null`** : l'inventaire du lab définit
>   la clé SSH via `inventory_dir`, que l'implicite `localhost` ne sait pas
>   résoudre. Sans cette neutralisation, le play plante avant sa 1ère tâche.

### 🚀 Lancement

```bash
export PASSBOLT_PASSPHRASE='<votre passphrase>'
ansible-playbook labs/vault/integration-passbolt/challenge/solution.yml
cat /tmp/lab83-passbolt-lookup.txt
```

### 🧪 Validation

```bash
pytest -v labs/vault/integration-passbolt/challenge/tests/
```

Serveur joignable + clé + passphrase présentes : les tests rejouent votre
playbook et vérifient la preuve sur le système (existence, mode `0600`,
longueur cohérente, aucun secret en clair dans le YAML). Sinon : `skip`
explicite, jamais un faux vert.

### 🧹 Reset

```bash
dsoxlab clean vault-integration-passbolt
rm -f /tmp/lab83-passbolt-lookup.txt
```

### 💡 Pour aller plus loin

- **Passbolt vs HashiCorp Vault** : Passbolt cible les **équipes humaines**
  (UI riche, partage par groupe), Vault cible le **runtime** (secrets
  dynamiques pour services). Beaucoup d'organisations utilisent les deux.
- **Compte bot** : pour automatiser sans MFA, créez un compte dédié avec sa
  propre clé, aux droits minimaux.
- **Backup de la clé OpenPGP** : sans elle, vos secrets sont perdus.
