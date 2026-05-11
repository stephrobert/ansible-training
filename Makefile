SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

LAB_DIR    := $(shell pwd)
INVENTORY  := $(LAB_DIR)/inventory/hosts.yml

GREEN := \033[0;32m
BLUE  := \033[0;34m
NC    := \033[0m

.PHONY: help bootstrap provision setup destroy verify-conn snapshot restore test-all lint-all clean ssh-control ssh-web1 ssh-web2 ssh-db1 status solutions-lock solutions-unlock solutions-status solve dsoxlab dsoxlab-next dsoxlab-stats lab hosts-add hosts-remove hosts-status ssh-config-add ssh-config-remove ssh-config-status

help:        ## Affiche cette aide
	@echo ""
	@echo "Lab Ansible RHCE — commandes disponibles"
	@echo "========================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

bootstrap:   ## Installe les outils requis (ansible, navigator, lint, molecule, yamllint, libvirt)
	@echo -e "$(BLUE)[bootstrap]$(NC) Installation des outils du lab..."
	@./scripts/bootstrap.sh

## provision = setup + hosts-add + ssh-config-add en une seule commande
provision: setup hosts-add ssh-config-add

## Crée réseau libvirt + 4 VMs + prep managed nodes (Ansible)
setup:
	@echo -e "$(BLUE)[provision]$(NC) Provisionning des VMs..."
	@./infra/virt-install/provision.sh
	@echo -e "$(BLUE)[provision]$(NC) Attente SSH (~30s)..."
	@for i in $$(seq 1 60); do \
	    READY=0; \
	    for IP in 10.10.20.10 10.10.20.21 10.10.20.22 10.10.20.31; do \
	        timeout 4 ssh -o ConnectTimeout=3 -o BatchMode=yes \
	            -i $(LAB_DIR)/ssh/id_ed25519 ansible@$$IP true 2>/dev/null \
	            && READY=$$((READY+1)); \
	    done; \
	    [ $$READY -eq 4 ] && echo "  SSH OK sur les 4 hôtes" && break; \
	    sleep 2; \
	done
	@echo -e "$(BLUE)[provision]$(NC) Préparation des managed nodes (Ansible)..."
	@cd $(LAB_DIR)/labs/bootstrap/prepare-managed-nodes && make run
	@echo -e "$(GREEN)[OK]$(NC) Lab prêt — lance 'make verify-conn' ou 'make test-all'"

destroy:     ## Détruit les 4 VMs et le réseau libvirt
	@echo -e "$(BLUE)[destroy]$(NC) Destruction du lab..."
	@./infra/virt-install/destroy.sh

verify-conn: ## ansible all -m ping (doit retourner pong sur les 4 hôtes)
	@echo -e "$(BLUE)[verify-conn]$(NC) Test connectivité Ansible..."
	@ansible all -i $(INVENTORY) -m ansible.builtin.ping

hosts-add:    ## 🔗 Ajoute les 4 hôtes du lab dans /etc/hosts (permet `ssh web1.lab`)
	@./scripts/manage-hosts.sh add

hosts-remove: ## 🧹 Retire les entrées du lab de /etc/hosts
	@./scripts/manage-hosts.sh remove

hosts-status: ## 🔍 État des entrées du lab dans /etc/hosts
	@./scripts/manage-hosts.sh status

ssh-config-add:    ## 🔑 Ajoute ~/.ssh/config.d/ansible-training.conf (utilise la clé du repo pour web1.lab, etc.)
	@./scripts/manage-ssh-config.sh add

ssh-config-remove: ## 🧹 Retire ~/.ssh/config.d/ansible-training.conf
	@./scripts/manage-ssh-config.sh remove

ssh-config-status: ## 🔍 État du fragment ~/.ssh/config.d/ansible-training.conf
	@./scripts/manage-ssh-config.sh status

snapshot:    ## Snapshot libvirt sur les 4 VMs avant test risqué
	@./scripts/snapshot-vms.sh

restore:     ## Restaure les 4 VMs depuis le dernier snapshot lab-checkpoint-*
	@./scripts/restore-vms.sh

test-all:    ## Exécute make verify dans chaque labs/*/* unitaire
	@./scripts/test-all.sh

lint-all:    ## yamllint + ansible-lint sur tout le repo
	@./scripts/lint-all.sh

solutions-lock:    ## 🔒 Chiffre toutes les solutions/ avec ansible-vault
	@./scripts/lock-solutions.sh

solutions-unlock:  ## 🔓 Déchiffre toutes les solutions/ (à reverrouiller avant commit)
	@./scripts/unlock-solutions.sh

solutions-status:  ## 📋 Affiche l'état chiffré/clair de chaque fichier de solution/
	@./scripts/solutions-status.sh

dsoxlab:    ## 📊 Tableau de bord d'avancement (CLI dans bin/dsoxlab)
	@./bin/dsoxlab

dsoxlab-next:    ## 🎯 Suggère le prochain lab à attaquer
	@./bin/dsoxlab next

dsoxlab-stats:   ## 📈 Statistiques par section
	@./bin/dsoxlab stats

lab:        ## 📖 Affiche un lab en Markdown riche (usage : make lab LAB=decouvrir/installation-ansible [CHALLENGE=1] [WIDTH=100])
	@if [ -z "$(LAB)" ]; then \
	    echo "Usage : make lab LAB=<section>/<dirname> [CHALLENGE=1] [BOTH=1] [WIDTH=N]"; \
	    exit 1; \
	fi
	@./bin/dsoxlab lab $(LAB) $(if $(CHALLENGE),-c) $(if $(BOTH),-b) $(if $(WIDTH),-w $(WIDTH))

solve:             ## 🎯 Pose la solution officielle d'un lab (usage : make solve LAB=ecrire-code/handlers)
	@if [ -z "$(LAB)" ]; then \
	    echo "Usage : make solve LAB=<section>/<lab>"; \
	    echo "Astuce : 'find labs -mindepth 2 -maxdepth 2 -type d | sort' pour lister."; \
	    exit 1; \
	fi
	@./scripts/solve.sh $(LAB)

clean:       ## Nettoie les artefacts temporaires
	@find . -name "*.retry" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete
	@find labs -name "expected-output.tmp" -delete 2>/dev/null || true
	@rm -rf .ansible_facts/
	@echo -e "$(GREEN)[OK]$(NC) Artefacts nettoyés"

ssh-control: ## SSH sur le control node
	@ssh -i $(LAB_DIR)/ssh/id_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ansible@10.10.20.10

ssh-web1:    ## SSH sur web1
	@ssh -i $(LAB_DIR)/ssh/id_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ansible@10.10.20.21

ssh-web2:    ## SSH sur web2
	@ssh -i $(LAB_DIR)/ssh/id_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ansible@10.10.20.22

ssh-db1:     ## SSH sur db1
	@ssh -i $(LAB_DIR)/ssh/id_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ansible@10.10.20.31

status:      ## État des 4 VMs (virsh list)
	@echo -e "$(BLUE)[status]$(NC) État des VMs du lab..."
	@virsh list --all | grep -E "control-node|web1|web2|db1" || echo "Aucune VM du lab trouvée"
