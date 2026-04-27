# Reset du lab 95.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime collection construite + cache build
	@rm -rf $(LAB_ROOT)/labs/collections/creer-custom/ansible_collections \
	        $(LAB_ROOT)/labs/collections/creer-custom/build 2>/dev/null || true
