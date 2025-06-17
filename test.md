## En une phrase, comment définiriez-vous DevOps à un public non technique ?

### Constat avant l’approche DevOps :

Traditionnellement, les équipes de développement (Dev) et d’exploitation (Ops)
travaillaient de manière séparée. Les développeurs étaient responsables de la
création des applications, tandis que les équipes d’exploitation géraient le
déploiement, la stabilité et la maintenance des systèmes en production. Cette
séparation entraînait souvent des silos, des incompréhensions, des délais
importants lors des mises en production, et une difficulté à réagir rapidement
aux besoins du marché ou aux incidents.

### Objectifs du DevOps :

DevOps vise à rapprocher ces deux mondes pour accélérer la livraison de
logiciels fiables, améliorer la collaboration et automatiser les processus.
L’objectif est de livrer plus rapidement de la valeur, tout en garantissant la
stabilité et la sécurité des systèmes.

### Modèle CALMS

Pour structurer la démarche DevOps, le modèle CALMS est souvent utilisé. Il
repose sur cinq piliers :

- Culture : Favoriser la collaboration, la confiance et le partage des
responsabilités entre toutes les équipes.
- Automation : Automatiser les tâches répétitives (tests, intégration,
déploiement) pour gagner en efficacité et en fiabilité.
- Lean : S’inspirer des principes Lean pour éliminer les gaspillages, optimiser
les processus et améliorer en continu.
- Measurement : Mesurer les performances, la qualité et les incidents pour
piloter l’amélioration continue.
- Sharing : Encourager le partage des connaissances, des bonnes pratiques et des
retours d’expérience.

### Définition du DevOps :

**Contrairement aux idées reçues, le DevOps n’est ni une méthode, ni une
technologie, ni un rôle isolé. Ce n’est pas non plus une simple automatisation
des tâches ou la mise en place de pipelines CI/CD. Et surtout, ce n’est pas une
équipe à part agissant en dehors des développeurs et des opérations.**

**Le DevOps est avant tout une culture de collaboration et de responsabilité
partagée entre le développement, l’exploitation, et parfois la sécurité, visant
à livrer plus rapidement des logiciels fiables, sûrs et alignés sur les besoins
métier, grâce à l’automatisation, à la communication et à l’amélioration
continue.**

## Vous accompagnez au quotidien des clients dans leur transformation. Quels freins rencontrez-vous souvent en France ? S’agit-il de technique, de processus, de mindset ?

Très souvent, ce ne sont pas les outils qui bloquent, mais les habitudes de
travail, les silos organisationnels et parfois une culture du contrôle assez
forte. On parle souvent de freins techniques, mais dans les faits, ce sont
surtout des freins humains et culturels. » Voici les freins les plus fréquents
que j’observe :

- Le mindset : “On a toujours fait comme ça” 👉 Beaucoup d’équipes restent sur
des cycles de validation longs, avec des validations manuelles, car elles ont
peur de l’automatisation. Il y a un manque de confiance dans les chaînes CI/CD,
souvent dû à un manque de tests automatisés.
- Le cloisonnement des équipes 👉 On retrouve encore beaucoup d'organisations où
développeurs, ops, sécurité, et conformité travaillent séparément, avec des
processus d’escalade lourds. Résultat : des délais, des conflits de
responsabilités, et peu de vision globale.
- La surcharge de règles internes 👉 Dans certaines grandes structures, des
politiques internes ou des processus de gouvernance sont devenus tellement
rigides qu’ils bloquent l’expérimentation. C’est l’opposé de l’itération rapide
attendue dans un modèle DevOps.
- Le manque de formation ou d’acculturation 👉 Le mot “DevOps” circule, mais peu
d’équipes sont formées à ce que cela implique réellement. Les outils sont
parfois mis en place (GitLab, Jenkins, Terraform…), mais les pratiques, elles,
ne changent pas.
- La peur de l’échec visible 👉 L’automatisation rend les erreurs visibles plus
rapidement. Et dans certaines cultures d’entreprise, l’erreur est encore vécue
comme une faute plutôt qu’une opportunité d’apprentissage. Cela freine
l’expérimentation.

