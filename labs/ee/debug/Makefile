LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime image EE de debug et logs
	@podman rmi -f localhost/lab88-buggy-ee:latest 2>/dev/null || true
	@rm -rf $(LAB_ROOT)/labs/ee/debug/logs/ 2>/dev/null || true
	@echo "Lab 88 : image EE buggy et logs nettoyés."
