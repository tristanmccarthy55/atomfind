# Installation and run guide

From nothing to reproduced atomic positions in about five minutes. No GPU, no MATLAB, no
separate data download — the example reconstruction ships in this repository.

---

## 1. What you need

| | |
|---|---|
| Python | **3.10 or newer** (3.9 works; see the note at the end) |
| Disk | ~200 MB (45 MB repository, the rest the virtual environment) |
| Time | ~1 s for the tests, ~5 min for the full run |
| Not needed | GPU, MATLAB, abtem, scikit-image, an internet connection after cloning |

## 2. Install

```bash
git clone https://github.com/<user>/atomfind.git
cd atomfind

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Five dependencies: numpy, scipy, h5py, matplotlib, ase.

## 3. Check the install (1 second)

```bash
python atomfind/test_atomfind.py
```

Expect `== 17/17 passed ==`. These run on synthetic data and need none of the example
volume, so they separate an environment problem from a genuine disagreement with the numbers
below. **If they fail, stop here** — nothing downstream will be meaningful.

## 4. Extract the atomic positions (~5 minutes)

```bash
python atomfind/run_atomfind.py --preset NL70_coherent --out ./out
python atomfind/polarisation.py --out ./out
```

The first fits the reconstruction as a superposition of the measured single-atom response and
writes the atoms; the second turns them into the local polarisation. Run both from the
repository root, the directory that contains `atomfind/`.

## 5. What you get

```
out/found_atoms.csv        every atom: element, x/y/z in A, 95% interval per axis,
                           model sigma, species confidence, lattice-constrained flag
out/found_atoms.extxyz     the same as an ASE object — opens in OVITO or VESTA
out/report.json            every score in this table, machine-readable
out/uq_conformal.json      the calibration table
out/polarisation.json      Ti-O6 off-centring with propagated uncertainty
out/*.png                  detection overlay, depth accuracy, ROC, kernel comparison
```

Check these against the run:

| quantity | expected |
|---|---|
| atoms found | 1834 |
| precision | 0.97 |
| bulk recall Pb / Ti / O | 95.6 / 96.4 / 95.5 % |
| axially overlapped oxygen | 82 % |
| species confusion | 1.1 % |
| in-plane RMS accuracy | 0.032 Å |
| depth RMS accuracy | 0.37 Å |
| in-plane polarisation error | 0.007 Å, 0.9° |
| propagated sigma, along beam | 0.237 Å |

The run is deterministic: on this input those numbers are exact, not approximate. Tolerances
and the two expected failure modes are in [PEER.md](PEER.md).

## 6. Running it on your own reconstruction

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

## 7. Where the data lives

Data files are resolved by **name**, never by an absolute path, searching in order:
`$ATOMFIND_DATA` (or `--data-dir`) → `atomfind/data/` → `~/Desktop`. A missing file raises with
the name it wanted and the full search path. Outputs go to `$ATOMFIND_OUT`, else `./atomfind_out`,
overridden by `--out`.

Shipped in `atomfind/data/` (45 MB):

| file | what |
|---|---|
| `NL70_phase.npz` | the reconstruction, as a compressed float32 phase array |
| `psf_Pb_NL70_vol.npy`, `psf_Ti_NL70_vol.npy` | the measured single-atom responses |
| `gt_prepared.npz` | the reference structure, in the beam frame — **scoring only** |

The phase archive is bit-identical to the complex volume it came from (`np.angle` of a
complex64 array returns float32 in any case, and nothing here uses the modulus) at less than
half the size. `python -m atomfind.make_example_data --check` verifies it against the source.

## 8. If something goes wrong

| symptom | cause |
|---|---|
| `FileNotFoundError` naming a data file | wrong working directory, or use `--data-dir` |
| thousands of `RuntimeWarning: ... in matmul` | scipy < 1.15 on Python 3.9; harmless, results are identical to 1e-11. Use Python 3.10+ to silence it |
| tests pass but the numbers differ | a real disagreement — please report it |
| `species confusion NN% > 5%` warning | expected on your own data if `--dz` is wrong |

## 9. What is and is not blind

The atom finding uses **no ground truth**: it fits the reconstruction and returns positions,
species and per-atom intervals from the data alone. The reference structure enters only
afterwards, to place the atoms in the model's frame and to score recall, precision and
coverage. Delete it and you still get atomic positions with uncertainties, in the
reconstruction's own frame.
