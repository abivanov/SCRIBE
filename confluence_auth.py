from atlassian import Confluence
import re
import configparser
import sys 


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
        auth_config['TYPE'] = 'BEARER'
        auth_config['TOKEN'] = config.get('CONFLUENCE', 'TOKEN').strip()
        auth_config['CERTIFICATE'] = config.get('CONFLUENCE', 'CERTIFICATE').strip()
        
        #elif 'BASIC_AUTH' in config:
        #    auth_config['TYPE'] = 'BASIC'
        #    auth_config['USERNAME'] = config.get('BASIC_AUTH', 'USERNAME').strip()
        #    auth_config['API_TOKEN'] = config.get('BASIC_AUTH', 'API_TOKEN').strip()
        #else:
        #    print("Error: No authentication section found in 'scribe.cfg'.")
        #    print("Please add either [BEARER_TOKEN_AUTH] or [BASIC_AUTH] section.")
        #    sys.exit(1)

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
                verify_ssl="/Users/aivanov/Documents/Projects/SCRIBE/confluence-tii-ae-chain.pem" # Ideally should be in the config file as well. 
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

if __name__ == "__main__":
    confluence_cfg, auth_cfg = read_config()
    # Initialize Confluence client once
    confluence_client = get_confluence_client(confluence_cfg, auth_cfg)
    if not confluence_client: # get_confluence_client might exit, but double check
        sys.exit(1)
    else :
        print("Confluence client initialized successfully.")
