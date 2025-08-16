import os
import sys
import pypandoc
from bs4 import BeautifulSoup
import re
import shutil
import urllib.parse

# O.R.G.A.N.O.N.I.Z.E.R.
#Obligatory Recursive Generator & Allocator of Navigable Output for Nearly Impossible Zero-Error Rendering
#
#    Conceived in the labyrinthine corridors of the Bureau of Technical Ornamentation, ORGANONIZER was designed to automate HTML-to-LaTeX conversion while maintaining “complete semantic fidelity and optimal typographic decorum.”
#
#    In practice, it behaves more like a fussy librarian with a soldering iron:
#
#        It reindexes tables according to a lunar calendar.
#
#        Adds footnotes about the existential inadequacy of unordered lists.
#
#        Occasionally refuses to process <div> tags unless offered a small JPEG of a potted fern.
#
#    Engineers report that the system has developed a self-referential awareness, frequently inserting passages about itself into converted documents. These are written in LaTeX, naturally, and formatted in an elegant Garamond.
#---------------------------------------------------------------------------

def check_pandoc():
    """Checks if Pandoc is installed and accessible."""
    try:
        pypandoc.get_pandoc_version()
        print("✅ Pandoc is installed.")
    except OSError:
        print("❌ Error: Pandoc not found.")
        print("Please install Pandoc from https://pandoc.org/installing.html and ensure it's in your system's PATH.")
        sys.exit(1)

def get_chapter_links(index_file):
    """
    Parses the index.html file to find links to chapter pages.
    """
    print(f"🔎 Parsing '{index_file}' for chapter links...")
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')
        
        links = soup.find_all('a', href=re.compile(r'.*\.html$'))
        chapter_files = []
        for link in links:
            href = link['href']
            if href != os.path.basename(index_file) and not href.startswith(('http:', 'https:', '#')):
                if href not in chapter_files:
                    chapter_files.append(href)

        if not chapter_files:
            print("⚠️ Warning: No chapter links found. Check your index.html structure.")
        else:
            print(f"👍 Found {len(chapter_files)} potential chapter files.")
        return chapter_files
    except FileNotFoundError:
        print(f"❌ Error: '{index_file}' not found.")
        return None

def convert_html_to_latex(html_file_path, output_dir, input_dir, copied_images):
    """
    Converts a single HTML file to LaTeX, finds and copies its images,
    and updates image paths for LaTeX.
    """
    html_filename = os.path.basename(html_file_path)
    print(f"   - Converting '{html_filename}'...")
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')

        # --- Extract Chapter Title ---
        title_tag = soup.find('h1')
        chapter_title = title_tag.get_text(strip=True) if title_tag else soup.title.string
        chapter_title = re.sub(r'[&%$#_{}]', r'\\\g<0>', chapter_title)

        # --- Extract Main Content ---
        content_div = soup.find(id='main-content')
        if not content_div:
            print(f"     ⚠️ Warning: Content container with id='main-content' not found in '{html_filename}'. Using entire <body>.")
            content_div = soup.body
        
        # --- NEW: Find, Copy, and Update Image Paths ---
        images = content_div.find_all('img')
        for img in images:
            src = img.get('src')
            if not src or 'attachments' not in src:
                continue

            # URL Decode the src in case of spaces etc. (%20)
            src_decoded = urllib.parse.unquote(src)
            image_filename = os.path.basename(src_decoded)
            
            # The source image path is inside the global attachments folder
            source_image_path = os.path.join(input_dir, 'attachments', image_filename)
            dest_image_path = os.path.join(output_dir, image_filename)

            if os.path.exists(source_image_path):
                if image_filename not in copied_images:
                    shutil.copy2(source_image_path, dest_image_path)
                    copied_images.add(image_filename)
                    print(f"       -> Copied attachment: '{image_filename}'")
                
                # Update the src in the HTML to be just the filename, so Pandoc
                # creates a clean \includegraphics{filename.png} command.
                img['src'] = image_filename
            else:
                print(f"     ⚠️ Warning: Image attachment not found at '{source_image_path}'. Skipping copy.")

        # --- Convert to LaTeX using Pandoc ---
        html_content = str(content_div)
        extra_args = ['--wrap=none', '--toc-depth=3']
        latex_content = pypandoc.convert_text(html_content, 'latex', format='html', extra_args=extra_args)

        # --- Write the .tex file ---
        base_name = os.path.splitext(html_filename)[0]
        safe_base_name = re.sub(r'[^a-zA-Z0-9_-]', '', base_name)
        tex_filename = f"{safe_base_name}.tex"
        tex_filepath = os.path.join(output_dir, tex_filename)

        with open(tex_filepath, 'w', encoding='utf-8') as f:
            f.write(f"% Converted from {html_filename}\n")
            f.write(f"\\chapter{{{chapter_title}}}\n\n")
            f.write(latex_content)
        
        print(f"     ✅ Successfully created '{tex_filepath}'")
        return tex_filename

    except FileNotFoundError:
        print(f"     ❌ Error: Chapter file '{html_filename}' not found. Skipping.")
        return None
    except Exception as e:
        print(f"     ❌ An error occurred while converting '{html_filename}': {e}")
        return None

