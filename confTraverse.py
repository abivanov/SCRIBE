# confluence_page_traverser.py

# This script traverses a Confluence site starting from a given page URL.
# It lists all child pages, saves the HTML content of each page, and
# downloads all associated attachments.

# --- Prerequisites ---
# 1. Install the required Python libraries:
#    pip install atlassian-python-api requests
#
# 2. Generate a Confluence API Token:
#    - Log in to your Confluence instance.
#    - Go to your profile picture > Settings > Password > API tokens.
#    - Create a new token and give it a label (e.g., "Python Script").
#    - Copy the token. You will not be able to see it again.

import os
import re
import requests
from getpass import getpass
from atlassian import Confluence
from urllib.parse import unquote, urljoin

from LatexWriter import LatexWriter

import pypandoc

from confluence_auth import read_config, get_confluence_client


def parse_confluence_url(url):
    """
    Parses a Confluence URL to extract the space key and page title.
    Handles both standard and "pretty" URLs.
    """
    try:
        # Example URL: /display/SPACEKEY/Page+Title
        match = re.search(r'/display/([^/]+)/([^/?]+)', url)
        if match:
            space_key = match.group(1)
            # URL encoding replaces spaces with '+', so we decode it
            page_title = unquote(match.group(2)).replace('+', ' ')
            return space_key, page_title
        else:
            print("Error: Could not parse the space key and page title from the URL.")
            print("Please ensure it's a valid Confluence page URL.")
            return None, None
    except Exception as e:
        print(f"An error occurred while parsing the URL: {e}")
        return None, None

def convert_confluence_images(html_content):
    """
    Converts Confluence-style image tags to standard HTML <img> tags using regex.

    This function finds all occurrences of the pattern:
    <ac:image ac:title="..." ac:alt="..."><ri:attachment ri:filename="..." /></ac:image>
    and replaces them with:
    <img src="..." alt="..." title="...">

    Args:
        html_content (str): A string containing the HTML content to process.

    Returns:
        str: The processed HTML content with standard <img> tags.
    """
    # Regex to find the Confluence image tag and capture the necessary parts.
    # It captures three groups:
    # 1. The value of ac:title
    # 2. The value of ac:alt
    # 3. The value of ri:filename
    # The pattern uses `.*?` (non-greedy) to handle other potential attributes
    # within the tags without breaking the match.
    pattern = re.compile(
        r'<ac:image.*?ac:title="([^"]+)".*?ac:alt="([^"]+)".*?>'  # Start of <ac:image> and capture title/alt
        r'\s*<ri:attachment.*?ri:filename="([^"]+)".*?/>\s*'      # The inner <ri:attachment> and capture filename
        r'</ac:image>',                                          # The closing </ac:image>
        re.DOTALL  # Allows '.' to match newlines, in case the tag is split across lines
    )

    # The replacement string uses backreferences to the captured groups.
    # \g<3> is the filename (src)
    # \g<2> is the alt text (alt)
    # \g<1> is the title (title)
    replacement_html = r'<img src="\g<3>" alt="\g<2>" title="\g<1>">'

    # Use re.sub() to find all matches and replace them.
    converted_content = pattern.sub(replacement_html, html_content)

    return converted_content

