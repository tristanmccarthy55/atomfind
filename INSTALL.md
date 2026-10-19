# Install notes and further use

The commands and the expected numbers are in the [README](README.md). This file covers what it
leaves out.

## Requirements

| | |
|---|---|
| Python | 3.10 or newer (3.9 works; see Troubleshooting) |
| Packages | numpy, scipy, h5py, matplotlib, ase (`requirements.txt`) |
| Disk | ~200 MB, most of it the virtual environment |
| Not needed | GPU, MATLAB, abtem, an internet connection after cloning |

On Windows, activate the environment with `venv\Scripts\activate`.

## Output files

```
out/found_atoms.csv        every atom: element, x/y/z in Å, 95% interval per axis,
                           model σ, species confidence, lattice-constrained flag
out/found_atoms.extxyz     the same as an ASE object; opens in OVITO or VESTA
out/report.json            every score, machine-readable
out/uq_conformal.json      the calibration table
out/polarisation.json      Ti–O6 off-centring with propagated uncertainty (+ .npz)
out/*.png                  detection overlay, depth accuracy, ROC, kernel comparison
```

## Running it on your own reconstruction

```bash
python atomfind/run_atomfind.py --recon /path/to/Niter200.mat --dz 0.666 --out ./out
```

`--recon` takes a PtychoShelves `Niter<N>.mat` directly, an extracted `.npy`, or a phase
`.npz`. Two things will not carry over from the shipped example, and both matter:

- **`--dz`, the depth spacing.** It sets the depth registration, and titanium and oxygen
  alternate every 1.95 Å, so a wrong value swaps species labels wholesale instead of failing.
- **The single-atom kernel** is the forward model being inverted and belongs to the
  reconstruction it was measured from. The shipped one against a different reconstruction of
  the same specimen drops lead recall 86 → 75 % and oxygen 59 → 26 %. Supply a matched one
  with `--single-atom-vol`, or measure one using `extract_psf.py`.

Scoring against the bundled reference structure is meaningless for a different specimen, but
the atoms and their uncertainties are still written.

## Where files are looked for

Data files are found by name, never by an absolute path, searching in order: `$ATOMFIND_DATA`
(or `--data-dir`), then `atomfind/data/`, then `~/Desktop`. A missing file raises with the name
it wanted and the full search path. Outputs go to `$ATOMFIND_OUT`, else `./atomfind_out`,
overridden by `--out`.

## Troubleshooting

| symptom | cause |
|---|---|
| `FileNotFoundError` naming a data file | wrong working directory; run from the repository root, or use `--data-dir` |
| thousands of `RuntimeWarning: ... in matmul` | scipy < 1.15 on Python 3.9; harmless, results are identical to 1e-11. Use Python 3.10+ to silence it |
| tests pass but the numbers differ | check the inputs with `SHA256SUMS` (see README); if they are intact, it is a real disagreement, please report it |
| `species confusion NN% > 5%` warning | expected on your own data if `--dz` is wrong |
