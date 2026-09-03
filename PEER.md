# Peer reproduction — run this and see if you get my numbers

**The exercise: given a ptychographic reconstruction, extract the atomic positions — with a
calibrated uncertainty on each one.**

Everything you need is in this repository. Clone it, install five dependencies, run three
commands. No GPU, no MATLAB, no separate data download, about five minutes of compute.

[INSTALL.md](INSTALL.md) is the step-by-step guide. **This file is the protocol**: what the
inputs are, exactly which numbers you should get, how far they are allowed to drift, and the two
failure modes you are *supposed* to see so you don't mistake them for your own mistakes.

The simulation and the ptychographic reconstruction that produce the input volume need GPU
hours, so the reconstruction is supplied as computed. Everything after it is reproduced from
scratch — the whole point of the exercise is the step from a reconstructed volume to a list of
atoms.

**If something disagrees, please say so.** A disagreement that survives the test suite is a real
finding and I would rather hear it than not.

---

## 1. Inputs

All four ship in `atomfind/data/` — 45 MB, already in your clone, nothing to download.

| File | What it is | Size |
|---|---|---|
| `NL70_phase.npz` | **the ptychographic reconstruction** — the recovered object's phase, `(70, 404, 404)`, dz 0.999 Å, dx 0.0495 Å/px | 42 MB |
| `psf_Pb_NL70_vol.npy` | the measured single-lead-atom response: the forward model the fit inverts | 1.3 MB |
| `psf_Ti_NL70_vol.npy` | the measured single-titanium response, used for species discrimination | 1.3 MB |
| `gt_prepared.npz` | the reference structure, pre-transformed into the beam frame — **for scoring only** | 0.4 MB |

**Why the phase and not the complex object.** Nothing in the pipeline uses the modulus, and
`np.angle` of a complex64 array returns float32 in any case, so storing the phase as float32 is
*bit-identical* to storing the complex volume it came from — verified, maximum difference exactly
zero — at less than half the size. That is what lets the data live in the repository instead of
behind a download. `python -m atomfind.make_example_data --check` re-verifies it against the
full-size source if you have it.

**Your own reconstruction works too.** `--recon` takes a raw PtychoShelves `Niter<N>.mat` (read
via `outputs.object_roi`), an extracted `.npy`, or a phase `.npz`. See §6.

**What is and is not blind.** The atom finding uses no ground truth: it fits the volume as a
superposition of the measured single-atom response and returns positions, species and per-atom
intervals from the data alone. The reference structure enters only afterwards, and only twice —
to place the recovered atoms in the model's coordinate frame, and to score recall, precision and
coverage. Delete it and you still get atomic positions with uncertainties, in the
reconstruction's own frame.

Data files are found by **name**, never by an absolute path: `$ATOMFIND_DATA` or `--data-dir`,
then `atomfind/data/`, then `~/Desktop`. A missing file raises with the name it wanted and the
full search path.

## 2. Install and run

Use **Python 3.10 or newer** if you have it. The pipeline runs correctly on 3.9, but pip then
resolves scipy to 1.13, whose NNLS raises tens of thousands of spurious floating-point warnings
on this problem; the results are identical either way (checked: largest relative difference
across `report.json` is 1e-11, and no non-finite value reaches any export).

```bash
git clone https://github.com/tristanmccarthy55/atomfind.git
cd atomfind

python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt

python atomfind/test_atomfind.py                      # ~1 s, no data needed

python atomfind/run_atomfind.py --preset NL70_coherent --out ./out
python atomfind/polarisation.py --out ./out
```

Run from the directory that contains `atomfind/`. A few minutes on one core; no GPU.

**Run the test suite first.** It takes about a second, needs none of the data, and checks the
things that would otherwise make a disagreement with the numbers below ambiguous: that the data
resolver works, that the shipped ground-truth cache is intact, that the recon-to-model map
inverts, that peak detection recovers planted atoms, and that the conformal intervals hit their
nominal coverage. If those 17 pass and the numbers below still differ, the disagreement is real
and worth telling me about; if they fail, it is an environment problem on your side.

