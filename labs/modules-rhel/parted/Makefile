# Reset du lab parted — DESTRUCTIF.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## DESTRUCTIF — efface la table de partitions de /dev/vdb
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "wipefs -af /dev/vdb || true; sgdisk --zap-all /dev/vdb || true" 2>&1 | tail -2
