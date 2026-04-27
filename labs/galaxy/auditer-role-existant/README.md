# Lab 75 — Auditer un rôle Ansible avant adoption

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : Ansible installé. Pas besoin des VMs (lab purement local + lecture).

## 🧠 Rappel

🔗 [**Auditer un rôle Ansible tiers**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/auditer-role/)

Avant d'adopter un rôle Galaxy ou GitHub dans votre projet (et donc de
**l'exécuter avec `become: true`** sur vos serveurs production), passez-le
au crible d'une **checklist d'audit**. Les rôles tiers sont du **code
arbitraire** qui tournera root sur vos machines.

| Risque | Si pas audité |
| --- | --- |
| Maintenance | Rôle abandonné depuis 3 ans, breaking change Ansible 2.18 |
| Sécurité | Téléchargement HTTP non chiffré, secret hardcodé |
| Qualité | Pas d'idempotence, casse au 2e run |
| Compat | Targets RHEL 7 only, votre prod est RHEL 10 |

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Évaluer un rôle sur **6 axes** : mainteneur, qualité, sécurité, tests,
   compat, idempotence.
2. Lire le `meta/main.yml` pour identifier les **plateformes supportées**.
3. Détecter les **anti-patterns** classiques (FQCN absent, secrets hardcodés,
   `command:` sans `creates:`).
4. Calculer un **score d'audit** chiffré (9-10/10 = adopter).
5. **Décider** : adopter / forker / refuser.

## 🔧 Préparation

```bash
# Pour les exemples : installer un rôle Galaxy célèbre
ansible-galaxy role install geerlingguy.docker
ls ~/.ansible/roles/geerlingguy.docker/
```

## ⚙️ Arborescence

```text
labs/galaxy/auditer-role-existant/
├── README.md
├── Makefile
├── AUDIT_CHECKLIST.md       ← checklist livrée (à étudier)
└── roles/
    └── webserver/            ← rôle exemple à auditer
```

## 📚 Exercice 1 — Lire `AUDIT_CHECKLIST.md`

La checklist couvre **6 sections** :

| Section | Items clés |
| --- | --- |
| ✅ Mainteneur | Auteur, date dernier commit, CHANGELOG |
| ✅ Qualité du code | meta/main.yml, argument_specs, FQCN, variables préfixées |
| ✅ Sécurité | Secrets, HTTPS, checksum, permissions, become |
| ✅ Tests | molecule, verify, ansible-lint, CI/CD |
| ✅ Compatibilité | Platforms, min_ansible_version, deps obsolètes |
| ✅ Idempotence | changed=0 au 2e run, changed_when justifié |
| ✅ Maintenabilité | Commentaires, defaults, structure |

## 📚 Exercice 2 — Audit pratique de `geerlingguy.docker`

```bash
cd ~/.ansible/roles/geerlingguy.docker/

# Vérifier date dernier commit
git log -1 --format="%cd" 2>/dev/null || stat -c '%y' meta/main.yml

# Vérifier FQCN (chercher les non-FQCN)
grep -rE "^\s*-\s*(dnf|apt|copy|template|file|service):" tasks/

# Vérifier presence argument_specs
ls meta/argument_specs.yml 2>/dev/null

# Vérifier scénario molecule
ls molecule/default/molecule.yml 2>/dev/null
```

🔍 **Observation** : `geerlingguy.docker` est un rôle de **référence
Galaxy** — il devrait passer la plupart des checkpoints.

## 📚 Exercice 3 — Détecter les red flags classiques

```bash
# Anti-pattern 1 : secrets en dur
grep -rE "(password|api_key|secret).*=.*[a-zA-Z0-9]{8,}" roles/

# Anti-pattern 2 : URLs HTTP non sécurisées
grep -rE "http://" roles/

# Anti-pattern 3 : downloads sans checksum
grep -B2 -A5 "get_url:" roles/ | grep -v "checksum:"

# Anti-pattern 4 : command/shell sans creates/removes
grep -rB2 -A5 "command:\|shell:" roles/ | grep -v "creates:\|removes:\|changed_when:"
```

## 📚 Exercice 4 — Score d'audit

| Score | Décision |
| --- | --- |
| **9-10/10** sections OK | ✅ Adopter sans réserve. |
| **7-8/10** | ⚠️ Acceptable avec audit complémentaire. |
| **5-6/10** | 🔧 Risqué. Forker ou chercher alternative. |
| **< 5/10** | ❌ Refuser. Maintenance trop coûteuse. |

🔍 **Observation** : un score < 5/10 sur un rôle tiers est un signal fort
pour **écrire le sien** plutôt que d'hériter de la dette technique.

## 📚 Exercice 5 — Auditer `roles/webserver/` du lab

Le rôle livré dans `roles/webserver/` est un rôle **simple**. Passez-le à
la checklist :

- [ ] `meta/main.yml` présent ? Quels champs `galaxy_info` ?
- [ ] `meta/argument_specs.yml` présent ?
- [ ] `tasks/main.yml` utilise FQCN ?
- [ ] `defaults/main.yml` documente les variables ?
- [ ] `README.md` présent ?

Calculez son score sur 10.

## 🔍 Observations à noter

- **Auditer** = obligatoire avant adoption en production.
- Un rôle sans **`molecule/`** = pas de garantie de fonctionnement.
- Un rôle sans **`argument_specs.yml`** = vous devez vous-même valider les
  inputs au runtime.
- **CHANGELOG.md absent** ou vide = mainteneur n'investit pas dans la
  communication des breaking changes.
- **Préférer Red Hat / geerlingguy / ansible-collections** : ces auteurs
  ont un track record vérifiable.

## 🤔 Questions de réflexion

1. Vous trouvez un rôle parfait sauf qu'il télécharge un binaire en HTTP
   (pas HTTPS). Adoptez-vous ? Quels mitigations envisagez-vous ?

2. Différence entre **forker** un rôle et écrire le sien ? Quels critères
   pour choisir ?

3. Sur quels critères jugez-vous **CRITIQUES** (refus immédiat) vs
   **MAJEURS** (audit complémentaire) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`ansible-lint --profile=production`** : run sur le rôle audité.
- **`safety check`** sur les `requirements.txt` éventuels.
- **`grype`** ou **`trivy`** : scan vulnérabilités sur les images Docker
  référencées.
- **Audit automatisé** : intégrer le rôle dans un repo + faire tourner
  Molecule pour valider en pratique.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/galaxy/auditer-role-existant/
```
