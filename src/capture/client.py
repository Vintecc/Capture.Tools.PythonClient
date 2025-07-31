import json
import requests as r
import httpx
from typing import Dict, List, Optional, Union

from capture._util import make_insert_ready

from capture.capture_enums import DatabaseType, DataOutput, TimeOutput, AuthorizationMethod

class CaptureClient:


    def __init__(self, base_url: str="https://capture-vintecc.com", api_token: Optional[str]=None):
        self._api_token = api_token
        self.base_url = base_url
        self._AuthorizationMethod = AuthorizationMethod.NOT_SET

        if api_token is None:
            self.data_version = 'V0.0.3'
        else:
            self.data_version = 'V0.0.5'
            self._AuthorizationMethod = AuthorizationMethod.API_TOKEN


    def authenticate(self, username: str, password: str):
        """Authenticate with the Capture API. Not needed when using an API token, as the client will be authenticated automatically. It is advised not to use Capture user credentials, but use an API token instead.
        
        Args:
            username (str): Capture logger UUID or Capture username.
            password (str): Password associated with the logger or user.
        """
        headers = {
            'AuthVersion': 'V0.0.1',
            'Content-Type': 'application/json'
        }
        response = r.post(f"{self.base_url}/auth", json={"Username": username, "Password": password}, headers=headers)
        response.raise_for_status()
        self._api_token = response.read().decode()
        self._AuthorizationMethod = AuthorizationMethod.USERNAME_PASSWORD
        return    
    
    def set_api_token(self, api_token: str):
        """Set the API token for the Capture client. This is used to authenticate with the Capture API. This can then be used to query and insert data without needing to authenticate with a username and password.

        Args:
            api_token (str): API token to use for authentication.
        """
        self._api_token = api_token
        self.data_version = 'V0.0.5'
        self._AuthorizationMethod = AuthorizationMethod.API_TOKEN
    
    def is_api_token_set(self) -> tuple[bool, AuthorizationMethod]:
        """Check if the API token is set and return the authorization method.

        Returns:
            tuple: 
                Bool: True if the API token is set, False otherwise |
                AuthorizationMethod: NOT_SET(-1), USERNAME_PASSWORD(0), or API_TOKEN(1)
        """
        is_set = self._api_token is not None and len(self._api_token) > 0
        return is_set, self._AuthorizationMethod

    def request(self, method: str, url: str, **kwargs) -> r.Response:
        """Make a generic authenticated request to the Capture backend.

        Args:
            method (str): HTTP method (e.g., 'GET', 'POST', etc.).
            url (str): The full URL to request (or relative to base_url).
            **kwargs: Additional arguments to pass to requests.request (e.g., params, json, data).

        Returns:
            requests.Response: The response object from requests.
        """
        # Use base_url if url is relative
        if not url.startswith("http"):
            url = self.base_url.rstrip("/") + "/" + url.lstrip("/")
        headers = kwargs.pop("headers", {})
        headers.setdefault('AuthVersion', 'V0.0.1')
        if self._api_token:
            headers.setdefault('Authorization', f'Bearer {self._api_token}')
        response = r.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response
    
    def query(
        self, 
        database: str, 
        query: str,
        database_root: str='Vintecc',
        database_type: DatabaseType=DatabaseType.INFLUXDB,
        output_type: DataOutput=DataOutput.JSON,
        time_output: TimeOutput=TimeOutput.EPOCH
    ) -> Union[List[Dict], str]:
        """Query data from the Capture API.

        Args:
            database (str): Capture database to query.
            query (str): Query that will be executed on the database.
            database_root (str, optional): Root database. Should only be passed for customers that are on a different database server. Defaults to 'Vintecc'.
            database_type (DatabaseType, optional): Database type, either InfluxDB or TimescaleDB. Defaults to DatabaseType.INFLUXDB.
            output_type (DataOutput, optional): Expected output, either JSON or CSV. Defaults to DataOutput.JSON.
            time_output (TimeOutput, optional): Timestamp format in result, either unix epoch or human readable format. Defaults to TimeOutput.EPOCH.

        Raises:
            Exception: An unexpected response was received from the Capture API.

        Returns:
            For JSON output:
                List[Dict]: List of database records in the form of Python dictionaries. Each dictionary contains:
                    * Name: Name of the measurement/table. 
                    * Timestamp: Timestamp of the record.
                    * Tags: Dictionary of tags.
                    * Fields: Dictionary of fields.
            For CSV output:
                str: CSV formatted string.
        """

        if self._AuthorizationMethod == AuthorizationMethod.NOT_SET:
            raise Exception("The Capture client is not authenticated. Please authenticate using 'authenticate' or set an API token using 'set_api_token' before querying data.")
        
        headers = {
            'AuthVersion': 'V0.0.1',
            'Authorization': f'Bearer {self._api_token}',
        }

        params = {
            'Db' : database,
            'DbRoot' : database_root,
            'DbType' : database_type.value,
            'OutputType' : output_type.value,
            'Query' : query,
            'TimeOutput' : time_output.value, 
        }

        response = r.request('GET', f"{self.base_url}/api/data", headers=headers, params=params)

        try:
            if output_type == DataOutput.JSON:
                # Use .text to get the response body as a string
                response_json = json.loads(response.text)
                return response_json['Metrics']
            elif output_type == DataOutput.CSV:
                # Use .text to get the CSV as a string
                return response.text
        except Exception:
            raise Exception("The Capture API returned an unexpected response.")
        
    
    def insert_data(self, data: List[Dict], database: Optional[str]=None, retention: Optional[str]=None) -> str:
        """Insert data in Capture using the API.

        Args:
            data (List[Dict]): List of Python dictionaries, each representing a record to be inserted. Each dictionary should contain: 
                * Name: Name of the measurement/table.
                * Timestamp: Timestamp of the record.
                * Tags: Dictionary of tags.
                * Fields: Dictionary of fields.
            database (Optional[str], optional): Database to insert the records in. Required when using an API token. Defaults to None.
            retention (Optional[str], optional): Retention to use for the inserted records. Required when using an API token. Defaults to None.

        Raises:
            ValueError: If using an API token, database and retention are required.
            ValueError: If any of the records in the data list are missing required attributes.

        Returns:
            str: Response from the Capture API.
        """
        if self.data_version == 'V0.0.5'and (database is None or retention is None):
            raise ValueError("Database and retention are required when using an API token.")

        headers = {
            'AuthVersion': 'V0.0.1',
            'Authorization': f'Bearer {self._api_token}',
            'Content-Type': 'application/json',
            'DataVersion': self.data_version
        }

        params = {"Database": database, "Retention": retention} if database and retention else {}

        to_insert = {"Metrics": make_insert_ready(data)}
        response = r.post(f"{self.base_url}/api/data", headers=headers, params=params, json=to_insert)
        response.raise_for_status()

        return response.text
    


    
