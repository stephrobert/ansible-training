# Lab decouvrir/declaratif-vs-imperatif — comparer un script Bash et un playbook
# Ansible sur la même tâche (déploiement nginx).

LAB_ROOT  := $(shell git rev-parse --show-toplevel 2>/dev/null || cd ../../.. && pwd)
INVENTORY := $(LAB_ROOT)/inventory/hosts.yml
PLAYBOOK  := $(CURDIR)/playbook.yml
TARGET    := web1.lab
TARGET_IP := 10.10.20.21

.PHONY: setup run-bash run-ansible run verify clean help

help:
	@echo "Lab decouvrir/declaratif-vs-imperatif"
	@echo ""
	@echo "  make setup          État initial : nginx absent sur web1"
	@echo "  make run-bash       Joue 3 fois le script Bash impératif"
	@echo "  make run-ansible    Joue 3 fois le playbook Ansible déclaratif"
	@echo "  make run            run-bash + setup + run-ansible (le scénario complet)"
	@echo "  make verify         pytest + idempotence playbook (changed=0 au 2e run)"
	@echo "  make clean          Désinstalle nginx, retire la règle firewalld"

setup:
	@echo "[setup] Reset web1 (nginx + page d'accueil)..."
	@ssh -o StrictHostKeyChecking=no -i $(LAB_ROOT)/ssh/id_ed25519 ansible@$(TARGET_IP) \
	    "sudo dnf remove -y nginx >/dev/null 2>&1; sudo rm -rf /usr/share/nginx /var/log/nginx; sudo firewall-cmd --permanent --remove-service=http >/dev/null 2>&1; sudo firewall-cmd --reload >/dev/null 2>&1; echo OK"

run-bash:
	@echo "=== Push du script + 3 runs successifs ==="
	@scp -o StrictHostKeyChecking=no -i $(LAB_ROOT)/ssh/id_ed25519 \
	    $(CURDIR)/scripts/install-nginx-impératif.sh \
	    ansible@$(TARGET_IP):/tmp/install-nginx.sh >/dev/null
	@for i in 1 2 3; do \
	    echo "--- Run #$$i ---"; \
	    ssh -o StrictHostKeyChecking=no -i $(LAB_ROOT)/ssh/id_ed25519 ansible@$(TARGET_IP) \
	        "bash /tmp/install-nginx.sh 2>&1 | tail -3"; \
	done

run-ansible:
	@echo "=== 3 runs successifs du playbook ==="
	@for i in 1 2 3; do \
	    echo "--- Run #$$i ---"; \
	    cd $(LAB_ROOT) && ansible-playbook $(PLAYBOOK) 2>&1 | grep -E "PLAY RECAP|$(TARGET)" | tail -2; \
	done

run: setup run-bash setup run-ansible

verify:
	cd $(LAB_ROOT) && pytest -v $(CURDIR)/challenge/tests/

clean:
	@$(MAKE) setup
	@rm -f $(CURDIR)/expected-output.tmp