Conclusion : « Finalement, c’est rarement un problème d’outillage. Ce qui
bloque, c’est l’absence de vision partagée, la peur du changement, et le manque
d’un cadre bienveillant pour apprendre de ses erreurs. C’est pour ça qu’un
accompagnement humain et progressif est souvent plus efficace qu’un simple
projet technique. »

> « Tant que la sécurité est perçue comme un frein, elle sera contournée. Tant
> qu’elle est pilotée comme une obligation externe, elle restera isolée. Il faut
> qu’elle devienne une **valeur commune**, portée par toute la chaîne. »

Aujourd’hui, le principal frein à l’adoption des pratiques DevSecOps n’est pas
technique, mais **culturel**. La sécurité est encore trop souvent vécue comme
une contrainte imposée par une entité externe — la direction sécurité, la
conformité, l’audit. Ce modèle descend de l’ère du cycle en V, où l’on « livrait
» au RSSI une version à valider *a posteriori*. Dans un monde agile, ce
fonctionnement ne tient plus.

Pour que le DevSecOps fonctionne, il faut **changer de posture** à tous les
niveaux. Cela commence par **abandonner les approches coercitives** : bloquer
les mises en production, imposer des checklists incomprises, ou sanctionner
l’erreur visible n’encourage ni la qualité, ni la sécurité. Au contraire, cela
alimente la défiance, les contournements, et la dette technique invisible.

👉 **Il faut créer un environnement où chacun se sent responsable de la
sécurité, sans avoir peur d’échouer.**

Ce changement ne concerne pas seulement les développeurs ou les ops. Il concerne
tout le monde dans l’organisation, y compris les **équipes produit**, les
**architectes**, et surtout — les **équipes dirigeantes**. Beaucoup de blocages
viennent d’un **manque de formation du management**, qui continue de penser en
termes de contrôle et de validation, alors que la sécurité doit aujourd’hui être
**intégrée, automatisée, continue et transparente**.

### Comment faire évoluer cette culture sans sacrifier la vélocité ?

* **Aligner les objectifs** dès le début du projet : la sécurité n’est pas un
  bonus à la fin, c’est un prérequis à chaque étape.
* **Automatiser les contrôles** dans la CI/CD (SCA, SAST, policies IaC), pour
  détecter tôt et corriger rapidement, sans intervention manuelle.
* **Donner le droit à l’erreur** : toute faille détectée est une opportunité
  d’apprendre, pas une occasion de blâmer.
* **Former tous les profils** : développeurs, PO, managers, métiers. Si seuls
  les techs sont formés, la transformation reste superficielle.
* **Valoriser les progrès** : plutôt que de traquer les non-conformités,
  célébrer les pipelines sécurisés, les correctifs déployés rapidement, les
  bonnes pratiques adoptées.

**En résumé** : Le DevSecOps, ce n’est pas des outils en plus. C’est **une
nouvelle manière de collaborer**, de partager la responsabilité de la sécurité,
et de créer un environnement où la protection n’est plus perçue comme un
obstacle… mais comme un catalyseur de qualité et de confiance.

## Pouvez-vous expliquer simplement à nos auditeurs ce qu’on entend par cloud souverain et pourquoi c’est important ? En quoi un cloud certifié SecNumCloud, par exemple, est-il différent d’un cloud public classique du type AWS ou Azure ?

Le cloud souverain, c’est un cloud qui respecte non seulement des règles
techniques, mais aussi juridiques et géopolitiques. C’est un cloud opéré en
France ou en Europe, par des acteurs soumis au droit européen, sans risque
d’ingérence étrangère. » Pourquoi c’est important ? Avec les lois
extraterritoriales comme le Cloud Act américain, des données hébergées en Europe
par une entreprise américaine peuvent potentiellement être accessibles aux
autorités US. Cela pose un problème de confidentialité, mais aussi de conformité
réglementaire pour certaines organisations, notamment dans :