class CaptureAsyncClient:

    def __init__(self, base_url: str="https://capture-vintecc.com", api_token: Optional[str]=None):
        self._client = httpx.AsyncClient(timeout=None)
        self._api_token = api_token
        self.base_url = base_url
        self._AuthorizationMethod = AuthorizationMethod.NOT_SET
        if api_token is None:
            self.data_version = 'V0.0.3'
        else:
            self.data_version = 'V0.0.5'
            self._AuthorizationMethod = AuthorizationMethod.API_TOKEN

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self._client.aclose()

    async def authenticate(self, username: str, password: str):
        """Authenticate with the Capture API. Not needed when using an API token, as the client will be authenticated automatically. It is advised not to use Capture user credentials, but use an API token instead.
        
        Args:
            username (str): Capture logger UUID or Capture username.
            password (str): Password associated with the logger or user.
        """
        headers = {
            'AuthVersion': 'V0.0.1',
            'Content-Type': 'application/json'
        }
        response = await self._client.post(f"{self.base_url}/auth", json={"Username": username, "Password": password}, headers=headers)
        response.raise_for_status()
        self._api_token = response.read().decode()
        self._AuthorizationMethod = AuthorizationMethod.USERNAME_PASSWORD
        return    
    
    def set_api_token(self, api_token: str):
        """Set the API token for the Capture client. This is used to authenticate with the Capture API. This can then be used to query and insert data without needing to authenticate with a username and password.

        Args:
            api_token (str): API token to use for authentication.
        """
        self._api_token = api_token
        self.data_version = 'V0.0.5'
        self._AuthorizationMethod = AuthorizationMethod.API_TOKEN
    
    def is_api_token_set(self) -> tuple[bool, AuthorizationMethod]:
        """Check if the API token is set and return the authorization method.

        Returns:
            tuple: 
                Bool: True if the API token is set, False otherwise |
                AuthorizationMethod: NOT_SET(-1), USERNAME_PASSWORD(0), or API_TOKEN(1)
        """
        is_set = self._api_token is not None and len(self._api_token) > 0
        return is_set, self._AuthorizationMethod

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make a generic authenticated async request to the Capture backend.

        Args:
            method (str): HTTP method (e.g., 'GET', 'POST', etc.).
            url (str): The full URL to request (or relative to base_url).
            **kwargs: Additional arguments to pass to httpx.AsyncClient.request (e.g., params, json, data).

        Returns:
            httpx.Response: The response object from httpx.
        """
        if not url.startswith("http"):
            url = self.base_url.rstrip("/") + "/" + url.lstrip("/")
        headers = kwargs.pop("headers", {})
        headers.setdefault('AuthVersion', 'V0.0.1')
        if self._api_token:
            headers.setdefault('Authorization', f'Bearer {self._api_token}')
        response = await self._client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response


    async def query(
        self, 
        database: str, 
        query: str,
        database_root: str='Vintecc',
        database_type: DatabaseType=DatabaseType.INFLUXDB,
        output_type: DataOutput=DataOutput.JSON,
        time_output: TimeOutput=TimeOutput.EPOCH
    ) -> Union[List[Dict], str]:
        """Query data from the Capture API.

        Args:
            database (str): Capture database to query.
            query (str): Query that will be executed on the database.
            database_root (str, optional): Root database. Should only be passed for customers that are on a different database server. Defaults to 'Vintecc'.
            database_type (DatabaseType, optional): Database type, either InfluxDB or TimescaleDB. Defaults to DatabaseType.INFLUXDB.
            output_type (DataOutput, optional): Expected output, either JSON or CSV. Defaults to DataOutput.JSON.
            time_output (TimeOutput, optional): Timestamp format in result, either unix epoch or human readable format. Defaults to TimeOutput.EPOCH.

        Raises:
            Exception: An unexpected response was received from the Capture API.

        Returns:
            For JSON output:
                List[Dict]: List of database records in the form of Python dictionaries. Each dictionary contains:
                    * Name: Name of the measurement/table. 
                    * Timestamp: Timestamp of the record.
                    * Tags: Dictionary of tags.
                    * Fields: Dictionary of fields.
            For CSV output:
                str: CSV formatted string.
        """

        if self._AuthorizationMethod == AuthorizationMethod.NOT_SET:
            raise Exception("The Capture client is not authenticated. Please authenticate using 'authenticate' or set an API token using 'set_api_token' before querying data.")
        
        headers = {
            'AuthVersion': 'V0.0.1',
            'Authorization': f'Bearer {self._api_token}',
        }

        params = {
            'Db' : database,
            'DbRoot' : database_root,
            'DbType' : database_type.value,
            'OutputType' : output_type.value,
            'Query' : query,
            'TimeOutput' : time_output.value, 
        }

        async with self._client.stream('GET', f"{self.base_url}/api/data", headers=headers, params=params) as response_stream:
            response_stream.raise_for_status()
            response_bytes = await response_stream.aread()
            
        try: 
            if output_type == DataOutput.JSON:
                response = json.loads(response_bytes)
                return response['Metrics']
            elif output_type == DataOutput.CSV: 
                return response_bytes.decode('utf-8')
        except Exception: 
            raise Exception("The Capture API returned an unexpected response.")
        
    
    async def insert(self, data: List[Dict], database: Optional[str]=None, retention: Optional[str]=None) -> str:
        """Insert data in Capture using the API.

        Args:
            data (List[Dict]): List of Python dictionaries, each representing a record to be inserted. Each dictionary should contain: 
                * Name: Name of the measurement/table.
                * Timestamp: Timestamp of the record.
                * Tags: Dictionary of tags.
                * Fields: Dictionary of fields.
            database (Optional[str], optional): Database to insert the records in. Required when using an API token. Defaults to None.
            retention (Optional[str], optional): Retention to use for the inserted records. Required when using an API token. Defaults to None.

        Raises:
            ValueError: If using an API token, database and retention are required.
            ValueError: If any of the records in the data list are missing required attributes.

        Returns:
            str: Response from the Capture API.
        """
        if self.data_version == 'V0.0.5'and (database is None or retention is None):
            raise ValueError("Database and retention are required when using an API token.")

        headers = {
            'AuthVersion': 'V0.0.1',
            'Authorization': f'Bearer {self._api_token}',
            'Content-Type': 'application/json',
            'DataVersion': self.data_version
        }

        params = {"Database": database, "Retention": retention} if database and retention else {}

        to_insert = {"Metrics": make_insert_ready(data)}
        response = await self._client.post(f"{self.base_url}/api/data", headers=headers, params=params, json=to_insert)
        response.raise_for_status()

        return response.content.decode("utf-8")
    
    
    