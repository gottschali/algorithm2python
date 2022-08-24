#!/usr/bin/env python3
import tempfile
from pathlib import Path


header = r"""
\documentclass{article}
\usepackage{algorithm2e}
\usepackage[usenames]{color}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage[utf8]{inputenc}
\usepackage[OT1]{fontenc}
\pagestyle{empty}             % do not remove
\begin{document}
\begin{algorithm}
"""
footer = r"""
\end{algorithm}
\end{document}"
"""

"""
         ("latex" "dvipng")
         :description "dvi > png" :message "you need to install the programs: latex and dvipng." :image-input-type "dvi" :image-output-type "png" :image-size-adjust
         (1.0 . 1.0)
         :latex-compiler
         ("latex -interaction nonstopmode -output-directory %o %f")
         :image-converter
         ("dvipng -D %D -T tight -o %O %f")
         :transparent-image-converter
         ("dvipng -D %D -T tight -bg Transparent -o %O %f"))
"""


def main():
    print(header)
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(Path(tmpdir) / "temp.tex", "w") as f:
            # f.write(header)
            try:
                while line := input():
                    print(line)
                    # f.write(line)
            except EOFError:
                pass
    print(footer)


if __name__ == "__main__":
    main()
