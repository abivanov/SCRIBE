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
                verify_ssl="/Users/aivanov/Documents/Projects/SCRIBE/confluence-tii-ae-chain.pem"
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
# 1. Introduction
a. The PMP shall contain a description of the purpose, objective and the
reason prompting its preparation (e.g. program or project reference and
phase)

# 2. Applicable and reference documents
a. The PMP shall list the applicable and reference documents used in
support of the generation of the document.

# 3. Objectives and constraints of the project
a. The PMP shall briefly describe the objective and constraints of the project
in conformance with the project requirements documents.

# 4. Project organization
a. The PMP shall describe the project organization approach in
conformance with the requirements as defined in clause 5.2.

# 5. Project breakdown structures
a. The PMP shall describe the project breakdown structures approach in
conformance with the project breakdown structure requirements as
defined in clause 5.3 and identify the title of individual documents called
up by these requirements.

# 6. Configuration, information and documentation
management
a. The PMP shall describe the configuration, information and
documentation management approach, as defined in ECSS M ST 40,
Annex A.

Here goes description of JIRA, Confluence and ARKHIV description. 

## 6.1 General
a. The configuration management plan shall identify all functions and
processes, both technical and managerial, required for managing the
configuration of the programme or project.
b. The configuration management plan shall introduce the following, as a
minimum:
1. configuration identification;
2. configuration control;
3. configuration status accounting;
4. configuration audits and reviews;
5. interface control;
6. supplier control.

## 6.2 Configuration identification
a. The configuration management plan shall identify, name, and describe
the documented physical and functional characteristics of the
information to be maintained under configuration management control
for the programme or project.
b. The configuration management plan shall describe the following, as a
minimum:

b. If the configuration, information and documentation management
approach is contained in a rolled out configuration management plan,
the PMP may include only a brief description together with a reference to
the configuration, information and documentation management plan.


1. product tree establishment (System decomposition);
2. identification of configuration items, i.e. the selection process of
the items to be controlled and their definitions as they evolve or
are selected;
3. naming of configuration items, i.e. the specification of the
identification system for assigning unique identifiers to each item
to be controlled;
4. configuration baselines establishment and maintenance;
5. interface identification;
6. configuration documentation and data release procedures.
c. In case of software configuration item and where a tool is used to build
its baseline, the following shall be described:
1. procedure to enter a software configuration item into a baseline;
2. procedure to configure and establish a baseline;
3. software products and records to define a baseline;
4. procedure to approve a baseline;
5. authority to approve a baseline.
d. In case software libraries are established, the following shall be
identified:
1. library types;
2. library locations;
3. media used for each library;
4. library population mechanism;
5. number of identical libraries and the mechanism for maintaining
parallel contents;
6. library contents and status of each item included in;
7. conditions for entering a SCI, including the status of maturity
compatible with the contents required for a particular software
library type;
8. provision for protecting libraries from malicious and accidental
harm and deterioration;
9. software recovery procedures;
10. conditions for retrieving any object of the library;
11. library access provisions and procedures.
## Configuration control
a. The configuration management plan shall describe the configuration
control process and data for implementing changes to the configuration
items and identify the records to be used for tracking and documenting
the sequence of steps for each change.

The configuration management plan shall describe the following, as a
minimum:
1. configuration control board functions, responsibilities, authorities;
2. processing changes;
3. change requests;
4. change proposal;
5. change evaluation;
6. change approval;
7. change implementation;
8. processing planned configuration departures (deviations);
9. processing unplanned configuration departures (product
nonconformances, waivers).
<4.4> Interface control
a. The configuration management plan shall describe the process and data
for coordinating changes to the programme or project configuration
management items with changes to interfaces.

## 6.3 Supplier control
a. For both subcontracted and acquired products (i.e. equipment, software
or service), the configuration management plan shall define the process
and data to flow down the CM requirements and the programme
monitoring methods to control the supplier.
b. The configuration management plan shall define the process and data to
incorporate the supplier developed items into programme or project
configuration management and to coordinate changes to these items.
c. The configuration management plan shall also describe how the product
is received, tested, and placed under configuration control.

