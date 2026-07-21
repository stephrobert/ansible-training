# Context — The template that crashed on a string it took for a list

The generator worked for a year. Then someone passed a single value where the
template expected a list. Jinja iterated over it happily — character by
character — and produced a config with one line per letter. Nobody noticed
until the service refused to start. Another day, an optional variable was
simply absent and the run died mid-render. A template that trusts its input is
a template waiting for the day the input changes.

You make it **check before it acts**, on `db1.lab`, from **control-node.lab**.

Your mission:

1. Write conditional lines into `/tmp/tests-jinja.txt` that only render when
   their test actually passes.
2. Test **existence** and test **type**: a variable that is defined, a value
   that is really a dict, a value that is really a list.
3. Test the negative case too: an optional variable that was never defined must
   be **detected as undefined**, not crash the render.
4. Do not mix the two syntaxes: a filter goes after `|`, a test goes after
   `is`. Then keep the output clean with whitespace control.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/tests-jinja/
