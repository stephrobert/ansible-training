# Prise en main de la CLI — Tour des 8 commandes Ansible

Bienvenue dans ce lab de découverte des commandes ! 🚀

---

## 🧠 Rappel et lecture recommandée

🔗 [**Prise en main de la CLI Ansible : les 8 commandes du quotidien**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/prise-en-main-cli/)

Cette page détaille chaque commande avec sa syntaxe et un exemple :

| Commande | Rôle |
|---|---|
| **`ansible`** | Exécution **ad-hoc** d'un module unique sur un pattern d'hôtes |
| **`ansible-playbook`** | Exécution d'un playbook YAML |
| **`ansible-doc`** | Documentation des modules (hors-ligne) |
| **`ansible-config`** | Inspection de la configuration Ansible |
| **`ansible-inventory`** | Validation et debug d'inventaire |
| **`ansible-galaxy`** | Installation de **collections** et **rôles** |
| **`ansible-vault`** | Chiffrement de fichiers de variables sensibles |
| **`ansible-lint`** | Détection d'anti-patterns dans un playbook |

---

## 🌟 Objectif du TP

À la fin :

1. Connaître par cœur les 8 commandes et leur rôle
2. Savoir trouver la documentation d'un module sans Internet
3. Lister les modules d'une collection et inspecter votre inventaire
4. Lint un playbook avec `ansible-lint`

---

## ⚙️ Exercices pratiques

### Exercice 1 — `ansible` : ad-hoc

```bash
ansible all -m ansible.builtin.ping
```

4 `pong` attendus. Le module `ping` ouvre une connexion SSH + lance un mini-script Python — c'est un **test bout-en-bout** de la chaîne Ansible.

### Exercice 2 — `ansible-playbook` : exécuter un playbook

```bash
ansible-playbook labs/000-prepare-managed-nodes/playbook.yml
```

Le playbook de préparation tourne. Au premier run, `changed > 0` ; au second, `changed=0` (idempotence).

### Exercice 3 — `ansible-doc` : documentation hors-ligne

```bash
ansible-doc ansible.builtin.dnf | less
```

Affiche la doc complète : description, paramètres, valeurs par défaut, exemples, options de retour.

Pour lister tous les modules :

```bash
ansible-doc -l | head -20
```

Filtrer par mot-clé :

```bash
ansible-doc -l | grep -i firewall
```

### Exercice 4 — `ansible-config` : configuration active

```bash
ansible-config dump --only-changed
```

Liste les paramètres qui diffèrent des défauts, avec leur **source** (env var, fichier, défaut). Indispensable quand un comportement vous surprend.

### Exercice 5 — `ansible-inventory` : valider l'inventaire

```bash
ansible-inventory --graph
```

Vue arborescente des groupes et hôtes. Attendu : `control`, `webservers`, `dbservers`, `rhce_lab` avec les bons hôtes.

```bash
ansible-inventory --host web1.lab
```

Variables résolues pour un hôte précis (héritage des `group_vars`).

### Exercice 6 — `ansible-galaxy` : installer une collection

Liste des collections déjà installées :

```bash
ansible-galaxy collection list
```

Pour installer une nouvelle collection (déjà fait via `requirements.yml` du repo) :

```bash
ansible-galaxy collection install community.docker
```

### Exercice 7 — `ansible-vault` : chiffrer un secret

Créez un fichier de test, chiffrez-le, déchiffrez-le :

```bash
echo "api_key: secret-ABC123" > /tmp/secrets.yml
ansible-vault encrypt /tmp/secrets.yml         # demande un mot de passe
cat /tmp/secrets.yml                            # contenu chiffré (ANSIBLE_VAULT;1.1;AES256...)
ansible-vault view /tmp/secrets.yml             # affiche en clair (mot de passe demandé)
ansible-vault decrypt /tmp/secrets.yml          # remet en clair sur disque
rm /tmp/secrets.yml
```

### Exercice 8 — `ansible-lint` : qualité du code

```bash
ansible-lint labs/000-prepare-managed-nodes/playbook.yml
```

Si le playbook est conforme, sortie vide. Sinon, ansible-lint pointe les anti-patterns : tâche sans `name:`, FQCN manquant, modules dépréciés.

Bonus :

```bash
ansible-lint --profile production labs/000-prepare-managed-nodes/
```

Profile `production` = le plus strict. À utiliser pour audit avant déploiement réel.

---

## 🚀 Pour aller plus loin

- Lancez `ansible-navigator run labs/000-prepare-managed-nodes/playbook.yml` (si EE installé) et observez l'interface texte interactive.
- Construisez votre propre Execution Environment avec `ansible-builder` (cf. lab 02 « Pour aller plus loin »).

---

Bonne pratique ! 🧠
