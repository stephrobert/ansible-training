LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime artefacts locaux (mon_role, monorg, .tar.gz)
	@rm -rf /tmp/mon_role /tmp/monorg 2>/dev/null || true
	@rm -f $(LAB_ROOT)/labs/galaxy/ansible-galaxy-cli/*.tar.gz 2>/dev/null || true
	@echo "Artefacts ansible-galaxy locaux nettoyés."
