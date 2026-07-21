# 🎯 Challenge : auditer un vrai rôle tiers, conclusions vérifiées

## ✅ Mission

Le lab embarque dans `vendor/thirdparty_backup/` un rôle tiers tel qu'on
en trouve sur Galaxy ou GitHub : court, pratique... et truffé de
problèmes. Auditez-le avec la méthodologie de `AUDIT_CHECKLIST.md` (à la
racine du lab) et consignez vos conclusions **factuelles** dans
`challenge/audit.yml`.

Pytest recalcule chaque fait directement depuis le code du rôle et le
compare à votre rapport : un audit copié-collé sans lire le rôle ne
passera pas.

Format exact attendu pour `challenge/audit.yml` :

```yaml
---
role: thirdparty_backup
has_argument_specs: <bool>        # meta/argument_specs.yml présent ?
has_molecule_tests: <bool>        # dossier molecule/ présent ?
non_fqcn_task_count: <int>        # tâches utilisant un module SANS FQCN
insecure_download_count: <int>    # téléchargements en http:// (non TLS)
unguarded_shell_count: <int>      # shell/command sans creates:/removes:
ignore_errors_count: <int>        # tâches avec ignore_errors: true
secret_in_defaults: <bool>        # secret en clair dans defaults/ ?
score: <int 0-10>                 # votre note globale
verdict: <adopt|fork|reject>      # votre recommandation argumentée
```

## 🧩 Indices

- Parcourez chaque fichier du rôle : `tasks/`, `defaults/`, `meta/`,
  et notez ce qui manque autant que ce qui est présent.
- Un module sans point dans son nom (`yum:` au lieu de
  `ansible.builtin.yum:`) n'est pas FQCN.
- Un `shell:`/`command:` sans `creates:` ni `removes:` casse
  l'idempotence : comptez-les.
- Un mot de passe dans `defaults/main.yml` finit dans Git de tous les
  consommateurs du rôle : c'est éliminatoire en production.
- Le barème est le vôtre, mais souvenez-vous de la grille de
  `AUDIT_CHECKLIST.md` : secret en clair + zéro test, la conclusion ne
  fait pas débat.

## 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes utilisées pour
l'audit (grep, find, ansible-lint éventuel...). Ce journal doit exister
pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/galaxy/auditer-role-existant/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean galaxy-auditer-role-existant
```

## 💡 Pour aller plus loin

- Passez `ansible-lint --profile production vendor/thirdparty_backup/` :
  combien de vos findings retrouve-t-il tout seul ? Lesquels lui
  échappent (le secret, l'URL http) ?
- Auditez un rôle réel de Galaxy avec la même grille et comparez.
- Transformez la grille en PR template pour vos revues internes.
