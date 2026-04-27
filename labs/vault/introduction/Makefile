LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime artefacts vault du lab/challenge sur web1 et db1
	@cd $(LAB_ROOT) && ansible web1.lab -b -m ansible.builtin.file \
	    -a "path=/tmp/lab77-vault-test.txt state=absent" 2>&1 | tail -2 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.file \
	    -a "path=/tmp/lab77-challenge-result.txt state=absent" 2>&1 | tail -2 || true
