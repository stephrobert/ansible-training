SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

LAB_DIR    := $(shell pwd)
INVENTORY  := $(LAB_DIR)/inventory/hosts.yml

GREEN := \033[0;32m
BLUE  := \033[0;34m
NC    := \033[0m

.PHONY: help bootstrap provision destroy verify-conn snapshot restore test-all lint-all clean ssh-control ssh-web1 ssh-web2 ssh-db1 status

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

provision:   ## Crée réseau libvirt + 4 VMs + prep managed nodes (Ansible)
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
	@cd $(LAB_DIR)/labs/000-prepare-managed-nodes && make run
	@echo -e "$(GREEN)[OK]$(NC) Lab prêt — lance 'make verify-conn' ou 'make test-all'"

destroy:     ## Détruit les 4 VMs et le réseau libvirt
	@echo -e "$(BLUE)[destroy]$(NC) Destruction du lab..."
	@./infra/virt-install/destroy.sh

verify-conn: ## ansible all -m ping (doit retourner pong sur les 4 hôtes)
	@echo -e "$(BLUE)[verify-conn]$(NC) Test connectivité Ansible..."
	@ansible all -i $(INVENTORY) -m ansible.builtin.ping

snapshot:    ## Snapshot libvirt sur les 4 VMs avant test risqué
	@./scripts/snapshot-vms.sh

restore:     ## Restaure les 4 VMs depuis le dernier snapshot lab-checkpoint-*
	@./scripts/restore-vms.sh

test-all:    ## Exécute make verify dans chaque labs/*/* unitaire
	@./scripts/test-all.sh

lint-all:    ## yamllint + ansible-lint sur tout le repo
	@./scripts/lint-all.sh

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
