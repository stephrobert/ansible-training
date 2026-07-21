# Security Policy

**Language:** [English](./SECURITY.md) · [Français](./SECURITY.fr.md)

## Supported versions

`ansible-training` is in active development. Security fixes are applied to
the latest release on the `main` branch.

| Version | Supported |
| --- | --- |
| latest (`main`) | ✅ |
| older | ❌ |

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.**

If you believe you have found a security vulnerability, report it privately:

- Preferred: open a
  [private security advisory](https://github.com/stephrobert/ansible-training/security/advisories/new)
  on GitHub.
- Alternatively, use the contact details published at
  <https://blog.stephane-robert.info>.

Please include:

- a description of the vulnerability and its impact,
- the steps to reproduce it (command, environment, `dsoxlab --version`),
- any relevant logs or proof of concept.

We will acknowledge your report as soon as possible, keep you informed about the
progress toward a fix, and credit you in the release notes if you wish.

## Scope

This repository ships **lab content** (scenarios, tests, setup/cleanup and
provisioning fixtures, SSH public keys) executed by the external `dsoxlab` CLI.
In scope: unsafe or malicious lab material (setup/cleanup, tests,
Terraform/cloud-init templates), leaked secrets, or a private key committed by
mistake. This repository keeps its reference solutions encrypted with
`ansible-vault` under `solution/`: a solution committed in clear text, or the
vault password (`.vault-pass`) appearing in the history, are also covered by this
policy. Vulnerabilities in the `dsoxlab` engine itself belong to
[its own repository](https://github.com/stephrobert/dsoxlab); third-party
dependency issues should be reported to their respective projects.
