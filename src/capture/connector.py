import requests as r
import json
from urllib.parse import quote_plus

from capture._util import make_insert_ready

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
    token = r.post(url, data=body, headers=headers).text.strip('\n')
    
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
    res = r.get(url, headers=headers, params=params)

    if (res.status_code == 200):
        return res.json()['Metrics']
    else: 
        return None
    

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
    """

    url = "https://capture-vintecc.com/api/data"
    headers = {
        'AuthVersion': 'V0.0.1',
        'DataVersion': 'V0.0.2',
        'Content-Type': 'application/json',
        'Token': token
    }

    to_insert = {"Metrics": make_insert_ready(data)}

    res = r.post(url, headers=headers, data=json.dumps(to_insert))
    
    return res.status_code == 200