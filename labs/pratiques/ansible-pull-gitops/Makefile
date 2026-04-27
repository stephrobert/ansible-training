# Reset du lab 98.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime fichier preuve + repo-pull + cache pull sur db1.lab
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "rm -rf /tmp/lab98-pull-marker.txt /var/lib/ansible-pull" 2>&1 | tail -2
	@rm -rf $(LAB_ROOT)/labs/pratiques/ansible-pull-gitops/repo-pull 2>/dev/null || true
