import os 

class LatexWriter:
    def __init__(self, filename="main.tex", export_dir="."):
        """
        Parameters:
        filename   : str, name of the LaTeX file (default: main.tex)
        export_dir : str, directory where the file will be stored (default: current directory)
        """
        self.export_dir = os.path.abspath(export_dir)
        # os.makedirs(self.export_dir, exist_ok=True)  # ensure directory exists
        self.filename = os.path.join(self.export_dir, filename)

        self.file = open(self.filename, "w", encoding="utf-8")
        self._write_preamble()
    
    def _write_preamble(self):
        preamble = r"""\documentclass[12pt,a4paper]{report}
\usepackage{TII_style}

\title{Minimal Example Document}
\author{Author Name}
\date{\today}

\begin{document}

\maketitle

\tableofcontents
"""
        self.file.write(preamble + "\n")
    
    def write_text(self, text: str):
        """Write arbitrary LaTeX text to the file."""
        self.file.write(text + "\n")
    
    def close(self):
        """Finish the LaTeX document and close the file."""
        self.file.write("\n\\end{document}\n")
        self.file.close()
