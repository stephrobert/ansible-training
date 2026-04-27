# Reset du lab 34.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les fichiers locaux collectés + tag distant
	@rm -f $(LAB_ROOT)/collected/web1-os-release.txt
	@rm -f $(LAB_ROOT)/collected/db1-os-release.txt
	@rm -f $(LAB_ROOT)/collected/web1-tag.txt
	@cd $(LAB_ROOT) && ansible web1.lab -b -m ansible.builtin.file \
	    -a "path=/etc/lab-tag.txt state=absent" 2>&1 | tail -2
