#!/usr/bin/env python
"""@file make_pol_fig.py
@brief Figure for the polarisation result: Ti-O6 off-centring recovered from the located atoms.

  fig_polarisation.pdf -- (a) in-plane off-centring map (located atoms vs ground truth);
                          (b) recovered vs true delta_x;
                          (c) the same along the beam, where the propagated uncertainty
                              exceeds the entire spread of the component itself.

Run:  python atomfind/paper/make_pol_fig.py   (cwd analysis/)
Needs <out_dir>/polarisation.npz from atomfind/polarisation.py.
"""
from __future__ import annotations
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _panel(ax, lab, three_d=False, size=9):
    """Panel letter outside the axes, above and left of the title."""
    t = ax.text2D if three_d else ax.text
    t(-0.06, 1.30, lab, transform=ax.transAxes, ha="left", va="top",
      fontsize=size, clip_on=False)


HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from atomfind import config

FIGDIR = os.path.join(HERE, "figs")
os.makedirs(FIGDIR, exist_ok=True)
plt.rcParams.update({
    "font.size": 8.5, "font.family": "serif", "mathtext.fontset": "cm",
    "axes.linewidth": 0.7, "xtick.major.width": 0.7, "ytick.major.width": 0.7,
    "axes.labelsize": 9, "axes.titlesize": 9, "legend.fontsize": 7.5,
    "figure.dpi": 150, "savefig.dpi": 300,
})
REC, GT = "#2166ac", "#b0b4b8"
BAD = "#d6604d"
MIN_PER_COL = 3          # scored Ti needed before a column mean is drawn (see main())


def main(out_dir=None):
    cfg = config.preset("NL70_coherent")
    d = np.load(os.path.join(out_dir or cfg.out_dir, "polarisation.npz"))
    ti, A, B, sig, tail = d["ti"], d["delta"], d["delta_gt"], d["sigma"], d["tail"]

    fig = plt.figure(figsize=(6.6, 2.75), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1])

    # (a) in-plane off-centring map, averaged per atomic column so the texture is legible
    ax = fig.add_subplot(gs[0, 0])
    key = np.round(ti[:, :2] / 2.0).astype(int)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    # A column average over one or two atoms is not a column average: it carries the full
    # single-atom off-centring instead of the depth-cancelled mean, so it draws as a long
    # arrow with no partner wherever that one atom is a cage-error atom. Drop those columns.
    n_col = np.bincount(inv, minlength=inv.max() + 1)
    keep = np.where(n_col >= MIN_PER_COL)[0]
    P = np.array([[ti[inv == u, 0].mean(), ti[inv == u, 1].mean(),
                   A[inv == u, 0].mean(), A[inv == u, 1].mean(),
                   B[inv == u, 0].mean(), B[inv == u, 1].mean()]
                  for u in keep])
    # Columns the wrong-cage tail dominates are the only ones that visibly disagree, so mark
    # them in the same red panel (c) uses rather than letting them read as a general failure.
    bad = np.array([tail[inv == u].mean() > 0.5 for u in keep])
    print(f"[fig_pol] (a) {len(keep)} columns drawn of {len(n_col)} "
          f"({(n_col < MIN_PER_COL).sum()} with < {MIN_PER_COL} scored Ti dropped); "
          f"median |column mean| rec {np.median(np.hypot(P[:, 2], P[:, 3])):.3f} A, "
          f"gt {np.median(np.hypot(P[:, 4], P[:, 5])):.3f} A")

    ax.quiver(P[:, 0], P[:, 1], P[:, 4], P[:, 5], color=GT, angles="xy",
              scale_units="xy", scale=0.10, width=0.014, label="true")
    ax.quiver(P[~bad, 0], P[~bad, 1], P[~bad, 2], P[~bad, 3], color=REC, angles="xy",
              scale_units="xy", scale=0.10, width=0.006, label="located atoms")
    if bad.any():
        ax.quiver(P[bad, 0], P[bad, 1], P[bad, 2], P[bad, 3], color=BAD, angles="xy",
                  scale_units="xy", scale=0.10, width=0.006, label="cage error")
    print(f"[fig_pol] (a) {int(bad.sum())} column(s) dominated by the wrong-cage tail, "
          f"marked: {[f'({P[i,0]:.0f},{P[i,1]:.0f})' for i in np.where(bad)[0]]}")

    ax.set_xlabel("x (Å)"); ax.set_ylabel("y (Å)")
    ax.set_title("in-plane off-centring", fontsize=8.5); _panel(ax, "(a)", size=8.5)
    # square window centred on the data; the margin clears the longest drawn arrow
    _cx = 0.5 * (P[:, 0].min() + P[:, 0].max()); _cy = 0.5 * (P[:, 1].min() + P[:, 1].max())
    _arrow = np.hypot(P[:, 4], P[:, 5]).max() / 0.10
    _half = 0.5 * max(P[:, 0].ptp(), P[:, 1].ptp()) + _arrow + 0.5
    ax.set_xlim(_cx - _half, _cx + _half); ax.set_ylim(_cy - _half, _cy + _half)
    # square BOX (so all three panels share a height and their letters line up) with the
    # data limits free to keep the arrows undistorted
    ax.set_aspect("equal", adjustable="datalim"); ax.set_box_aspect(1)
    print(f"[fig_pol] (a) square window {2*_half:.1f} A, longest arrow {_arrow:.1f} A")
    # anchored 2% inside the axes so the frame can never straddle a spine
    ax.legend(loc="lower left", bbox_to_anchor=(0.02, 0.02), borderaxespad=0.0,
              framealpha=1.0, edgecolor="0.8", handlelength=1.0,
              handletextpad=0.4, borderpad=0.25, fontsize=6.8)

    # (b,c) recovered vs true, in-plane and along the beam
    for n, (k, lab, ttl) in enumerate([(0, r"$\delta_x$", r"(b) in-plane $\delta_x$"),
                                       (2, r"$\delta_z$", "(c) along beam")]):
        ax = fig.add_subplot(gs[0, 1 + n])
        lo, hi = -0.55, 0.55
        ax.plot([lo, hi], [lo, hi], color="0.6", lw=0.8, zorder=0)
        ax.errorbar(B[:, k], A[:, k], yerr=1.96 * sig[:, k], fmt="none",
                    ecolor="#c8d4e3", elinewidth=0.7, zorder=1)
        ax.scatter(B[~tail, k], A[~tail, k], s=5, color=REC, lw=0, zorder=2)
        ax.scatter(B[tail, k], A[tail, k], s=11, facecolor="none", edgecolor=BAD,
                   lw=0.7, zorder=3, label="cage error")
        r = np.corrcoef(A[:, k], B[:, k])[0, 1]
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.set_aspect("equal"); ax.set_box_aspect(1)
        ax.set_xlabel(f"true {lab} (Å)", labelpad=1)
        ax.set_ylabel(f"recovered {lab} (Å)", labelpad=1)
        ax.set_title(f"{ttl[4:]},  $r={r:.2f}$", fontsize=8.5); _panel(ax, ttl[:3], size=8.5)
        if n == 1:
            ax.legend(loc="lower right", bbox_to_anchor=(0.98, 0.02), borderaxespad=0.0,
                      framealpha=1.0, edgecolor="0.8", markerscale=1.1,
                      handletextpad=0.3, borderpad=0.3, fontsize=7)

    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIGDIR, f"fig_polarisation.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print("wrote fig_polarisation.pdf/.png")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Polarisation figure from polarisation.npz.")
    ap.add_argument("--out", default=None, help="directory holding polarisation.npz")
    main(ap.parse_args().out)
