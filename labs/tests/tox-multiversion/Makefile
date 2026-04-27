LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Reset (purement local : pas de managed nodes touchés)
	@cd $(CURDIR) && molecule destroy 2>/dev/null || true
	@rm -rf $(CURDIR)/.tox 2>/dev/null || true
	@echo "Lab nettoyé"