**To run it on your own reconstruction instead**, give it the reconstruction and its depth
spacing:

```bash
python atomfind/run_atomfind.py --recon /path/to/Niter200.mat --dz 0.666 --out ./out
```

Two things carry over from the shipped preset and will not be right for someone else's data:

- **`--dz`.** The depth spacing sets the registration, and Ti and O alternate every 1.95 Å, so a
  wrong value swaps species labels wholesale rather than failing loudly.
- **The single-atom kernel.** It is the forward model the fit inverts, and it belongs to the
  reconstruction it was measured from. Running the shipped NL70 kernel against a different
  reconstruction of the same specimen (105 layers, dz 0.666, dosed) drops lead recall from
  $86\%$ to $75\%$ and oxygen from $59\%$ to $26\%$ — nothing is broken, the model is simply
  wrong for that volume. Supply a matched one with `--single-atom-vol`, or measure one with
  `extract_psf.py`.

Scoring against the reference structure is meaningless for a different specimen, but
`found_atoms.csv` and the uncertainty export are still produced.

## 3. What you should get

`run_atomfind.py` writes `found_atoms.csv` (element, x/y/z in ångström in the reference frame,
per-axis 95% conformal half-widths, model σ, species confidence, and a flag marking
lattice-constrained detections), `found_atoms.extxyz`, `uq_conformal.json` and `report.json`.
`polarisation.py` writes `polarisation.json` / `.npz`.

The axially overlapped oxygen is the one to watch: it is the oxygen sitting 1.95 Å from a
titanium along the beam, inside the axial response, and the entire advantage of this method over
deconvolve-then-peak-pick lives in that population (82 % against 9–26 %). If any single number
disagrees, that is the informative one.

On this input the run is deterministic and should reproduce

| Quantity | Expected |
|---|---|
| atoms found | 1834 |
| precision | 0.97 |
| bulk recall, Pb / Ti / O | 95.6 / 96.4 / 95.5 % |
| axially overlapped oxygen | 82 % |
| species confusion | 1.1 % |
| in-plane RMS accuracy | 0.032 Å |
| depth RMS accuracy | 0.37 Å |
| in-plane polarisation error (median) | 0.007 Å, 0.9° |
| propagated σ on the along-beam component | 0.237 Å |

**The uncertainty is the point, not the coordinates.** The number that validates it is the
coverage: 96% of true errors fall inside the nominal 95% interval, per stratum, held out on a
50/50 split. Typical half-widths are 0.02 Å in-plane and 0.5 Å in depth, rising to 1.5 Å for
weak oxygen near the exit surface. They are strongly heteroscedastic, so propagate the
**per-atom** interval, never a global figure.

## 4. Tolerances

The only stochastic element is the conformal calibration split, which is seeded. Re-seeding
(`polarisation.py --seed N`) moves the per-stratum quantiles by under 5% and the coverage
figures by under one percentage point. Coverage is finite-sample, so a stratum with fewer
than ~20 atoms — the constrained-oxygen entrance band here — shows several percentage points
of conformal noise and should not be read as a failure.

## 5. Failure modes you are expected to see

These are reported, not absorbed, and both appear in the output:

- **~28% of bulk titanium do not acquire a complete oxygen cage.** They are excluded from the
  polarisation map rather than completed from the lattice.
- **~5% have a cage of the wrong composition.** Their in-plane error rises to a median of
  0.45 Å, and the positional interval covers only 12% of them. This is a *detection* failure,
  not a localisation failure: conformal intervals are conditional on correct detection. It is
  visible in the exported cage completeness and species confidence, not in the error bars.

If your numbers differ by more than the tolerances above, the most likely causes are a
truncated download (check `sha256sum -c SHA256SUMS`) or a different reference structure.
