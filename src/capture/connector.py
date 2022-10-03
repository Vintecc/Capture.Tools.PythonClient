from .exception import APIException
import json
import requests as r
from urllib.parse import quote_plus

def get_token(username, password):
    """Get a valid Capture token
    
    Parameters
    ----------
    username : str
        Name of a user or Activation ID of a logger
    password : str
        password associated with the passed username
        
    Returns
    -------
    str
        valid Capture token"""


    url = 'https://capture-vintecc.com/Auth'
    
    headers = {
        'AuthVersion': 'V0.0.1',
        'Content-Type': 'application/json'
    }        
    
    body = json.dumps({"Username": username, "Password": password})
    response = r.post(url, data=body, headers=headers)
    if response.status_code != 200:
        raise APIException(response.status_code, response.text)

    token = response.text.strip('\n')

    return token

def get_data(token, database, query):
    """Query a Capture database 
    
    Parameters
    ----------
    token : str
        Token associated with a Capture logger
    database : str 
        Database to be queried
    query : str
        Query that should be executed

    Returns
    -------
    list
        List of records that comply with the passed query
    """

    url = "http://capture-vintecc.com/api/data?Query=" + quote_plus(query)
    auth = "Bearer " + token
    params = {
        'Db' : database,
        'TimeOutput' : '1',
        'DbRoot' : 'Vintecc',
        'DbType' : '0',
        'OutputType' : '0'
    }
    headers = {
        'AuthVersion': 'V0.0.1',
        'Authorization': auth
    }
    response = r.get(url, headers=headers, params=params)


    if response.status_code != 200:
        raise APIException(response.status_code, response.text)

    return response.json()['Metrics']


def insert_data(token, data):
    """Insert data in all capture databases that are in the retention policy of the logger associated with the token. 
    
    Parameters
    ----------
    token : str
        Token associated with a Capture logger
    data : list 
        List of records that should be inserted

    Returns
    -------
    bool
        true if the insertion was successful, false otherwise

    Raises
    ------
    ValueError
        If one or more records have missing fields

    """

    url = "https://capture-vintecc.com/api/data"
    headers = {
        'AuthVersion': 'V0.0.1',
        'DataVersion': 'V0.0.2',
        'Content-Type': 'application/json',
        'Token': token
    }

    for record in data:
        if not 'Name' in record:
            raise ValueError("All records should contain a 'Name' field")


        if 'Tags' in record:
            for tag in record['Tags']:
                record['Tags'][tag] = str(record['Tags'][tag])
        else:
            record['Tags'] = {}


        if 'Fields' in record:
            for field in record['Fields']:
                if not isinstance(record['Fields'][field], str):
                    record['Fields'][field] = float(record['Fields'][field])
        else:
            record['Fields'] = {}


        if 'Timestamp' in record:
            record['Timestamp'] = str(record['Timestamp'])
        else:
            raise ValueError("All records should contain a 'Timestamp'.")


    data = {"Metrics": data}

    response = r.post(url, headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise APIException(response.status_code, response.text)

    return response.status_code == 200