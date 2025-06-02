# SnareSyslogIngest
Ingest syslog data into Snare from an API
This example will query an API endpoint with token authetication, format the json output into syslog format and send the formatted message to Snare Central over port 514 

The config file contains information relevant to the API being called.  The syslog reciever is the IP of the Snare Central server, or other destination SIEM
The json data contains an ascending audit ID.  The python script uses this to compare to the last written ID to ensure no duplication of data is enacted.

 Example of Config paramaters.  
      "HighestAuditID": 634408,  
      "LowestAuditID": 634000,  
      "AUTH_URL": "https://your-auth-server.com/token",  
      "API_URL": "https://your-api-endpoint.com/data",  
      "CLIENT_ID": "your-client-id",  
      "SYSLOG_SERVER": "your.syslog.receiver",  
      "SYSLOG_PORT": 514,  

In this example the returned data takes the json format:  
{
    "items": [
        {
            "auditId": 634408,
            "auditDateTime": "2025-04-15T06:52:05Z",
            "authenticationId": 191,
            "authenticationName": "authName",
            "description": "Acquired bearer token for auth",
            "objectType": "Bearer Token",
            "operation": "Authenticate",
            "outcome": true,
            "links": [
                {
                    "rel": "canonical",
                    "href": "https://example.demo.com/audit-entries/634408"
                },
                {
                    "rel": "describedBy",
                    "href": "https://example.demo.com/api/12.2/catalog/audit-entry"
                }
            ]
        },
         {
            "auditId": 634407,
            "auditDateTime": "2025-04-15T06:52:05Z",
            "authenticationId": 191,
            "authenticationName": "authName",
            "description": "Acquired bearer token for auth",
            "objectType": "Bearer Token",
            "operation": "Authenticate",
            "outcome": true,
            "links": [
                {
                    "rel": "canonical",
                    "href": "https://example.demo.com/audit-entries/634408"
                },
                {
                    "rel": "describedBy",
                    "href": "https://example.demo.com/api/12.2/catalog/audit-entry"
                }
            ]
        }
    ]
}
'''


The output from the python script is a call to a Snare Syslog endpoint with the formatted data.

This Python script is scheduled to run hourly by placing a bash script which calls our python code in the **/data/Snare/RunHourly/** directory within the Snare Central server.
