from capture.connector import get_token, get_data, insert_data

user = ""
pwd = ""

logger_uid = ""
logger_pwd = ""

db = ""
query = ""

# User token needed for requesting data
token = get_token(user, pwd)
# Logger token needed for inserting data
logger_token = get_token(logger_uid)

# DB and query like you would set in grafana
data = get_data(token, db, query)

############################################################


# Do processing on records
# e.g. pandas.json_normalize(data) will flatten the column structure and give back a pandas dataframe



############################################################


#writes to all retentions of logger, data should be a list of records that look like this (same structure as received when executing get_data):
#   {
#       'Name': 'MeasurementName',
#       'Tags': { ... },
#       'Fields': { ... },
#       'Timestamp': '1670572800352000000'
#   }
success = insert_data(logger_token, data)