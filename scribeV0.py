from atlassian import Confluence
import re
import configparser
import sys

#

# --- Function to read configuration ---
def read_config(config_file='scribe.cfg'):
    config = configparser.ConfigParser()
    try:
        config.read_file(open(config_file))
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        print("Please create 'scribe.cfg' with your Confluence URL, Space Key, and authentication details.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading configuration file '{config_file}': {e}")
        sys.exit(1)

    confluence_config = {}
    auth_config = {}

    try:
        # Read Confluence general settings
        confluence_config['URL'] = config.get('CONFLUENCE', 'URL').strip()
        confluence_config['SPACE_KEY'] = config.get('CONFLUENCE', 'SPACE_KEY').strip()

        # Determine authentication method
        if 'BEARER_TOKEN_AUTH' in config:
            auth_config['TYPE'] = 'BEARER'
            auth_config['TOKEN'] = config.get('BEARER_TOKEN_AUTH', 'TOKEN').strip()
        elif 'BASIC_AUTH' in config:
            auth_config['TYPE'] = 'BASIC'
            auth_config['USERNAME'] = config.get('BASIC_AUTH', 'USERNAME').strip()
            auth_config['API_TOKEN'] = config.get('BASIC_AUTH', 'API_TOKEN').strip()
        else:
            print("Error: No authentication section found in 'scribe.cfg'.")
            print("Please add either [BEARER_TOKEN_AUTH] or [BASIC_AUTH] section.")
            sys.exit(1)

    except configparser.NoSectionError as e:
        print(f"Error: Missing section in 'scribe.cfg': {e}")
        print("Ensure you have [CONFLUENCE] and an authentication section ([BEARER_TOKEN_AUTH] or [BASIC_AUTH]).")
        sys.exit(1)
    except configparser.NoOptionError as e:
        print(f"Error: Missing option in 'scribe.cfg': {e}")
        print("Please check all required keys are present (URL, SPACE_KEY, TOKEN/USERNAME, API_TOKEN).")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing configuration from 'scribe.cfg': {e}")
        sys.exit(1)

    return confluence_config, auth_config


text_description = """
# Blalahdfha
This is the main description for Project Apollo. It outlines the overall vision
and high-level goals.
## 1.1 Project Goals
Our primary goal is to land a human on the Moon and return them safely to Earth
before the end of the decade. We aim to achieve this through rigorous testing
and innovative engineering.
"""

# --- Function to parse the text description ---
def parse_description(text):
    pages = []
    # Regex to find Markdown headings:
    matches = re.findall(r"^(#+)\s*(.*?)\n(.*?)(?=\n#+|\Z)", text, re.MULTILINE | re.DOTALL)

    for match in matches:
        heading_hashes = match[0] # e.g., "#", "##"
        level = len(heading_hashes) # Level is determined by the number of hashes
        title = match[1].strip()
        content = match[2].strip()

        pages.append({
            "level": level,
            "title": title,
            "content": content,
            "parent_id": None # Will be filled later
        })
    return pages


# --- Function to parse the text description ---
def OLD_parse_description(text):
    pages = []
    # Regular expression to find level markers (e.g., "## Level 1:", "### Level 2:")
    # and capture the level number and the title.
    # It also captures the content associated with that level.
    # We use re.DOTALL to make '.' match newlines as well.
    matches = re.findall(r"^(#+)\s*Level\s*(\d+):\s*(.*?)\n(.*?)(?=\n#+\s*Level\s*\d+:|\Z)", text, re.MULTILINE | re.DOTALL)

    for match in matches:
        # `match[0]` is the hash count (e.g., '##')
        # `match[1]` is the level number (e.g., '1', '2')
        # `match[2]` is the title
        # `match[3]` is the content (stripped of leading/trailing whitespace)
        level = int(match[1])
        title = match[2].strip()
        content = match[3].strip()

        pages.append({
            "level": level,
            "title": title,
            "content": content,
            "parent_id": None # Will be filled later
        })
    return pages


# --- Function to create Confluence pages ---
def create_confluence_pages(parsed_pages, space_key):
    # Dictionary to keep track of the last created page ID for each level
    # This helps in assigning parent_id for sub-pages
    level_page_ids = {}

    for page_data in parsed_pages:
        level = page_data['level']
        title = page_data['title']
        content = page_data['content']
        parent_id = None

        if level == 1:
            # Create a top-level page
            try:
                print(f"Creating Level 1 page: '{title}' in ...")
                response = confluence.create_page(
                    space=space_key,
                    title=title,
                    body=content,
                    parent_id=None # Top-level pages have no parent
                )
                page_id = response['id']
                level_page_ids[level] = page_id
                print(f"Created page '{title}' with ID: {page_id}")
            except Exception as e:
                print(f"Error creating page '{title}': {e}")
                continue # Skip to the next page if creation fails
        else:
           # Determine parent_id for sub-pages
            # The parent is the last created page of the immediate higher level
            parent_level = level - 1
            if parent_level in level_page_ids:
                parent_id = level_page_ids[parent_level]
                try:
                    print(f"Creating Level {level} sub-page: '{title}' under parent ID {parent_id}...")
                    response = confluence.create_page(
                        space=space_key,
                        title=title,
                        body=content,
                        parent_id=parent_id
                    )
                    page_id = response['id']
                    level_page_ids[level] = page_id # Update current level's last page ID
                    print(f"Created page '{title}' with ID: {page_id}")
                except Exception as e:
                    print(f"Error creating sub-page '{title}': {e}")
                    continue
            else:
                print(f"Skipping page '{title}': No parent found for Level {level}.")

# --- Main execution ---
if __name__ == "__main__":

    confluence_cfg, auth_cfg = read_config()
    #--- Configuration (see config file for values) ---
    CONFLUENCE_URL = confluence_cfg['URL'] # ]" # e.g., "https://your-domain.atlassian.net/wiki"
    USERNAME  = "email"          # Your Confluence username (email)
    API_TOKEN =  auth_cfg['TOKEN']; #           #  Generate from Atlassian account settings
    print( API_TOKEN )
    SPACE_KEY = "SAF"                 # e.g., "PROJ" for a project space


    if not all([CONFLUENCE_URL, USERNAME, API_TOKEN, SPACE_KEY]):
        print("Please configure CONFLUENCE_URL, USERNAME, API_TOKEN, and SPACE_KEY in the script.")
        exit(); 

# --- Initialize Confluence API client ---
    try:
    	confluence = Confluence(
        	url=CONFLUENCE_URL,
        	token=API_TOKEN, # For API tokens, use 'password' parameter
        	cloud=True,          # Set to True for Confluence Cloud
        	verify_ssl="/Users/aivanov/Documents/Projects/SCRIBE/confluence-tii-ae-chain.pem"
        	)
    
    	print("Successfully connected to Confluence.")
    except Exception as e:
    	print(f"Error connecting to Confluence: {e}")
    	print("Please check your CONFLUENCE_URL, USERNAME, and API_TOKEN.")
    	exit()


    print("Parsing text description...")
    parsed_pages = parse_description(text_description)
    print(f"Found {len(parsed_pages)} pages to create.")

    # Optional: Print parsed structure for verification
    for page in parsed_pages:
        print(f"Level: {page['level']}, Title: {page['title']}")

    create_confluence_pages(parsed_pages, SPACE_KEY)
