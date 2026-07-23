"""Tests pytest+testinfra pour le challenge « rôles système RHEL » (timesync).

Ce que ces tests prouvent, et comment.

Un rôle système ne « fait » rien de visible par lui-même : il CONFIGURE. On ne
vérifie donc ni qu'un playbook existe, ni qu'une commande a été tapée, mais
trois choses distinctes sur db1.lab :

1. le fichier de configuration a bien été PRODUIT PAR LE RÔLE (sa signature) et
   pas édité à la main par-dessus celui de la distribution ;
2. les variables du rôle ont bien été TRADUITES en directives chrony exactes ;
3. le démon TOURNE avec cette configuration (chronyc interroge chronyd en
   mémoire, pas le fichier sur disque) et l'horloge est réellement synchronisée.

Piège évité ici : `/etc/chrony.conf` d'AlmaLinux livre `#minsources 2` EN
COMMENTAIRE et `makestep 1.0 3` en directive active. Un test écrit
`assert "minsources 2" in content` serait donc VERT avant même que l'apprenant
ait ouvert son éditeur. On ne compare que des lignes actives, normalisées, et
par ÉGALITÉ, jamais par sous-chaîne.
"""

import time

import pytest
import yaml

from conftest import assert_idempotent, lab_host, lab_solution_text

TARGET_HOST = "db1.lab"
CHRONY_CONF = "/etc/chrony.conf"
NETWORK_SYSCONFIG = "/etc/sysconfig/network"

# Marqueur écrit par le template `chrony.conf.j2` du rôle timesync, et par lui
# seul : ni le paquet chrony, ni anaconda, ni aucun script d'AlmaLinux ne le
# posent. Sa présence signe la génération par le rôle.
ROLE_MARKER = "# system_role:timesync"
ROLE_FQCN = "fedora.linux_system_roles.timesync"

# Lignes EXACTES attendues dans chrony.conf, telles que le template du rôle les
# rend à partir de `timesync_ntp_servers`. L'ordre des options (maxpoll avant
# iburst) est imposé par le template : c'est ce qui distingue un fichier généré
# d'un fichier recopié de mémoire.
EXPECTED_SERVERS = [
    "server 0.fr.pool.ntp.org iburst prefer",
    "server 1.fr.pool.ntp.org iburst",
    "server 2.fr.pool.ntp.org maxpoll 10 iburst",
]

EXPECTED_HOSTNAMES = {
    "0.fr.pool.ntp.org",
    "1.fr.pool.ntp.org",
    "2.fr.pool.ntp.org",
}


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def directives(host):
    """Les lignes ACTIVES de chrony.conf, commentaires et blancs retirés."""
    contenu = host.file(CHRONY_CONF).content_string
    lignes = []
    for brute in contenu.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#"):
            continue
        lignes.append(" ".join(ligne.split()))
    return lignes


def _sources_chronyd(host):
    """Les sources que chronyd a RÉELLEMENT chargées, et leur état de sélection.

    `chronyc -N sources` rend les noms d'origine plutôt que les IP résolues :
    on lit donc ce que le démon a en mémoire, pas ce qui traîne sur le disque.
    C'est la différence entre « le fichier est écrit » et « la configuration
    est appliquée ».

    Returns:
        dict {nom de la source: état de sélection}. L'état est le 2e caractère
        de la colonne « MS » : `*` pour la source sur laquelle l'horloge est
        verrouillée, `+` pour une source acceptable, `-` pour une source
        écartée, `?` pour une source injoignable.
    """
    cmd = host.run("chronyc -N sources")
    assert cmd.rc == 0, f"chronyc a échoué : {cmd.stderr}"
    lignes = cmd.stdout.splitlines()
    debut = next(
        (i for i, ligne in enumerate(lignes) if ligne.startswith("===")), None
    )
    assert debut is not None, f"Sortie chronyc inattendue :\n{cmd.stdout}"
    sources = {}
    for ligne in lignes[debut + 1:]:
        champs = ligne.split()
        if len(champs) >= 2 and len(champs[0]) == 2:
            sources[champs[1]] = champs[0][1]
    return sources


# ----------------------------------------------------------------------
# Garde-fou : ce que le lab ne doit pas casser.
# ----------------------------------------------------------------------


def test_chronyd_reste_installe_actif_et_active(host):
    """chrony reste installé, chronyd démarré ET activé au boot.

    Ce test ne discrimine rien (il est déjà vert au départ) : c'est un
    garde-fou. Le lab bootstrap/prepare-managed-nodes exige cet état sur les
    managed nodes, et les VMs sont partagées. Une solution qui satisferait les
    tests suivants en cassant chronyd casserait son voisin.
    """
    assert host.package("chrony").is_installed
    chronyd = host.service("chronyd")
    assert chronyd.is_running
    assert chronyd.is_enabled


