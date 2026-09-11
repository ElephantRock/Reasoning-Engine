# Paper build

Current manuscript sources:

- `MANUSCRIPT_DRAFT_V2.md` — readable preprint-oriented source;
- `main.tex` — neutral LaTeX build target;
- `references.bib` — bibliography;
- `REPRODUCIBILITY_APPENDIX_V1.md` — exact experimental provenance;
- `TABLES_AND_FIGURES_V1.md` — frozen figure/table data and interpretation rules;
- `make_figures.py` — deterministic figure renderer;
- `SUBMISSION_CHECKLIST_V1.md` — submission readiness state;
- `MANUSCRIPT_REVIEW_V2.md` — second-pass reviewer audit.

## Generate figures

Requires Python 3 and matplotlib.

```bash
python paper/make_figures.py
```

This writes PDF and PNG figures under `paper/figures/`. The figure script contains no model calls and performs no new inference.

## Build LaTeX

From the `paper/` directory:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

`main.tex` conditionally includes generated figures, so the manuscript can compile before figures are rendered.

## Before public release

Replace `Anonymous for review` with actual author metadata as appropriate, then complete the unchecked items in `SUBMISSION_CHECKLIST_V1.md`.

Do not change experiment values in the manuscript without checking the authoritative result documents under `docs/`.