def sanitize_filename(filename):
    """Removes characters that are invalid for filenames."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def save_page_content(page, output_dir):
    """Saves the HTML content of a page to a file."""
    try:
        page_title = page['title']
        # Sanitize the title to create a valid filename
        filename = sanitize_filename(page_title) + ".tex"
        filepath = os.path.join(output_dir, filename)
        
        # The HTML content is in the 'storage' format
        html_content1 = page['body']['storage']['value']

        html_content = convert_confluence_images(html_content1)

        try:
            # Use pypandoc to convert the HTML string to LaTeX.
            # The 'string' format for the input and 'latex' for the output
            # ensures we get a plain LaTeX string, not a full document.
            # This will also handle things like HTML tables, lists, and headings.
            latex_content = pypandoc.convert_text(
                html_content,
                'latex',
                format='html',
                extra_args=['--wrap=none']  # Prevents long lines from wrapping
            )
        except Exception as e:
            # Handle potential errors, such as pandoc not being installed or found.
            print(f"An error occurred during conversion: {e}" )
            return
        
        latex_content = latex_content.replace("keepaspectratio", r"width=0.9\textwidth")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        print(f"    - Saved LaTex to {filepath}")

        return( filename )

    except Exception as e:
        print(f"    - Error saving HTML content for page '{page.get('title', 'N/A')}': {e}")

def save_page_attachments(confluence, page_id, output_dir, auth_cfg):
    """Downloads and saves all attachments for a given page."""
    try:
        # Create a dedicated directory for attachments if it doesn't exist
        attachments_dir = os.path.join(output_dir, "attachments")
        os.makedirs(attachments_dir, exist_ok=True)
        
        attachments = confluence.get_attachments_from_content(page_id, start=0, limit=200)
        
        if not attachments['results']:
            return # No attachments to download

        print(f"    - Found {len(attachments['results'])} attachment(s). Downloading...")
        for attachment in attachments['results']:
            attachment_title = attachment['title']
            download_url = urljoin(confluence.url, attachment['_links']['download'])
            
            # Use the authenticated session from the confluence object to download
            # print(download_url) 
            
            # There probably some bug in the Confluence implemntation: SSL certificate doesn't get sent 
            # Resorting to using requests directly
            #response = confluence.session.get(download_url)
            #response.raise_for_status() # Raise an exception for bad status codes
            
            
            # Prepend page_id to filename to avoid name conflicts
            # filename = f"{page_id}_{sanitize_filename(attachment_title)}"
            filename = sanitize_filename(attachment_title)
            filepath = os.path.join(attachments_dir, filename)
            
            token = auth_cfg['TOKEN']
            cert_path = auth_cfg['CERTIFICATE']  # Assuming the certificate path is in the config

            response = requests.get(
                download_url,
                headers={"Authorization": f"Bearer {token}"},
                verify=cert_path,
                stream=True
            )

            response.raise_for_status()
            # print( response.status_code)
        
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"      - Downloaded '{attachment_title}' to {filepath}")

    except requests.exceptions.HTTPError as e:
        print(f"    - HTTP Error downloading attachments for page {page_id}: {e}")
    except Exception as e:
        print(f"    - General Error downloading attachments for page {page_id}: {e}")

def process_page_and_children(confluence, page_id, level, output_dir, auth_cfg, latex_writer):
    """
    Processes a given page (prints info, saves content/attachments)
    and then recursively does the same for all its children.
    """
    try:
        # Expand 'body.storage' to get the HTML content
        page = confluence.get_page_by_id(page_id, expand="body.storage")
        if not page:
            print(f"Could not retrieve details for page ID {page_id}. Skipping.")
            return
    except Exception as e:
        print(f"Error getting page details for ID {page_id}: {e}. Skipping.")
        return

    page_title = page['title']
    
    # Define the hierarchical labels
    levels = ["Document", "chapter", "section", "subsection", "subsubsection"]
    indent = "  " * level
    
    if level < len(levels):
        level_label = levels[level]
    else:
        level_label = f"{levels[-1]}-{level - len(levels) + 2}"
    
    # Print the formatted page information
    if level == 0:
        print(f"Processing Root Page: {page_title}")
    else:
        print(f"{indent}- {level_label}: {page_title}")
        latex_writer.write_text(f"\\{level_label}{{{page_title}}}")

    # Save the page's HTML content
    filename = save_page_content(page, output_dir)
    latex_writer.write_text(f"\\input{{{filename}}}")

    # Download and save the page's attachments
    save_page_attachments(confluence, page_id, output_dir, auth_cfg)

    # --- Recurse for child pages ---
    try:
        child_pages = confluence.get_child_pages(page_id)
        for child in child_pages:
            process_page_and_children(confluence, child['id'], level + 1, output_dir, auth_cfg, latex_writer)
    except Exception as e:
        print(f"{indent}Error retrieving child pages for '{page_title}': {e}")

    
if __name__ == "__main__":
    # Also alternatively take configuration file from the command line 
    confluence_cfg, auth_cfg = read_config()

    # Should be actually taken from the command line arguments
    # Initialize Confluence client once
    confluence = get_confluence_client(confluence_cfg, auth_cfg)
    # Create a root directory for the export
    export_dir = "confluence_export"

    start_page_url = "https://confluence.tii.ae/display/SAF/Project+Management+Plan"
    start_page_url = "https://confluence.tii.ae/display/SAF/System+Engineering+Plan"
    space_key, page_title = parse_confluence_url(start_page_url)

    print( space_key, ":",  page_title)


    if not space_key or not page_title:
        print("Invalid Confluence URL. Please check the format and try again.")   
        exit() 

    try:
        print(f"\nFetching starting page ID for '{page_title}' in space '{space_key}'...")
        start_page_id = confluence.get_page_id(space_key, page_title)
        
        if not start_page_id:
            print(f"Error: Could not find a page with title '{page_title}' in space '{space_key}'.")
            exit()

        print(f"Successfully found page ID: {start_page_id}")
        
        # Create a root directory for the export
        export_dir = "confluence_export"
        os.makedirs(export_dir, exist_ok=True)
        print(f"All content will be saved in the '{export_dir}' directory.")
        
        print("----Creating main LaTeX file...")
        # Initialize the LatexWriter
        latex_writer = LatexWriter(export_dir = export_dir)
        print("\n--- Traversing Site and Exporting Content ---")
        process_page_and_children(confluence, start_page_id, 0, export_dir, auth_cfg, latex_writer)
        print("\n--- Export Complete! ---")

        # Finalize the main LaTex Document 
        latex_writer.close()

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
