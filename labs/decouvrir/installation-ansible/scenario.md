# Context — "It works on my machine"

A teammate hands you a playbook that runs fine on their laptop and dies on
yours with a laconic *"couldn't resolve module/action"*. Two hours later the
culprit surfaces: a missing collection. Nobody had ever written down what a
workstation must actually carry before it can be called a control node, so
everyone rediscovers it the hard way. You are going to encode that check once.

Everything happens on **your own control node**, no managed node involved.

Your mission:

1. Identify how Ansible got installed here, and refuse anything older than
   **ansible-core 2.18**.
2. Assert the **8 standard binaries** are on the `PATH`: a control node without
   `ansible-vault` cannot handle a single secret.
3. Assert a real module library is reachable (**at least 100 modules** via
   `ansible-doc`) and that the **3 collections** this repo relies on are
   installed.
4. Make it usable in CI: **exit 0** when the node is fit, **exit 1** with a
   message naming what is missing.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/installation-ansible/
