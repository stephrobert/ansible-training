# Clé SSH du lab

La clé privée du lab (`id_ed25519`) est **gitignored**. Elle est regénérée
automatiquement par `make bootstrap` au premier lancement, dans ce dossier.

```bash
ssh-keygen -t ed25519 -N "" -f ssh/id_ed25519 -C "ansible-lab@$(hostname)"
```

La clé publique (`id_ed25519.pub`) est injectée dans cloud-init au
provisionnement des VM, et autorise le user `ansible` à se connecter en SSH
sur chaque hôte du lab.

Si tu cherches à utiliser une clé déjà existante (par exemple ta clé personnelle
`~/.ssh/id_ed25519`), tu peux à la place poser un lien symbolique vers ta clé :

```bash
ln -s ~/.ssh/id_ed25519     ssh/id_ed25519
ln -s ~/.ssh/id_ed25519.pub ssh/id_ed25519.pub
```

Le bootstrap respecte un fichier déjà présent et ne l'écrase pas.
