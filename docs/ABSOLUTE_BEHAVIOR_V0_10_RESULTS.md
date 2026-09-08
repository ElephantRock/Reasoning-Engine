# Absolute Behavior Identification v0.10 — Results

Run: `34161654785`

Commit: `f04bcd9b5a88290d91b308fa4bd9d1a652bcecda`

Experiment role: development diagnostic, not held-out validation.

## Manipulation result

Independent absolute behavior scoring removed the v0.9 side-by-side contrast concern, but the coarse 0–4 scale saturated.

### TEST

- CONTROL: `4.000`
- ATTENTION: `4.000`
- TARGET: `4.000`
- TARGET minus CONTROL: `0.000`
- identification gate: **failed**

### ENGINEER

- CONTROL: `4.000`
- ATTENTION: `3.667`
- TARGET: `4.000`
- TARGET minus CONTROL: `0.000`
- identification gate: **failed**

The preregistered gate was `TARGET - CONTROL >= 0.5/4`.

Therefore v0.10 does not identify a causal instruction -> broad-behavior pathway for either family.

## Quality result

The quality results nevertheless strongly favored TARGET.

### TARGET vs CONTROL

Overall score: `0.778`, 95% case-bootstrap interval `0.611–0.944`.

By family:

- TEST: `0.778`
- ENGINEER: `0.778`

### TARGET vs ATTENTION

Overall score: `0.931`, interval `0.833–1.000`.

By family:

- TEST: `0.889`
- ENGINEER: `0.972`

### ATTENTION vs CONTROL

Overall score for ATTENTION: `0.167`, interval `0.042–0.292`.

By family:

- TEST: `0.250`
- ENGINEER: `0.083`

Generic extra attention was therefore not an adequate explanation for the TARGET quality advantage on these development cases.

## Diagnostic interpretation

Raw behavior-judge notes show why the absolute manipulation gate failed: CONTROL already clearly performed the broad category of behavior. For example, CONTROL already selected discriminating evidence on TEST cases and already produced mechanism-linked, monitored, reversible intervention plans on ENGINEER cases.

Raw quality-judge notes repeatedly preferred TARGET for finer-grained execution differences, including:

- more complete prospective outcome branches;
- stronger falsification/anti-confirmation logic;
- clearer outcome-to-belief/update rules;
- more explicit control of confounds;
- quantitatively bounded temporary mitigations;
- stronger precommitted rollback/stop criteria;
- better reversible/irreversible sequencing;
- more explicit second-order monitoring and containment.

This suggests that the 0–4 behavior measure is too coarse for already-capable models. It measures capability presence rather than execution fidelity.

## Consequence

v0.11 replaces the single coarse behavior score with a five-criterion behavioral-fidelity composite. Each response is still scored independently; no behavior/fidelity judge sees competing conditions side by side.
