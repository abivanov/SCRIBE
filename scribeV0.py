from atlassian import Confluence
import re

# --- Configuration (see config file for values) ---
CONFLUENCE_URL = "confluence"  # e.g., "https://your-domain.atlassian.net/wiki"
USERNAME  = "email"          # Your Confluence username (email)
API_TOKEN = ""                 # Generate from Atlassian account settings
SPACE_KEY = "RRR"                 # e.g., "PROJ" for a project space

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


# --- Sample Text Description ---
# Use '## Level 1:' for top-level pages
# Use '### Level 2:' for sub-pages
# Use '#### Level 3:' for sub-sub-pages, etc.
# The content for each page will be everything after the level marker until the next level marker.

text_description = """
## Level 1:  Introduction
a. The MDD shall contain a description of the purpose, objective, content and
the reason prompting its preparation (e.g. logic, organization, process or
procedure).
## Level 1:  Applicable and reference documents
The MDD shall list the applicable and reference documents in support to
the generation of the document, and include, as a minimum, the current
preliminary technical requirements specification.
## Level 1: Technical requirements specification
Summary of key Technical requirements provided by LASP (Mass/Size, Power, Data, Key interfaces )
Autonomy requirements (no uplink)
## Level 1: Mission Description

### Level 2: 1. Overview of the concept
Brief overview - we're building effectively a cubesat that will function for 7 years in space to make a final descent onto the asteroid 267 Justitia. 
### Level 2: 2. Mission analysis
High level overview of the mission profile. 
### Level 2: 3 CONOPS 
we distinguish two main phases: pre-deployment (or cruise phase) and post deployment (after sepration from the main spacecraft towards the asteroid) . During the cruise phase, there the satellite will be be turned on for major events: fly-bys of asteroids and planets and aliveness check. 
#### Level 3: Pre-deployment 

##### Level 4: Fly bys 
we expect to fly by Venus, Earth, Mars as weell as 6 asteroids. 
Describe here how we're going to signal the fly-by mode 
##### Level 4: Aliveness 
Aliveness check is planned for all instruments during the cruise phase. Expected frequency once per year. 
#### Level 3: Deployment and Descent 
Describe CONOPS during descent with options depending on the asteroid gravity. 
### Level 2: 4. System description
#### Level 3: Payload
All experiments on board 
##### Level 4: Imaging cameras
Requirements 
Description of NAC and WAC
Analysis
##### Level 4: Data Processing Unit
Requirements
Description
Analysis
##### Level 4: Attitude Determination and Control System
Requirements
Description
Analysis
#### Level 3: Platform
Platform (mostly contributed by the HEX20) 
##### Level 4: Structure
Requirements
Description
Analysis
##### Level 4: Thermal
Requirements
Description
Analysis
##### Level 4: Energy and power System
Requirements
Description
Analysis
##### Level 4: Communications
Requirements
Description
Analysis
##### Level 4: OnBoard Computer
Requirements
Description
Analysis
## Level 1:  Assessment of the performance
### Level 2: Design vs. Key Technical requirements 
### Level 2: Verification of Key Technical requirements 
### Level 2: Key Technical risks
The MDD shall provide the list of identified risk related to the concept,
including as a minimum technology, contingencies handling, and
programmatic aspects.
## Level 1:  Summary
The MDD shall summarize the strengths and weaknesses of the concept.
"""

# --- Function to parse the text description ---
def parse_description(text):
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
                print(f"Creating Level 1 page: '{title}'...")
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
    if not all([CONFLUENCE_URL, USERNAME, API_TOKEN, SPACE_KEY]):
        print("Please configure CONFLUENCE_URL, USERNAME, API_TOKEN, and SPACE_KEY in the script.")
    else:
        print("Parsing text description...")
        parsed_pages = parse_description(text_description)
        print(f"Found {len(parsed_pages)} pages to create.")

        # Optional: Print parsed structure for verification
        for page in parsed_pages:
            print(f"Level: {page['level']}, Title: {page['title']}")

        create_confluence_pages(parsed_pages, SPACE_KEY)
