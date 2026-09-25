# Manuscript: IEEE TGRS submission package

**Title:** Does a Governing Equation Help? A Controlled Evaluation of a Convection-Diffusion-Reaction
Physics-Informed Neural Operator for Forest Fire Susceptibility Mapping in India

Prepared 2026-09-25 from the audited results (`results/FINAL_MANUSCRIPT_NUMBERS.md`). Every number in the
paper comes from the audit result files. The Markdown version of the same paper is
`../CDR_PINN_Full_Paper_Draft.md`.

## Contents

| File | What it is |
|---|---|
| `main.tex` | Full manuscript in `IEEEtran` journal format (11 pages when compiled) |
| `references.bib` | Bibliography (36 references, IEEE style) |
| `main.pdf` | Compiled PDF of the current version |
| `main.bbl` | Compiled bibliography, which some submission systems require |
| `figures/` | Figures 3 to 10 (PNG, 200 dpi). Figs. 1 and 2 are drawn in TikZ inside `main.tex` |
| `figures_src/make_fig_contribution.py` | Redraws Fig. 7 with non-overlapping labels from `results/final/FIGURE_DATA/FigA_contribution_1km.csv` |

### Figures

1. **Fig. 1.** Workflow flowchart (TikZ).
2. **Fig. 2.** Detailed CDR-PINO architecture (TikZ): the FNO path, one Fourier layer, the three
   physics heads, the spectral derivatives, the residual and the loss.
3. **Fig. 3.** Physics-term ablation.
4. **Fig. 4.** Same-cell comparison.
5. **Fig. 5.** Held-out years vs persistence baselines.
6. **Fig. 6.** Term magnitudes.
7. **Fig. 7.** Contribution decomposition.
8. **Fig. 8.** National susceptibility map.
9. **Figs. 9 and 10** (Appendix): reference-study importance comparison and MaxEnt sample size.

### Tables

1. Predictors.
2. Evaluation tracks.
3. Classical results.
4. Physics ablation.
5. Same-cell comparison.
6. Term magnitudes.
7. ΔAUC decomposition.
8. Sensitivity (Appendix).

Algorithm 1 is the training epoch.

## Compile

On Overleaf, upload the whole folder; the compiler is pdfLaTeX. Locally, with TeX Live or MiKTeX:

```bash
latexmk -pdf main.tex
```

This is equivalent to running `pdflatex main`, then `bibtex main`, then `pdflatex main` twice.

## Before submission (checklist)

- [ ] **Authors and affiliations.** Replace the placeholder names, affiliations, e-mail and
  corresponding-author line in `main.tex` (the `\author{...}` and `\thanks{...}` blocks).
- [ ] **Unverified references.** Confirm the volume, issue and page details of 10 standard
  references against the publisher records. Their records were not re-checked in the project's
  literature pass:
  - roberts2017, giglio2016, hirsch1982, sen1968, benjamini1995, anselin1995;
  - breiman2001, phillips2006, delong1988, wang2021gradient.
- [ ] **Novelty check.** Run the journal's similarity check. The text was written fresh for this
  version: related work is paraphrased and cited, with no quoted passages.
- [ ] **Style.** The text uses no em-dashes or special symbols. En-dashes appear only in the page
  ranges of the bibliography, which is IEEE style.
- [ ] **Journal requirements.** Add a graphical abstract or highlights if the journal asks for
  them.
- [ ] **Map figure.** Fig. 8 uses the RF v2 relative score. The GeoTIFF is
  `results/final/maps/Susceptibility_RF_v2_score.tif`.