# ----------------------------------------------------------------------
# 1. Le fichier a été produit par le rôle, pas retouché à la main.
# ----------------------------------------------------------------------


def test_chrony_conf_porte_la_signature_du_role(host):
    """chrony.conf a été GÉNÉRÉ par le template du rôle timesync.

    Le rôle ouvre le fichier par l'en-tête `ansible_managed` suivi de
    `# system_role:timesync`. Aucune de ces deux lignes n'existe dans le
    chrony.conf livré par AlmaLinux : les trouver prouve que le fichier a été
    remplacé par le rôle, et non édité par un lineinfile posé à côté.
    """
    lignes = [ligne.strip() for ligne in host.file(CHRONY_CONF).content_string.splitlines()]
    assert ROLE_MARKER in lignes, (
        f"{CHRONY_CONF} ne porte pas la signature du rôle système "
        f"({ROLE_MARKER!r}). Le fichier n'a pas été généré par timesync."
    )
    assert "# Ansible managed" in lignes, (
        f"{CHRONY_CONF} ne porte pas l'en-tête `ansible_managed` du rôle."
    )


def test_le_pool_de_la_distribution_a_disparu(directives):
    """Plus aucune directive `pool` : le fichier d'origine a été REMPLACÉ.

    AlmaLinux livre `pool 2.almalinux.pool.ntp.org iburst`. Le rôle, lui, écrit
    des `server`. Si le pool est encore là, la configuration a été complétée à
    côté du fichier d'origine plutôt que régénérée : db1 interrogerait 4
    sources de plus que demandé.
    """
    pools = [ligne for ligne in directives if ligne.split()[0] == "pool"]
    assert not pools, (
        "Le pool par défaut de la distribution est toujours actif dans "
        f"{CHRONY_CONF} : {pools}"
    )


def test_sourcedir_dhcp_absent(directives):
    """Aucune directive `sourcedir` : les serveurs NTP du DHCP sont écartés.

    Le rôle n'écrit `sourcedir` que si `timesync_dhcp_ntp_servers` est vrai. Le
    laisser reviendrait à laisser le DHCP injecter des serveurs par-dessus ceux
    de la conformité.
    """
    sourcedirs = [ligne for ligne in directives if ligne.split()[0] == "sourcedir"]
    assert not sourcedirs, (
        f"`sourcedir` est encore actif dans {CHRONY_CONF} : {sourcedirs}"
    )


def test_peerntp_desactive(host):
    """`PEERNTP=no` dans /etc/sysconfig/network.

    Effet de bord du rôle que personne n'écrit spontanément : sans lui, le
    client DHCP réinjecte ses propres serveurs NTP au prochain bail et la
    conformité saute silencieusement. Au départ, ce fichier ne contient que
    `# Created by anaconda`.
    """
    lignes = [
        ligne.strip()
        for ligne in host.file(NETWORK_SYSCONFIG).content_string.splitlines()
    ]
    assert "PEERNTP=no" in lignes, (
        f"{NETWORK_SYSCONFIG} ne désactive pas les serveurs NTP du DHCP. "
        f"Lignes lues : {lignes}"
    )


# ----------------------------------------------------------------------
# 2. Les variables du rôle ont été traduites en directives exactes.
# ----------------------------------------------------------------------


@pytest.mark.parametrize("ligne_attendue", EXPECTED_SERVERS)
def test_serveur_ntp_declare(directives, ligne_attendue):
    """Chaque serveur est déclaré avec EXACTEMENT les options demandées.

    Comparaison par égalité de ligne, pas par sous-chaîne : `server
    0.fr.pool.ntp.org iburst` ne doit PAS satisfaire une attente qui réclame
    `prefer`, et l'ordre `maxpoll 10 iburst` est celui du template.
    """
    assert ligne_attendue in directives, (
        f"Ligne absente de {CHRONY_CONF} : {ligne_attendue!r}\n"
        f"Directives actives lues : {directives}"
    )


def test_seuil_de_correction_applique(directives):
    """`makestep 0.1 3` : le seuil demandé, pas celui de la distribution.

    AlmaLinux livre `makestep 1.0 3`. Le test échoue donc aussi bien si rien
    n'a été fait que si `timesync_step_threshold` a été oublié.
    """
    makesteps = [ligne for ligne in directives if ligne.split()[0] == "makestep"]
    assert makesteps == ["makestep 0.1 3"], (
        f"Attendu ['makestep 0.1 3'], lu : {makesteps}"
    )


def test_minimum_de_sources_applique(directives):
    """`minsources 2` en directive ACTIVE.

    La distribution livre cette ligne commentée (`#minsources 2`) : un test par
    sous-chaîne sur le contenu brut du fichier serait vert sans travail. On
    exige donc la ligne parmi les directives actives.
    """
    assert "minsources 2" in directives, (
        "`minsources 2` n'est pas une directive active de "
        f"{CHRONY_CONF}. Directives lues : {directives}"
    )


