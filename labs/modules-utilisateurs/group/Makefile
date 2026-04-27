# Reset du lab 41.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les groupes rhce-* et myapp-system sur db1
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "groupdel rhce-shared 2>/dev/null; groupdel rhce-admins 2>/dev/null; groupdel rhce-readonly 2>/dev/null; groupdel myapp-system 2>/dev/null; true" 2>&1 | tail -2
