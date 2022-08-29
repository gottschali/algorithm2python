#!/usr/bin/env python3

# TODO make configurable
options = "linesnumbered,lined,boxed,commentsnumbered"

header = (
    r"\documentclass{article}"
    + r"\usepackage["
    + options
    + "]{algorithm2e}"
    + r"""
\usepackage{minted}
\usepackage{paracol}
\usepackage[usenames]{color}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage[utf8]{inputenc}
\usepackage[OT1]{fontenc}
% \pagestyle{empty}
\columnratio{0.55} % Set the left/right column width ratio to 6:4.
\usepackage{geometry}
\geometry{left=3.0cm,right=3.0cm,top=1.0cm,bottom=1.0cm,columnsep=1.0cm}
\title{Python2Algorithm}
\author{Ali G.}
\begin{document}
\maketitle
\begin{paracol}{2}
"""
)
footer = r"""
\end{paracol}
\end{document}
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
    try:
        print(r"\begin{algorithm}")
        while line := input():
            print(line)
    except EOFError:
        pass
    finally:
        print(r"\end{algorithm}")
    print(r"\switchcolumn")
    print(r"\inputminted{python3}{src/sample/bench.py}")
    print(footer)


if __name__ == "__main__":
    main()
