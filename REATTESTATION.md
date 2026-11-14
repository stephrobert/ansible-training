# Re-attesting this catalogue's labs

> Written on 2026-10-19, with values **measured on disk** rather than copied.
> Numbers age: `validation-labs.json` remains the source of truth for verdicts.

## Why this page exists

On 2026-10-19, a re-attestation campaign recorded **twelve false REDs** in one
catalogue before being stopped, and hung for twenty-three minutes in another.
Neither cause had anything to do with the labs: a `.venv` whose shebangs still
named the repository's former path after a rename, and a command-line tool
waiting on network access the sandbox does not grant.

In both cases the validator **looked like it was measuring the labs when it was
measuring its own breakdown**, and it wrote that into the record. A false RED
costs more than a missing verdict: it sends people hunting for a defect in a lab
that has none.

## What this catalogue requires

- **dsoxlab 0.5.4 or newer** on the `PATH`. That is the engine version the record will carry, and the record states it for ALL labs: see the section on partial replays.
- The tools pinned by `mise.toml`, so run the command through `mise exec --`. Without it, a missing or differently versioned tool fails labs for reasons unrelated to their subject.
- **`.vault-pass` at the root**: 811 solution file(s) in this catalogue are ansible-vault encrypted, and the cycle lays them decrypted. The secret is never committed. Here: present.
- **Provisioned infrastructure**: 88 lab(s) are `runtime: vm` on the `lab-ansible` network and require `dsoxlab provision` before the campaign and `dsoxlab destroy` after. Expected hosts: `control-node.lab`, `web1.lab`, `web2.lab`, `db1.lab`.
- Real free memory, not what `doctor` reports: destroy the other repositories' infrastructure BEFORE provisioning this one, or the VMs compete for RAM and labs fail by exhaustion, which looks like a lab defect.
- **Docker reachable**: 2 lab(s) declare `runtime.services`. An unreachable service fails `run` and `check`, which do not silently record a 0.

### The step without which the validator refuses to run

This catalogue isolates its labs with qcow2 overlays: every lab starts from a
fresh VM, otherwise each one would grade the state left by the previous one.
`scripts/rebase-vms.sh` freezes that starting state, and **every
`dsoxlab provision` invalidates it**: provisioning recreates the domains with a
new UUID, and libvirt then refuses to restore the former memory state.

The sequence is therefore fixed, in this order:

```bash
dsoxlab provision                  # the meta.yml VMs
bash scripts/rebase-vms.sh         # full boot then memory freeze, a few minutes
mise exec -- uv run scripts/valider-labs.py
dsoxlab destroy                    # on the way out, to free the RAM
```

**Skipping the rebase does not produce a false green, it produces a RED about
something else.** Measured on 2026-10-19 on `bdd`: "isolation impossible:
db1.lab has no frozen base". The message names the gesture, but a RED verdict
written into the record then reads as a lab defect, when the lab was never
played at all. That is why that particular record was not committed.

The rebase wants VMs that **have played no lab**: right after provisioning,
then, and not in the middle of a campaign.

## The command

```bash
mise exec -- uv run scripts/valider-labs.py
```

A single lab, to exercise the harness before committing to all 113:

```bash
mise exec -- uv run scripts/valider-labs.py --lab <lab-id>
```

**Starting with one lab is not a matter of principle.** It is what separates an
environment defect from a lab defect: if the single lab passes, the harness is
sound; if it fails like the others, the harness is what needs fixing.

## Current state

**This catalogue has no `validation-labs.json`.** Its 113 labs have therefore never been attested: they are to be attested for the first time, not re-attested. No measured duration exists for them, so the campaign cost is unknown.

## The four traps that produce a false verdict

**1. A `.venv` with dead shebangs.** If the repository was renamed, the scripts
in `.venv/bin/` still point at the old path and no longer execute. The symptom
is an identical failure on every lab, often on decrypting the solution. Check
and fix:

```bash
head -1 .venv/bin/ansible-vault      # the path must exist
uv venv --clear && uv sync           # recreate it
```

**2. `uv run --no-sync` on an empty venv.** The flag assumes an already
populated environment. On a fresh clone it raises `ModuleNotFoundError` before
looking at a single lab. Run without `--no-sync` the first time.

**3. A tool waiting on network access the sandbox does not grant.** Measured on
an `octl --version` that hung for twenty-three minutes: only the top-level
command is exempt, a subprocess is not. If a campaign stops progressing, look at
its child processes before suspecting a lab:

```bash
ps -eo pid,etimes,cmd | grep -E 'python.*valider[-]labs'
ps --ppid <validator-pid> -o pid,etimes,cmd
```

**4. A partial replay makes the record's header false.** The engine version is
recorded **once for the whole file**, while verdicts are per lab. Replaying a
single lab therefore rewrites that header, and the record then claims all its
labs were attested with the current version. Either replay everything, or
restore the record:

```bash
git checkout -- validation-labs.json
```

## What the record does not say

It does not say **which engine version attested each lab**, only the one from
the last campaign. This is a known gap, and it shows as soon as a campaign is
partial.

**Here the record carries no engine version at all**: it has no root key, where six catalogues in the collection record `genere_le`, `dsoxlab` and each tool's version. Until that changes, nothing tells whether its verdicts hold for the current engine.

## Why this catalogue's verdicts are stale

They are not stale: **they do not exist**. This catalogue has no record, so its labs are to be attested for the first time. No measured duration exists, so the cost is unknown.

## The record's shape decides what the site can say about it

This catalogue's record uses the **aucun** shape, and the site can therefore display nothing about its attestation.

The site's generator reads `genere_le` and `dsoxlab` **only when the `labs`
key is a dictionary**: a record whose top-level keys are lab identifiers falls
into another branch, which returns an empty date and tool. Fixing the field
without fixing the shape would therefore change nothing, which is why both are
stated together here.
