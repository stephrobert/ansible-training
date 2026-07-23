# Context — The role that ran when it was told not to

A colleague guarded the `webserver` role with a `when:` and a feature flag, and
the role deployed anyway on a host that was supposed to stay untouched. The
condition was there, in plain sight, and it was ignored. The bug is not in the
`when:`, it is in the way the role was called: two of the three ways to invoke a
role resolve at parse time, and only one of them evaluates conditions at runtime.

Your mission, from the project directory, against **db1.lab**:

1. Deploy the `webserver` role the standard way, at play level, listening on
   port 8080: package, service, page, everything provable on the target.
2. **Import** the role's trace entry point statically, guarded by a feature
   flag that is off, and show both faces of "static": the trace file must NOT
   appear, yet the role's default variables must be visible to the play,
   because the role was loaded at parse time anyway.
3. **Include** the same entry point dynamically, under a condition that only
   exists at runtime (the live state of the nginx service), and show the
   mirror image: the trace file appears, but the role's variables stay
   private.
4. State the rule you would give your team: which form for a systematic role,
   which for a tag-driven one, which for a flag decided at runtime.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/consommer-role/
