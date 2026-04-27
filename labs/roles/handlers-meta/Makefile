# Reset du lab 60.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Désinstalle nginx, supprime les logs et règles firewall sur db1
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.systemd_service \
	    -a "name=nginx state=stopped enabled=no" 2>&1 | tail -2 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.dnf \
	    -a "name=nginx state=absent" 2>&1 | tail -2 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "rm -f /var/log/webserver-deploy.log /var/log/deploy-notification.log" 2>&1 | tail -2
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.posix.firewalld \
	    -a "port=8080/tcp state=disabled permanent=yes immediate=yes" 2>&1 | tail -2 || true
