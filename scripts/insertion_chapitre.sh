#!/bin/bash

# Usage : ./insert_chapter.sh 03-Handlers

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <new-folder-name (e.g., 03-Handlers)>"
    exit 1
fi

new_folder="$1"

# Extraire le préfixe numérique du nouveau dossier
new_prefix=$(echo "$new_folder" | cut -d'-' -f1)
new_suffix=$(echo "$new_folder" | cut -d'-' -f2-)

# Vérifier que le préfixe est bien un entier
if ! [[ "$new_prefix" =~ ^[0-9]{2}$ ]]; then
    echo "Erreur : le dossier doit commencer par un numéro à deux chiffres (ex: 03-Handlers)"
    exit 1
fi

# Lister les dossiers existants correspondant au format NN-*
existing_dirs=($(ls -d [0-9][0-9]-* 2>/dev/null | sort -r))

# Renommer les dossiers existants pour faire de la place
for dir in "${existing_dirs[@]}"; do
    prefix=$(echo "$dir" | cut -d'-' -f1)
    suffix=$(echo "$dir" | cut -d'-' -f2-)

    if (( 10#$prefix >= 10#$new_prefix )); then
        new_index=$(printf "%02d" $((10#$prefix + 1)))
        mv "$dir" "${new_index}-${suffix}"
        echo "Renommé : $dir → ${new_index}-${suffix}"
    fi
done

# Créer le nouveau dossier
mkdir "$new_folder"
echo "Créé : $new_folder"
