# Reset du lab yum_repository.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les .repo de test sur db1
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "rm -f /etc/yum.repos.d/local-test.repo /etc/yum.repos.d/epel-test.repo" 2>&1 | tail -2
