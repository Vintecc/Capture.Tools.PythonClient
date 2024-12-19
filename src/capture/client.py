from enum import Enum
import json
import httpx
from typing import Dict, List, Optional, Union

from capture._util import make_insert_ready


class DataOutput(Enum):
    JSON = 0
    CSV = 1

class DatabaseType(Enum):
    INFLUXDB = 0
    TIMESCALEDB = 1

class TimeOutput(Enum):
    HUMANREADABLE = 0 # 
    EPOCH = 1 # Unix Epoch (nanoseconds)

class CaptureAsyncClient:

    def __init__(self, base_url: str="https://capture-vintecc.com", api_token: Optional[str]=None):
        self._client = httpx.AsyncClient(timeout=None)
        self._api_token = api_token
        self.base_url = base_url
        if api_token is None:
            self.data_version = 'V0.0.3'
        else:
            self.data_version = 'V0.0.5'

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
        return    
    
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
    