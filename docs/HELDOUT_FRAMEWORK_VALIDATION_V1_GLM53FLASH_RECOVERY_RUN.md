# GLM-5.3-Flash held-out validation recovery launch

Recovery implementation commit: `4bce7062d53a046e39f7dd0ed6c67dbb4fac7a40`.

Source execution run: `34232674771`.

The source run completed every frozen target generation but five shards terminated during judge-format parsing. The checkpoint-preserving recovery has passed deterministic CI, including frozen-design checks, malformed-JSON rejection, trailing-text parsing, exact target-run completeness, and a fail-closed prohibition on target regeneration.

This launch changes no scientific parameter. It restores source-run checkpoints, retains valid recorded votes, requests only missing preregistered vote keys with the original deterministic A/B orientation, and retries only judge response-format failures. The resulting aggregate remains Tier-1B cross-model same-family evidence and is not independent-provider validation.
