# atomfind

Finds the atoms in a 3-D electron-ptychographic reconstruction (lead, titanium and oxygen in a
PbTiO₃/SrTiO₃ superlattice), gives every coordinate a calibrated uncertainty, and derives the
local polarisation from them. This is the code behind the PX915 report; how it works is in
[METHODS.md](METHODS.md).

## Reproducing the report's result

The result in the report's Appendix E is the set of located atoms with a 95 % interval on every
coordinate, and the in-plane polarisation derived from them. The input reconstruction is in this
repository, so there is nothing else to download. The run takes a few minutes on one CPU core and
needs no GPU.

```bash
git clone https://github.com/tristanmccarthy55/atomfind.git
cd atomfind
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt

python atomfind/test_atomfind.py                                   # expect 17/17 passed, ~1 s
python atomfind/run_atomfind.py --preset NL70_coherent --out ./out
python atomfind/polarisation.py --out ./out
```

Run the tests first. They need no data, so if they pass and a number below still differs, the
disagreement is real. [INSTALL.md](INSTALL.md) covers requirements, the output files, running on
your own reconstruction, and troubleshooting.

### What you should get

The run is deterministic, so these numbers are exact:

| quantity | expected |
|---|---|
| atoms found | 1834 |
| precision | 0.97 |
| bulk recall, Pb / Ti / O | 95.6 / 96.4 / 95.5 % |
| axially overlapped oxygen | 82 % |
| species confusion | 1.1 % |
| in-plane / depth RMS accuracy | 0.032 / 0.37 Å |
| coverage of the 95 % interval | 96 % |
| in-plane polarisation error (median) | 0.007 Å, 0.9° |
| propagated σ on the along-beam component | 0.237 Å |

The uncertainty matters more than the coordinates. Typical 95 % half-widths are 0.02 Å in-plane
and 0.5 Å in depth, and they vary from atom to atom, so propagate the per-atom interval in
`found_atoms.csv` rather than a single global figure.

**Tolerances.** The only random step is the Monte-Carlo propagation in `polarisation.py`, which is
seeded. Changing `--seed` moves the along-beam σ by about 0.001 Å and the polarisation coverages
by about one percentage point. Groups of fewer than ~20 atoms show a few points of coverage noise
and should not be read as failures.

**Two failure modes you should see.** Both are reported in the output, not hidden. About 28 % of
titanium do not get a complete oxygen cage and are left out of the polarisation map. About 5 %
get a cage of the wrong composition: their in-plane error has a median of 0.45 Å, and the
interval covers only 12 % of them, because the intervals assume the atoms were detected
correctly.

If a number differs, first check the inputs with
`cd atomfind/data && shasum -a 256 -c SHA256SUMS` (on Linux, `sha256sum -c SHA256SUMS`). If all
four report `OK`, please tell me.

## Data

All four inputs are in `atomfind/data/` (45 MB):

| file | what |
|---|---|
| `NL70_phase.npz` | the reconstruction, (70, 404, 404), stored as its phase |
| `psf_Pb_NL70_vol.npy`, `psf_Ti_NL70_vol.npy` | measured single-atom responses for lead and titanium |
| `gt_prepared.npz` | the reference structure, used only for scoring |

Nothing downstream uses the modulus of the reconstruction, so storing only the phase is exact,
not a compression. The atom finding never sees the reference structure. It is used afterwards,
to put the atoms in the model's frame and to score them.
