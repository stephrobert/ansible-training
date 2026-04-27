# Reset du lab 47.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Démonte /mnt/lab-data + supprime fstab + image
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.posix.mount \
	    -a "path=/mnt/lab-data state=absent" 2>&1 | tail -2
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "rm -f /opt/lab-disk.img; rmdir /mnt/lab-data 2>/dev/null; true" 2>&1 | tail -2
