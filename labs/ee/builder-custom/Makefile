LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime image custom EE construite localement
	@podman rmi -f localhost/lab86-custom-ee:latest 2>/dev/null || true
	@rm -rf $(LAB_ROOT)/labs/ee/builder-custom/context/ 2>/dev/null || true
	@echo "Image EE et contexte du lab 86 nettoyés."