# ----------------------------------------------------------------------
# 3. Le démon tourne avec cette configuration, et l'horloge est synchronisée.
# ----------------------------------------------------------------------


def test_chronyd_a_recharge_la_configuration(host):
    """chronyd interroge EXACTEMENT les trois serveurs du rôle.

    Le test le plus important du lab : il lit l'état du démon en mémoire, pas
    un fichier. Une solution qui écrirait la bonne configuration sans notifier
    de redémarrage laisserait chronyd sur les sources du pool AlmaLinux, et ce
    test le verrait. Le rôle, lui, notifie son handler `Restart chronyd`.

    `chronyc -N sources` peut ne pas lister les trois sources dans l'instant qui
    suit le restart du démon (résolution des noms en cours), et le saut d'horloge
    que l'isolation applique au reset élargit cette fenêtre. On réessaie donc
    brièvement : soit les sources du rôle apparaissent (la config a été
    rechargée), soit le délai expire et l'assertion tranche (chronyd est resté
    sur le pool par défaut, la config n'a jamais été appliquée). Le retry ne
    masque pas un échec, il ne fait que laisser au démon le temps de répondre.
    """
    deadline = time.monotonic() + 20
    sources = set(_sources_chronyd(host))
    while sources != EXPECTED_HOSTNAMES and time.monotonic() < deadline:
        time.sleep(2)
        sources = set(_sources_chronyd(host))
    assert sources == EXPECTED_HOSTNAMES, (
        f"chronyd tourne avec les sources {sorted(sources)}, "
        f"attendu {sorted(EXPECTED_HOSTNAMES)}. La configuration sur disque "
        "n'a pas été rechargée par le démon."
    )


def test_horloge_verrouillee_sur_un_serveur_du_role(host):
    """L'horloge est synchronisée, ET sur l'un des serveurs demandés.

    Preuve de bout en bout : les serveurs configurés résolvent, répondent, et
    l'horloge du système est effectivement verrouillée sur l'un d'eux.

    Les deux moitiés comptent. `chronyc waitsync` seul serait vert AVANT le
    travail de l'apprenant : db1 est déjà synchronisé sur le pool AlmaLinux au
    démarrage du lab. C'est l'identité de la source retenue qui rend ce test
    discriminant : elle doit venir de la configuration produite par le rôle.
    """
    attente = host.run("chronyc waitsync 30 0 0 1")
    assert attente.rc == 0, (
        "chronyd n'a pas réussi à se synchroniser en 30 s sur les serveurs "
        f"configurés :\n{attente.stdout}\n{attente.stderr}"
    )
    sources = _sources_chronyd(host)
    verrouillees = {nom for nom, etat in sources.items() if etat == "*"}
    assert verrouillees, f"Aucune source sélectionnée par chronyd : {sources}"
    assert verrouillees <= EXPECTED_HOSTNAMES, (
        f"L'horloge est verrouillée sur {sorted(verrouillees)}, qui ne fait "
        f"pas partie des serveurs demandés {sorted(EXPECTED_HOSTNAMES)}."
    )


# ----------------------------------------------------------------------
# 4. Le sujet du lab : c'est bien le RÔLE SYSTÈME qui pilote tout ça.
# ----------------------------------------------------------------------


def test_la_solution_consomme_le_role_systeme():
    """Le play consomme `fedora.linux_system_roles.timesync`, en FQCN.

    Complément structurel assumé, et le seul de ce fichier : tous les tests
    ci-dessus vérifient l'ÉTAT de db1, et cet état reste atteignable à la main
    (rien n'empêche de recopier la sortie du template dans un `copy:`). Or le
    sujet du lab n'est pas « configurer chrony », c'est « consommer un rôle
    système ». On parse donc le YAML de la solution, on ne le grep pas : on
    exige le rôle dans la liste `roles:` d'un play, sous son nom pleinement
    qualifié, comme le jour de l'examen.
    """
    plays = yaml.safe_load(lab_solution_text(__file__))
    roles_consommes = set()
    for play in plays or []:
        for entree in play.get("roles", []) or []:
            nom = entree.get("role") if isinstance(entree, dict) else entree
            if nom:
                roles_consommes.add(nom)
    assert ROLE_FQCN in roles_consommes, (
        f"La solution ne consomme pas le rôle système {ROLE_FQCN} au niveau "
        f"du play. Rôles trouvés : {sorted(roles_consommes) or 'aucun'}. "
        "Le lab porte sur la consommation d'un rôle éditeur, pas sur "
        "l'écriture de chrony.conf."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un rôle système est un convergeur : rejoué, il ne doit ni réécrire
    chrony.conf ni redémarrer chronyd. Un playbook qui annonce encore des
    `changed` au second run n'est pas idempotent, même si l'état final paraît
    correct.
    """
    assert_idempotent(__file__)
