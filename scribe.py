from atlassian import Confluence
import re
import configparser
import sys # For clean exit on config errors

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


# --- Initialize Confluence API client ---
def get_confluence_client(confluence_config, auth_config):
    try:
        # It's generally safer not to disable SSL verification unless absolutely necessary
        # and you understand the security implications.
        # If you face SSL errors due to corporate proxies/firewalls,
        # consult your IT or provide a path to a trusted CA certificate.
        # import urllib3
        # urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # Uncomment to suppress warnings with verify_ssl=False

        if auth_config['TYPE'] == 'BEARER':
            confluence = Confluence(
                url=confluence_config['URL'],
                token=auth_config['TOKEN'],
                cloud=True,
                verify_ssl=True # Adjust as needed for your environment
            )
            print("Successfully connected to Confluence using Bearer Token.")
        else: # BASIC_AUTH
            confluence = Confluence(
                url=confluence_config['URL'],
                username=auth_config['USERNAME'],
                password=auth_config['API_TOKEN'], # Use 'password' for API tokens
                cloud=True,
                verify_ssl=True # Adjust as needed for your environment
            )
            print("Successfully connected to Confluence using Basic Auth (API Token).")

        return confluence
    except Exception as e:
        print(f"ERROR: Could not initialize Confluence client. Please check your credentials and network connectivity.")
        print(f"Details: {e}")
        sys.exit(1) # Exit if connection fails


# --- Sample Text Description in Markdown Format ---
# Use # for Level 1, ## for Level 2, ### for Level 3, and so on.
# Content for each section goes directly below its heading.
text_description = """
# Project Apollo Overview
This is the main description for Project Apollo. It outlines the overall vision
and high-level goals.

## 1.1 Project Goals
Our primary goal is to land a human on the Moon and return them safely to Earth
before the end of the decade. We aim to achieve this through rigorous testing
and innovative engineering.

## 1.2 Project Objectives
* Develop a lunar module capable of soft landing.
* Design a command module for Earth orbit and re-entry.
* Establish ground control and communication systems.
* Train astronauts for lunar missions.

## 1.3 Meeting Minutes (Recent)
Summary of the last project steering committee meeting:
-   Budget approved for Q3.
-   Engine test schedule pushed back by two weeks.
-   New team members onboarded for navigation systems.

### 1.3.1 Q1 Meeting Summary
Key decisions from the first quarter meeting.
-   Initial team formation.
-   Technology stack selection.

# Astronaut Training Program
Details about the rigorous training regimen for our astronauts.

## 2.1 Physical Conditioning
Information on the physical requirements and training exercises.
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

# --- Function to create Confluence pages ---
def create_confluence_pages(parsed_pages, space_key, confluence_client):
    level_page_ids = {} # To track parent page IDs for each level

    for page_data in parsed_pages:
        level = page_data['level']
        title = page_data['title']
        content = page_data['content']
        parent_id = None

        # Determine parent_id
        if level > 1:
            parent_level = level - 1
            if parent_level in level_page_ids:
                parent_id = level_page_ids[parent_level]
            else:
                print(f"Skipping page '{title}': No parent (Level {parent_level}) found for current Level {level}. (Ensure hierarchy starts with Level 1 or higher levels have parents.)")
                continue

        try:
            print(f"Creating Level {level} page: '{title}' (Parent ID: {parent_id if parent_id else 'None'}) ...")
            response = confluence_client.create_page( # Use the passed client
                space=space_key,
                title=title,
                body=content,
                parent_id=parent_id
            )
            page_id = response['id']
            level_page_ids[level] = page_id
            # Clear IDs for lower levels, as this new page is now the "active" parent for its sub-levels
            for l in range(level + 1, max(level_page_ids.keys() or [level]) + 1):
                level_page_ids.pop(l, None)
            print(f"Created page '{title}' with ID: {page_id}")
        except Exception as e:
            print(f"Error creating page '{title}': {e}")
            continue

# --- Main execution ---
if __name__ == "__main__":
    confluence_cfg, auth_cfg = read_config()

    # Initialize Confluence client once
    confluence_client = get_confluence_client(confluence_cfg, auth_cfg)
    if not confluence_client: # get_confluence_client might exit, but double check
        sys.exit(1)

    print("Parsing text description...")
    parsed_pages = parse_description(text_description)
    print(f"Found {len(parsed_pages)} pages to create.")

    create_confluence_pages(parsed_pages, confluence_cfg['SPACE_KEY'], confluence_client)
  
