import requests
import json
import socket
from datetime import datetime, timezone
import platform
import os

########
print("Running xml_output_direct_RFC5424")
Current_audit_id = 0

# Path to config
config_path = "/data/SnareCollect/OracleAPI/OracleAPIconfig.json"
#config_path = "C:\\data\\SnareCollect\\OracleAPIconfig.json"


# Ensure config exists
if not os.path.exists(config_path):
    print(f"Config file not found: {config_path}")
    exit(1)

# Load config
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except Exception as e:
    print(f"Error reading config: {e}")
    exit(1)

# Extract values
LastAuditIDsent = config.get("LastAuditIDsent")
AUTH_URL = config.get("AUTH_URL")
API_URL = config.get("API_URL")
CLIENT_ID = config.get("CLIENT_ID")
CLIENT_SECRET = config.get("CLIENT_SECRET")
GRANT_TYPE = config.get("GRANT_TYPE")
SYSLOG_SERVER = config.get("SYSLOG_SERVER")
SYSLOG_PORT = config.get("SYSLOG_PORT")
HOSTNAME = config.get("HOSTNAME")
TAG = config.get("TAG")

# Show loaded config values
print(f"Loaded config:")
print(f"  LastAuditIDsent: {LastAuditIDsent}")
print(f"  AUTH_URL: {AUTH_URL}")
print(f"  API_URL: {API_URL}")
print(f"  CLIENT_ID: {CLIENT_ID}")
print(f"  CLIENT_SECRET: {'*' * len(CLIENT_SECRET) if CLIENT_SECRET else None}")
print(f"  GRANT_TYPE: {GRANT_TYPE}")
print(f"  SYSLOG_SERVER: {SYSLOG_SERVER}")
print(f"  SYSLOG_PORT: {SYSLOG_PORT}")
print(f"  HOSTNAME: {HOSTNAME}")
print(f"  TAG: {TAG}")


# Priority = Facility Number 4 (security/authorization messages) + 6 (INFORMATIONAL)
PRI = '<46>'
PROCID = str(os.getpid())
NOW_ZULU = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TimeNow=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

# === STEP 1: Get Bearer Token ===
try:
    auth_response = requests.post(
        AUTH_URL,
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': GRANT_TYPE
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    auth_response.raise_for_status()
    access_token = auth_response.json().get('access_token')
    if not access_token:
        raise Exception("No access_token found in response.")
except Exception as e:
    print(f"ERROR - Failed to get access token: {e}")
    exit(1)

# === STEP 2: Fetch Audit Logs ===
response = requests.get(API_URL)
data = response.json()
try:
    headers = {'Authorization': f'Bearer {access_token}'}
    api_response = requests.get(API_URL, headers=headers)
    api_response.raise_for_status()
    data = api_response.json()
    print("Audit Token retrieved")
    #print(f"{data}")
except Exception as e:
    print(f"ERROR - Failed to fetch audit logs: {e}")
    exit(1)
    
# Get list of items
my_items = data.get('items', [])
# Get list of links
my_links = data.get('links', [])
# Get first auditId - Highest ID in json returned
first_audit_id = data["items"][0]["auditId"]
print(f"first auditId from API ={first_audit_id}")
# Get last auditId
last_audit_id = data["items"][-1]["auditId"]
print(f"last auditId from API ={last_audit_id}")


#check if first auditId in list is higher than last recorded send
#only send if data auditId is higher than last recorded auditId sent
#work on looping
#
try:
    print("Check last auditID")
    # Check for termination condition
    if first_audit_id < LastAuditIDsent:
        print(f"LastAuditIDsent = {LastAuditIDsent}  < first_audit_id = {first_audit_id}")
        exit_program()
    # Continue with other operations
except Exception as e:
    print(f"An error occurred : {e}")
    exit_program()

print("OK to proceed to send syslog stream with API data")

# --- SET UP SYSLOG SOCKET ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- SEND EACH ITEM ENTRY TO SYSLOG ---
for my_item in my_items:
#debug
#    print(f"{my_item.get('auditId')}")
#    print(f"{my_item}")
#    timestamp=my_item.get('auditDateTime')
    timestamp=NOW_ZULU
#      Format all links
    links_list = my_item.get("links", [])
    links_str = "; ".join(
        f"{link.get('rel')}:{link.get('href')}" for link in links_list if link.get("rel") and link.get("href")
        )
    MSGID=my_item.get('auditId')
    Current_audit_id = MSGID
#message_body contains full json return item entry
    message_body = (
            f"auditId={my_item.get('auditId')} "
            f"auditDateTime={my_item.get('auditDateTime')} "
            f"authName={my_item.get('authenticationName')} "
            f"description=\"{my_item.get('description')}\" "
            f"objectType={my_item.get('objectType')} "
            f"operation={my_item.get('operation')} "
            f"outcome={my_item.get('outcome')}"
            f" links=\"{links_str}\""
        )
    syslog_message = f"{PRI}1 {timestamp} {HOSTNAME} {TAG} {PROCID} {MSGID} {message_body}"
#    print(f"syslog_message = {PRI}1 {timestamp} {HOSTNAME} {TAG} {PROCID} {MSGID} {message_body}")
    if my_item.get('auditId') > LastAuditIDsent:
        sock.sendto(syslog_message.encode(), (SYSLOG_SERVER, SYSLOG_PORT))
        print(f"syslog auditId sent ={my_item.get('auditId')} ")
 

sock.close()

# ---Update audit ID values (example values shown) ---
LastAuditIDsent = first_audit_id
config["LastAuditIDsent"] = LastAuditIDsent

# --- Write full updated config back to file ---
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
    
print(f"\nUpdated LastAuditIDsent = {LastAuditIDsent} written to {config_path}")

