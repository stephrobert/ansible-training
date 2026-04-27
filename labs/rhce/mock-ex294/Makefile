# Reset du lab 100 — purge tout l'état mock RHCE.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help prep clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

prep:    ## Pose l'environnement examen (vg_lab, UID 2001 libre, port 80 libre)
	@cd $(LAB_ROOT) && labs/rhce/mock-ex294/prep-environment.sh

clean:   ## Purge fichiers, paquets, services, users, FW, mounts du mock
	@cd $(LAB_ROOT) && ansible all -b -m ansible.builtin.shell \
	    -a "rm -f /tmp/lab100-* /tmp/file{1..5} 2>/dev/null; true" \
	    2>&1 | tail -3
	@cd $(LAB_ROOT) && ansible all -b -m ansible.builtin.user \
	    -a "name=appuser state=absent remove=yes" \
	    2>&1 | tail -2
	@cd $(LAB_ROOT) && ansible all -b -m ansible.builtin.group \
	    -a "name=appgroup state=absent" \
	    2>&1 | tail -2
