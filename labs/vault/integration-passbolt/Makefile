LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les containers Passbolt locaux (passbolt + mariadb)
	@podman rm -f passbolt mariadb-passbolt 2>/dev/null || true
	@echo "Stack Passbolt locale supprimée."