- La santé (données sensibles)
- Le secteur public
- Les industries dites d’importance vitale (OIV) comme la défense ou l’énergie

Qu’apporte la certification SecNumCloud ? SecNumCloud, c’est une certification
de l’ANSSI, très exigeante, qui garantit : Une sécurité de haut niveau
(architecture, chiffrement, contrôle d’accès…)

- Une gouvernance 100 % française ou européenne
- Une protection juridique contre les lois extraterritoriales

👉 Par exemple, chez Outscale, notre cloud certifié SecNumCloud est utilisé par
des ministères, des hôpitaux ou des entreprises critiques. Cela leur permet de
faire du cloud sans compromis sur la souveraineté, tout en gardant des pratiques
DevOps modernes. En quoi c’est différent d’un AWS ou Azure ? Ce n’est pas une
question de performance ou de technologie brute : beaucoup d’acteurs souverains
utilisent les mêmes standards (VMs, conteneurs, stockage objet…).

La différence clé, c’est l’indépendance : où sont les données, qui les
administre, et sous quelle juridiction.

Conclusion possible : « En résumé, le cloud souverain n’est pas une version
“bridée” du cloud. C’est un choix stratégique pour les organisations qui veulent
tirer parti du DevOps et de la scalabilité, tout en gardant le contrôle total
sur leurs données et leur conformité. »

## Vous qui êtes au contact des nouvelles technos, est-ce que vous utilisez déjà
l’IA dans vos processus ? Par exemple, Copilot ou des algos pour optimiser les
déploiements ? Et comment voyez-vous ça évoluer ?

« Oui, on commence à utiliser l’IA au quotidien, notamment avec des outils comme
GitHub Copilot ou des modèles d’IA pour prioriser des alertes, détecter des
erreurs plus vite, voire générer des tests. Mais ce n’est pas magique. L’IA dans
DevOps, c’est une aide, pas une baguette. » Voici quelques usages concrets que
j’ai vus ou expérimentés : Aide à la rédaction de code ou de YAML 👉 Avec
Copilot, on gagne du temps sur les blocs de code répétitifs – que ce soit pour
écrire un playbook Ansible, un module Terraform ou une pipeline CI/CD. Mais il
faut toujours valider ce que propose l’IA.

Optimisation de pipelines 👉 On commence à voir des outils qui analysent
l’historique des exécutions pour suggérer des points d’optimisation : étapes
lentes, jobs inutiles, erreurs récurrentes, etc. Ce sont des gains incrémentaux,
mais réels.

AIOps (IA pour les opérations) 👉 Dans certaines grandes infrastructures, l’IA
est utilisée pour faire du tri intelligent dans les alertes, détecter les
comportements anormaux, ou même prédire des incidents à venir. On en est encore
aux débuts, mais ça progresse vite.

Génération ou réécriture de documentation technique 👉 Certains outils comme
Cody, Tabnine, ou les LLMs internes permettent de générer de la doc, des
readmes, ou des guides d’installation, à partir du code. C’est un gain de
productivité, surtout dans les équipes qui manquent de temps pour bien
documenter.


Et demain ? Je pense qu’on va voir apparaître des copilotes spécialisés pour
chaque partie du DevOps : Un copilote pour la sécurité (expliquer les CVE,
proposer des correctifs)


Un copilote pour l’observabilité (faire parler les logs)


Un copilote pour l’IaC (suggérer des patterns Terraform sécurisés)


Mais il faudra toujours des humains pour valider, interpréter, et surtout,
rester responsables des décisions. L’IA peut accélérer, mais elle ne remplace ni
la compréhension métier, ni l’expérience terrain.

💬 Conclusion possible : « L’IA n’efface pas le DevOps, elle l’augmente. Elle
peut fluidifier les tâches répétitives, aider à sécuriser ou optimiser, mais
elle ne remplace pas l’expertise. Le défi, ce sera d’en faire un assistant de
confiance, pas une boîte noire. »

