LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime image EE locale + cache navigator
	@rm -rf $(LAB_ROOT)/labs/ee/hello/.ansible-navigator/ 2>/dev/null || true
	@echo "Cache ansible-navigator du lab 84 nettoyé."
