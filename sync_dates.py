import xml.etree.ElementTree as ET
import json
import requests
import configparser
import sys


def is_number(value):
    try:
        float(value)  # Works for int, float, scientific notation
        return True
    except (ValueError, TypeError):
        return False


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
        # Read `JIRA` general settings
        confluence_config['URL']         = config.get('JIRA', 'URL').strip()
        confluence_config['PROJECT_KEY'] = config.get('JIRA', 'PROJECT_KEY').strip()
        confluence_config['TOKEN']       = config.get('JIRA', 'TOKEN').strip()
        confluence_config['CERTIFICATE'] = config.get('JIRA', 'CERTIFICATE').strip()

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

    return confluence_config


def retrieve_jira_info(issue_key):
    """
    Retrieve Jira issue details by issue key.
    
    Args:
        issue_key (str): The Jira issue key (e.g., "SAF-485").
    
    Returns:
        dict: The JSON fields for the issue.
    """
    
    # Read configuration file 
    jcfg = read_config()   # scrbie.cfg by defintion, so far all in one directory. 
    # Jira connection settings
    JIRA_BASE_URL = jcfg["URL"] # "https://jira.tii.ae"  # Change to your Jira instance
    API_ENDPOINT = f"/rest/api/2/issue/{issue_key}"
    TOKEN = jcfg["TOKEN"]     # Replace with your token
    CERT_PATH = jcfg['CERTIFICATE']          # Or True to verify with system CA

    # Build the request
    url = JIRA_BASE_URL + API_ENDPOINT
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, verify=CERT_PATH )
        response.raise_for_status()  # Raise for 4xx/5xx errors
        issue_data = response.json()
        return issue_data.get("fields", {})  # Return only fields
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Jira: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing Jira response: {e}")
        return None


def update_jira_fields(issue_key, sd_value, due_date):
    """
    Updates two fields in a Jira issue: 'sd' (custom field) and 'duedate'.

    Args:
        issue_key (str): Jira issue key, e.g. 'PROJ-123'
        sd_value (str): Value for the SD field (string or other data type depending on the field type)
        due_date (str): Due date in 'YYYY-MM-DD' format
   
    """

 # Jira connection settings
      # Read configuration file 
    jcfg = read_config()   # scrbie.cfg by defintion, so far all in one directory. 
    # Jira connection settings
    JIRA_BASE_URL = jcfg["URL"] # "https://jira.tii.ae"  # Change to your Jira instance
    API_ENDPOINT = f"/rest/api/2/issue/{issue_key}"
    TOKEN = jcfg["TOKEN"]    # Replace with your token
    CERT_PATH = jcfg['CERTIFICATE']          # Or True to verify with system CA

    # Build the request
    url = JIRA_BASE_URL + API_ENDPOINT
    
    # Replace 'customfield_XXXXX' with the real SD field ID from your Jira instance
    payload = {
        "fields": {
            "customfield_10015": sd_value,
            "duedate": due_date
        }
    }

    headers = {
         "Content-Type": "application/json",
         "Authorization": f"Bearer {TOKEN}", 
         "Accept": "application/json"
    }

    # print( url, headers, sd_value, due_date)
    response= requests.put(url, headers=headers, data=json.dumps(payload),  verify= CERT_PATH )
    
    if response.status_code == 204:
        print(f"Issue {issue_key} updated successfully.")
    else:
        print(f"Failed to update issue {issue_key}: {response.status_code} - {response.text}")

# THis is a simple function to compare times 
def compare_first_10(str1, str2):
    if str1 is None or str2 is None or str1 == "None" or str2 == "None":
        return False
    return str1[:10] == str2[:10]

# Load and parse the XML file
tree = ET.parse('SAFAR Project Schedule.xml')
root = tree.getroot()

# Namespace handling (if any)
namespaces = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}


# Extract task information
tasks = []

for task in root.findall('.//ns:Task', namespaces):
    name = task.findtext('ns:Name', default='N/A', namespaces=namespaces)
    notes = task.findtext('ns:Notes', default='N/A', namespaces=namespaces)
    ms_start = task.findtext('ns:Start', default='N/A', namespaces=namespaces)
    ms_finish = task.findtext('ns:Finish', default='N/A', namespaces=namespaces)
    outline1 = task.findtext('ns:OutlineNumber', default='N/A', namespaces=namespaces)
    outline2 = task.findtext('ns:OutlineLevel', default='N/A', namespaces=namespaces)
    if is_number(notes):
        n = int(outline2)
        task_type = ["Work Package", "Epic", "Story", "Task", "Subtask"][n-3] if 1 <= n <= 6 else None
        issue_key = f"SAF-{notes}"
        
        # Don't update work packages or EPics - apparently they rolled up. 
        # if task_type == "Work Package" : continue 
        
        fields = retrieve_jira_info(issue_key)
        j_start_date = fields.get("customfield_10015")
        j_end_date = fields.get("duedate")
        print(issue_key, ":", name, ms_start, ms_finish, outline2, task_type)
        print("JIRA", j_start_date, j_end_date)
        
    
        
        if compare_first_10(ms_start, j_start_date):
            print('Data synced ok')
            continue
        else:
            print(issue_key, ' Need update: from', j_start_date, 'to', ms_start[:10])
        
        if compare_first_10(ms_finish, j_end_date):
            print('Data synced ok')
        else:
            print(issue_key, ' Need update: from', j_end_date, 'to', ms_finish[:10])
            
        update_jira_fields(issue_key, ms_start[:10], ms_finish[:10])

        # Debugging exit after the first cycle .
        # exit()
    	
	
