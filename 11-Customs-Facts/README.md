# 11 – Utilisation des Custom Facts Ansible

Bienvenue dans le onzième TP de la formation Ansible ! Ce TP vous apprendra à
**définir et exploiter des faits personnalisés (custom facts)** Ansible.
Ces faits permettent d'adapter dynamiquement les playbooks aux caractéristiques
des hôtes.

## 🧠 Lecture recommandée

Avant de commencer, je vous recommande de lire cette section du guide : 🔗
[Ansible - Custom
Facts](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/customs-facts/)

Vous y apprendrez :

* Comment définir vos propres facts personnalisés dans `/etc/ansible/facts.d/`
* Les formats utilisables (INI et JSON)
* Les bonnes pratiques de nommage et de gestion

---

## 🌟 Objectifs du TP

1. Créer un fichier de facts personnalisés au format INI et JSON
2. Le déployer sur un hôte cible avec Ansible
3. Utiliser les facts personnalisés dans un playbook
4. Appliquer des conditions `when` en fonction de ces facts
5. Simuler un provisionnement avec Packer ou Terraform (fichier de facts
   pré-installé)

---

## ⚙️ Étapes du TP

### Étape 0 : Prérequis

Assurez-vous de disposer d'une machine cible Ansible. Pour simplifier, utilisez
un conteneur Incus avec Ubuntu :

```bash
incus launch images:ubuntu/24.04/cloud myhost --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
```

### Étape 1 : Créer un custom fact INI

Créez un fichier `preference.fact` dans le dossier `files` avec le contenu
suivant :

```ini
[general]
function=War
family=Destruction
```

Créez un playbook `copie-facts.yml` pour copier ce fichier dans `/etc/ansible/facts.d/` sur la
cible :

```yaml
- name: Déploiement du custom fact INI
  hosts: all
  become: true
  tasks:
    - name: Créer le dossier facts.d
      ansible.builtin.file:
        path: /etc/ansible/facts.d
        state: directory
        mode: '0755'

    - name: Copier le fichier de facts
      ansible.builtin.copy:
        src: preference.fact
        dest: /etc/ansible/facts.d/preference.fact
        mode: '0644'
```

Vérifiez ensuite avec :

```bash
ansible -m setup -a 'filter=ansible_local' all
```

Vous devriez voir ce résultat :

```json
myhost | SUCCESS => {
    "ansible_facts": {
        "ansible_local": {
            "preference": {
                "general": {
                    "family": "Destruction",
                    "function": "War"
                }
            }
        },
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false
}
```

Vous remarquez que le nom du fichier `preference.fact` est transformé en
`ansible_local.preference`, et la section `[general]` devient
`ansible_local.preference.general`.

---

### Étape 2 : Créer un custom fact JSON

Créez un fichier `infos.fact` avec le contenu suivant :

```json
{
  "general": {
    "environment": "staging",
    "role": "webserver"
  }
}
```

Déployez-le comme précédemment en modifiant le playbook et vérifiez que
`ansible_local.infos.general` est disponible comme suit :

```json
myhost | SUCCESS => {
    "ansible_facts": {
        "ansible_local": {
            "infos": {
                "general": {
                    "family": "Destruction",
                    "function": "War"
                }
            },
            "preference": {
                "general": {
                    "family": "Destruction",
                    "function": "War"
                }
            }
        },
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false
}
```

---

### Étape 3 : Utiliser les facts dans des conditions

Ajoutez une tâche dans un playbook avec :

```yaml
- name: Créer un fichier de test
  ansible.builtin.file:
    path: /tmp/test
    state: touch
  when: ansible_local.infos.general.family == "Destruction"
```

Exécutez le playbook et vérifiez que le fichier `/tmp/test` est créé
uniquement si le fact `family` est égal à `Destruction`.

## 🧪 Challenge à valider

Voir `challenge/README.md` pour la consigne du challenge final : Créer un
fichier `final.fact` avec une structure JSON contenant des champs `level: final`
et `passed: true`, puis vérifier leur existence avec un test `pytest` +
`testinfra`.

---

## ✅ Compétences acquises

* Création de facts personnalisés en INI et JSON
* Déploiement de fichiers sur un hôte cible avec Ansible
* Utilisation de `ansible_local.*` dans les conditions `when`
* Intégration avec des outils d’infrastructure comme Packer ou Terraform

---

🚀 Maintenant il ne vous reste plus qu'à mettre en oeuvre ce concept. Par
exemple, créer des facts lors du provisionnement d'une machine avec Packer ou
Terraform, pour les utiliser ensuite dans vos playbooks en fonction de
vos besoins.
