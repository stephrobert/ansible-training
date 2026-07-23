# Politique de sécurité

**Langue :** [English](./SECURITY.md) · [Français](./SECURITY.fr.md)

## Versions supportées

`ansible-training` est en développement actif. Les correctifs de sécurité
sont appliqués à la dernière version de la branche `main`.

| Version | Supportée |
| --- | --- |
| dernière (`main`) | ✅ |
| plus anciennes | ❌ |

## Signaler une vulnérabilité

**N'ouvrez pas d'issue publique pour une vulnérabilité de sécurité.**

Si vous pensez avoir trouvé une vulnérabilité, signalez-la en privé :

- De préférence : ouvrez un
  [avis de sécurité privé](https://github.com/stephrobert/ansible-training/security/advisories/new)
  sur GitHub.
- Sinon, utilisez les coordonnées publiées sur
  <https://blog.stephane-robert.info>.

Merci d'inclure :

- une description de la vulnérabilité et de son impact,
- les étapes pour la reproduire (commande, environnement, `dsoxlab --version`),
- tout log ou preuve de concept pertinent.

Nous accuserons réception de votre signalement dès que possible, vous tiendrons
informé de l'avancement du correctif, et vous créditerons dans les notes de
version si vous le souhaitez.

## Périmètre

Ce dépôt livre du **contenu de labs** (scénarios, tests, fixtures de mise en
place/nettoyage et de provisioning, clés SSH publiques) exécuté par la CLI
externe `dsoxlab`. Sont dans le périmètre : du matériel de lab dangereux ou
malveillant (setup/cleanup, tests, templates Terraform/cloud-init), une fuite de
secret, ou une clé privée commitée par erreur. Ce dépôt garde ses solutions de
référence chiffrées avec `ansible-vault` sous `solution/` : une solution commitée
en clair, ou le mot de passe du vault (`.vault-pass`) apparaissant dans
l'historique, relèvent aussi de cette politique. Les vulnérabilités du moteur
`dsoxlab` lui-même relèvent de
[son propre dépôt](https://github.com/stephrobert/dsoxlab) ; les problèmes des
dépendances tierces doivent être signalés à leurs projets respectifs.
