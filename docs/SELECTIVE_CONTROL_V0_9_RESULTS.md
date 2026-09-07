# Selective Control v0.9 — recovered results

## Status

Workflow run `34135081395` was cancelled at the GitHub-hosted runner time limit after the final scheduled comparison had begun, before `run_v09.py` could synthesize `v09_report.json`.

The runner checkpoint uploaded successfully. Raw completeness was:

- target generations: `108/108`;
- absolute behavior votes: `108/108`;
- paired TARGET-vs-CONTROL behavior votes: `108/108`;
- quality votes: `323/324`;
- every `TARGET_vs_CONTROL` quality vote: complete;
- every `TARGET_vs_ATTENTION` quality vote: complete;
- only missing datum: replicate 3, `RF-V09-EN02-STRESS`, `ATTENTION_vs_CONTROL`, vote 3.

The experiment is therefore usable for its two primary quality comparisons and both preregistered behavioral gates, but not as a formally completed workflow report.

## Preregistered selective-control gates

A family was interpretable as stress-triggered selective recovery only if both conditions held:

1. `CLEAN CONTROL - STRESS CONTROL behavior >= 0.5/4`;
2. `STRESS TARGET - STRESS CONTROL behavior >= 0.5/4`.

Recovered results:

| Family | Clean control behavior | Stress control behavior | Stress drop | Gate 1 | Paired stress TARGET-CONTROL behavior lift | Gate 2 | Selective recovery interpretable? |
| --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| DIAGNOSE | 3.556 | 3.722 | -0.167 | fail | +0.833 | pass | no |
| REVISE | 4.000 | 4.000 | 0.000 | fail | +0.222 | fail | no |
| ENGINEER | 4.000 | 3.778 | +0.222 | fail | +1.389 | pass | no |

No family passed Gate 1. The constructed stressors did not suppress endogenous target behavior enough to identify a stress-recovery effect.

## Quality results — descriptive because Gate 1 failed

| Family | TARGET vs CONTROL — clean | TARGET vs CONTROL — stress | TARGET vs ATTENTION — clean | TARGET vs ATTENTION — stress |
| --- | ---: | ---: | ---: | ---: |
| DIAGNOSE | 0.694 | 0.722 | 0.667 | 0.750 |
| REVISE | 0.500 | 0.611 | 0.417 | 0.222 |
| ENGINEER | 1.000 | 0.972 | 1.000 | 1.000 |

These scores do not establish stress-triggered recovery because the required stress-degradation gate failed. They remain useful development evidence. In particular, ENGINEER again produced a strong quality signal against both CONTROL and generic ATTENTION across clean and stressed variants.

## Measurement warning discovered by v0.9

The behavior judge was format-sensitive. Absolute CONTROL behavior stayed near ceiling, while side-by-side TARGET-vs-CONTROL behavior scoring sometimes assigned materially lower CONTROL scores. The discrepancy was especially large for ENGINEER under stress.

This creates a plausible contrast effect: seeing a stronger TARGET response can make CONTROL look weaker than it does when scored independently.

Therefore future manipulation measurement must not use side-by-side behavior scoring as the primary mediation measure. The next experiment computes behavior lift from independently presented absolute behavior judgments for CONTROL, ATTENTION, and TARGET.

## Interpretation

v0.9 does **not** establish stress-selective routing. It does strengthen the development hypothesis that explicit ENGINEER control can improve reasoning quality, while DIAGNOSE remains incrementally unresolved and the current explicit REVISE wording lacks persuasive incremental evidence.

All v0.9 cases remain development data and are not eligible for future held-out validation.