## 6.4 Configuration status accounting
a. The configuration management plan shall describe the process and data
for reporting the status of configuration items.
b. The following minimum information shall be tracked and reported for
each configuration management item:
1. status of the configuration baselines;
2. design status of the configuration item;
3. status of configuration documentation and configuration data sets;
4. status of approval of changes and deviations and their
implementation status;
5. status of discrepancies and actions arising from technical reviews
and configuration verification reviews.

## 6.5 Configuration verification
a. The configuration management plan shall describe the process and data
to verify the current configuration status from which the configuration
baselines are established.
b. The configuration management plan shall provide the description of
verification plans, procedures and schedules.
c. The configuration management plan shall identify how the recording,
reporting and tracking of action items and incorporation of review
recommendations are maintained.

## 6.6 Audits of CM system
a. The configuration management plan shall describe the process, data and
schedule for configuration audits to ensure that the configuration
management of the programme or project is performed.
b. As a minimum, the configuration management plan shall enable that
1. the CM process is properly defined, implemented and controlled,
and
2. the configuration management items reflect the required physical
and functional characteristics.

## 6.7 Technical data management
a. The configuration management plan shall describe the process and data
to access and maintain text and CAD files, data and software repositories,
and the implementation of any PDM system.

## 6.8 Information/documentation management

### Information identification
a. The configuration management plan shall describe the main
information/documentation categories, such as management information,
contractual documentation or engineering data, to be established and
used throughout the programme/project life cycle.
b. The configuration management plan shall describe methods for
information/document identification including versioning.
c. The configuration management plan should list the codes for companies,
information types, models, subsystems, etc. which are applied
specifically in the identification method or are in general use during
project execution.
d. The configuration management plan shall identify the metadata
structures of the main information categories.

### Data formats
a. The configuration management plan shall define for the various
information categories the data formats to be used for
1. content creation and update
2. distribution
3. archiving
b. The configuration management plan shall specify which format takes
precedence in case a format conversion is applied.

### Processes
a. The configuration management plan shall describe the actors involved in,
as well as the method and processes for, creating, collecting, reviewing,
approving, storing, delivering and archiving information items.
b. The configuration management plan shall describe the handling of legacy
documentation and off the shelf documentation.
c. The configuration management plan shall define the information
retention period.

### Information systems
a. The configuration management plan shall list the project information
systems to be used for creating, reviewing, storing, delivering and
archiving the main information categories
NOTE For example: ABC for schedule, and XYZ for
engineering DB.

### Delivery methods
a. The configuration management plan shall describe the methods used to
deliver TDPs.

### Digital signature
a. The configuration management plan shall define the procedures,
methods and rules applicable to digital signatures. This comprises
information about the following aspects:
1. certificate type
2. management of signature key
3. time stamping
4. signing of PDF documents
5. multiple signatures per document

### Information status reporting
a. The configuration management plan shall describe the process and
content for reporting the status of information items.
b. For documentation the following attributes shall be reported as a
minimum: document identification, version, title, issue date, status, and
document category.

# 7. Cost and schedule management
a. The PMP shall describe the cost and schedule management approach, as
defined in ECSS M ST 60.
b. If the cost and schedule management approach is described in a rolled
out cost and schedule management plan, the PMP may include only a
brief description together with a reference to the cost and schedule
management plan.

# 8. Integrated logistic support
a. The PMP shall describe the integrated logistic support approach, as
defined in ECSS M ST 70.

# 9. Risk management
a. The PMP shall briefly describe the risk management approach which is
described in more detail in a rolled out risk management policy and plan,
as defined in ECSS M ST 80, Annexes A and B.

# 10. Product assurance management
a. The PMP shall describe the product assurance management approach,
including the proposed breakdown into PA disciplines and the interfaces
between these disciplines, as defined in ECSS Q ST 10, Annex A.
b. If the product assurance management approach is described in a rolled
out PA plan, the PMP may include only a brief description together with
a reference to the product assurance plan.

Here goes CHASM description. 

# 11. Engineering management
a. The PMP shall describe the engineering management approach,
including the proposed breakdown into engineering disciplines and the
interfaces between these disciplines, as defined in ECSS E ST 10,
Annex D.
b. If the engineering management approach is described in a rolled out
system engineering plan, the PMP may include only a brief description
together with a reference to the system engineering plan.

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
            print(f"Creating Level {level} page: '{space_key}/{title}' (Parent ID: {parent_id if parent_id else 'None'}) ...")
            
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
  
