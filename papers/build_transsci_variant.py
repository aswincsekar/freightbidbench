"""Derive the Transportation Science submission variant from the
canonical v0.4 methods paper.

INFORMS submission format: 1.5-spaced, >=11pt, 1-inch margins, single
column, no footnotes. The canonical tex is single-spaced with one
\\thanks footnote on the title; this script patches both at build time
so the two versions cannot drift.

Usage: python3 build_transsci_variant.py <in.tex> <out.tex>
"""

import re
import sys


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    tex = open(src).read()

    # 1.5 spacing (setspace's \onehalfspacing).
    anchor = "\\usepackage{microtype}"
    if anchor not in tex:
        raise SystemExit("anchor package line not found")
    tex = tex.replace(
        anchor, anchor + "\n\\usepackage{setspace}\n\\onehalfspacing", 1
    )

    # Drop the title \thanks footnote (INFORMS: no footnotes); its
    # content moves to the head of the Reproducibility appendix.
    m = re.search(r"\\thanks\{.*?\}\}", tex, re.S)
    if not m:
        raise SystemExit("title \\thanks not found")
    tex = tex.replace(m.group(0), "}", 1)

    repro = "\\section{Reproducibility}\n\\label{sec:repro}\n"
    if repro not in tex:
        raise SystemExit("reproducibility section not found")
    tex = tex.replace(
        repro,
        repro
        + "\nEvaluation artifact: FreightBidBench (contracts "
        + "\\texttt{freightbidbench-v0.4-dev} and \\texttt{-v0.4.1}), "
        + "release \\texttt{v0.4.2},\n"
        + "\\url{https://github.com/aswincsekar/freightbidbench}. All\n"
        + "values in the paper reproduce from the commands below.\n",
        1,
    )

    open(dst, "w").write(tex)
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