def create_main_latex_file(chapter_tex_files, output_dir):
    """
    Generates the main .tex file that includes all the converted chapter files.
    """
    main_file_path = os.path.join(output_dir, 'main.tex')
    print(f"\n✍️ Creating main LaTeX file at '{main_file_path}'...")
    
    preamble = r"""
\documentclass[12pt, a4paper]{report}

% --- PACKAGES ---
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{geometry}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage[T1]{fontenc} % For better character encoding

% --- SET GRAPHICS PATH ---
% Tells LaTeX to look for images in the current directory
\graphicspath{ {./} }

% --- PAGE LAYOUT ---
\geometry{a4paper, margin=1in}

% --- HYPERLINK SETUP ---
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=cyan,
    pdftitle={My Confluence Document},
    pdfpagemode=FullScreen,
    breaklinks=true % Allows links to break across lines
}

\title{Documentation Exported from Confluence}
\author{Your Name}
\date{\today}

\begin{document}

\maketitle
\tableofcontents
\newpage
"""
    content = preamble
    for tex_file in chapter_tex_files:
        content += f"\\input{{{os.path.splitext(tex_file)[0]}}}\n"
    content += "\n\\end{document}\n"

    with open(main_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"👍 Main file 'main.tex' created successfully.")

def main():
    """Main function to orchestrate the conversion process."""
    print("--- Confluence HTML to LaTeX Converter ---")
    
    # --- NEW: Get input directory from command line argument ---
    if len(sys.argv) < 2:
        print("❌ Usage: python convert_to_latex.py <path_to_confluence_export_directory>")
        print("   Example: python convert_to_latex.py SAF")
        sys.exit(1)
        
    input_dir = sys.argv[1]
    if not os.path.isdir(input_dir):
        print(f"❌ Error: Input directory '{input_dir}' not found.")
        sys.exit(1)

    # --- NEW: Define output directory based on input ---
    output_dir = f"{os.path.basename(os.path.normpath(input_dir))}.tex"
    
    check_pandoc()

    index_file_path = os.path.join(input_dir, 'index.html')
    chapter_html_files = get_chapter_links(index_file_path)
    if chapter_html_files is None:
        return

    if os.path.exists(output_dir):
        print(f"'{output_dir}' already exists. Clearing it before proceeding.")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    print(f"📂 Created output directory: '{output_dir}'")

    print("\n🚀 Starting conversion of chapter files...")
    converted_tex_files = []
    copied_images = set() # To avoid copying the same image multiple times
    for html_file in chapter_html_files:
        full_html_path = os.path.join(input_dir, html_file)
        tex_file = convert_html_to_latex(full_html_path, output_dir, input_dir, copied_images)
        if tex_file:
            converted_tex_files.append(tex_file)
    
    if not converted_tex_files:
        print("\nNo files were converted. Exiting.")
        return

    create_main_latex_file(converted_tex_files, output_dir)

    print("\n🎉 --- Conversion Complete! --- 🎉")
    print(f"Your LaTeX project is ready in the '{output_dir}' directory.")
    print(f"To compile, open '{os.path.join(output_dir, 'main.tex')}' in a LaTeX editor and compile (e.g., using pdfLaTeX).")

if __name__ == '__main__':
    main()
