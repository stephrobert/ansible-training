# Reset du lab filesystem — DESTRUCTIF.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## DESTRUCTIF — démonte et efface les fs sur /dev/vdb*
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "umount /mnt/data 2>/dev/null || true; for p in /dev/vdb1 /dev/vdb2 /dev/vdb3; do test -b \$$p && wipefs -af \$$p || true; done" 2>&1 | tail -2
