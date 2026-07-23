# Context — Talk to the API from the playbook, not from a curl pipeline

The deployment chain has to register each server with an inventory API: read
the reference payload, then declare the node. Today it is done with
`command: curl` piped into `jq`, and it hurts. The exit status says nothing
useful about the HTTP code, the response is parsed with a regex, and any API
that answers `201` instead of `200` breaks the run. You rewrite the exchange
from **control-node.lab**, targeting **db1.lab**, with Ansible actually parsing
the JSON instead of a shell pretending to.

Your mission:

1. **Query the reference endpoint** in GET from **db1.lab**, **capturing the
   response body**, which the module does not return by default, and save it
   under `/opt/`.
2. **Declare the node in POST** with a **JSON body** built as a structure, not a
   hand-escaped string.
3. **Accept the API's legitimate codes** (`200` and `201`): a creation
   answering `201` is a success, not a failure.
4. Save the **parsed** response as readable JSON, working from the structure the
   module returns rather than from raw text.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/reseau/module-uri/
