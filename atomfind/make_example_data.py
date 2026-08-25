#!/usr/bin/env python
"""@file make_example_data.py
@brief Build the in-repo example data from the full-size source volumes.

The reconstruction ships as a compressed float32 PHASE archive rather than the complex object.
Nothing downstream uses the modulus, and `np.angle` of a complex64 array returns float32
anyway, so this is bit-identical to shipping the complex volume (verified: max |difference|
= 0) at less than half the size -- small enough to live in the repository, so reproducing the
published result needs a clone and nothing else.

    python -m atomfind.make_example_data            # writes atomfind/data/
    python -m atomfind.make_example_data --check    # verify the archive against the source
"""
from __future__ import annotations
import argparse
import os

import numpy as np

from . import config

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")


def _phase_of(path):
    v = np.load(path)
    return np.angle(v).astype(np.float32) if np.iscomplexobj(v) else v.astype(np.float32)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    src = config.data_path("NL70_new_vol.npy", required=True)
    dst = os.path.join(OUT, "NL70_phase.npz")
    if a.check:
        ref = _phase_of(src)
        with np.load(dst) as d:
            got = d["phase"]
        assert got.shape == ref.shape, f"{got.shape} != {ref.shape}"
        worst = float(np.abs(got.astype(float) - ref.astype(float)).max())
        assert worst == 0.0, f"archive differs from source by up to {worst:.3e}"
        print(f"example archive matches the source volume exactly ({got.shape}, max diff 0)")
        return

    np.savez_compressed(dst, phase=_phase_of(src))
    print(f"  {os.path.basename(dst):24s} {os.path.getsize(dst)/1e6:6.1f} MB   reconstruction (phase)")
    for name in ("psf_Pb_NL70_vol.npy", "psf_Ti_NL70_vol.npy"):
        s = config.data_path(name, required=True)
        d = os.path.join(OUT, name)
        if os.path.abspath(s) != os.path.abspath(d):
            np.save(d, np.load(s))
        print(f"  {name:24s} {os.path.getsize(d)/1e6:6.1f} MB   measured single-atom kernel")
    print(f"  {'gt_prepared.npz':24s} "
          f"{os.path.getsize(os.path.join(OUT,'gt_prepared.npz'))/1e6:6.1f} MB   reference structure")
    print(f"\ntotal {sum(os.path.getsize(os.path.join(OUT,f)) for f in os.listdir(OUT))/1e6:.1f} MB")


if __name__ == "__main__":
    main()
