# Vintecc-capture

This package allows to connect to Capture, a data platform used to capture data from industry (<https://www.vintecc.com/en/solutions/capture>) from python code.

# Documentation

This library wraps the Capture Data API to add convenience in accessing data from capture and inserteing data into the capture framework.

# Usage methods

Possible usage methods:
- Connector
- Client
- Async Client


## 1. Simple Connector usage

- **HTTP Library:** Uses the `requests` library for synchronous HTTP requests.
- **Usage:** Standalone functions, not classes. You call them directly with the required arguments.
- **Typical Use Case:** Quick scripts, prototyping, or when you want minimal abstraction and direct access to the API.
- **Example Usage:**
  ```python
  from capture.connector import get_token, get_data, insert_data

  token = get_token("username", "password")
  data = get_data(token, "database", "SELECT * FROM ...")
  success = insert_data(token, data_to_insert)
  ```
- **Implementation Details:**
  - Functions like `get_token`, `get_data`, and `insert_data` wrap direct HTTP requests.
  - No object-oriented structure, no state is kept between calls.
  - Minimal error handling and no extensibility.

---

## 2. `CaptureClient` (Synchronous Class)

- **HTTP Library:** Uses the `requests` library for synchronous HTTP requests.
- **Usage:** Object-oriented; you instantiate the class and call its methods.
- **Typical Use Case:** Scripts, notebooks, or applications where you want a reusable client with state (e.g., API token).
- **Example Usage:**
  ```python
  from capture.client import CaptureClient

  client = CaptureClient(api_token="...")
  result = client.query(database="...", query="...")
  ```
- **Implementation Details:**
  - Maintains state (API token, base URL, etc.).
  - Methods for authentication, querying, and inserting data.
  - Easier to extend and maintain than simple functions.

---

## 3. `CaptureAsyncClient` (Asynchronous Class)

- **HTTP Library:** Uses `httpx.AsyncClient` for asynchronous HTTP requests.
- **Usage:** Object-oriented and asynchronous; requires `async with` and `await`.
- **Typical Use Case:** Async applications, web servers, or when making many requests concurrently.
- **Example Usage:**
  ```python
  from capture.client import CaptureAsyncClient

  async with CaptureAsyncClient(api_token="...") as client:
      result = await client.query(database="...", query="...")
  ```
- **Implementation Details:**
  - Maintains state and uses async context management.
  - Methods are `async def` and require `await`.
  - Best for high-performance or concurrent use cases.

---

## Summary Table

| Feature                | Simple Connector Functions | CaptureClient (Sync) | CaptureAsyncClient (Async) |
|------------------------|---------------------------|----------------------|----------------------------|
| HTTP Library           | requests                  | requests             | httpx.AsyncClient          |
| Structure              | Functions                 | Class                | Class                      |
| State                  | None                      | Yes (token, etc.)    | Yes (token, etc.)          |
| Method Type            | Synchronous               | Synchronous          | Asynchronous (`async def`) |
| Usage                  | Direct call               | Instantiate & call   | `async with` + `await`     |
| Context Manager        | No                        | No                   | Yes (`async with`)         |
| Use Case               | Quick scripts, protos     | Scripts, notebooks   | Async apps, concurrency    |
| Extensibility          | Low                       | High                 | High                       |
| Blocking?              | Yes                       | Yes                  | No (non-blocking)          |

---

# Examples

## 1. Simple Connector Functions

```python
from capture.connector import get_token, get_data, insert_data

# --- Using API token ---
api_token = "YOUR_API_TOKEN"

# --- Using user credentials ---
username = "your_username"
password = "your_password"
token = get_token(username, password)

# Query data
query = 'SELECT \"TestField\" from \"fiveYears\".\"TestMeasurement\" LIMIT 3'
database = "TestDB"
result = get_data(api_token, database, query)
print("Query result (API token):", result)

# Insert data (https://vintecc.github.io/Capture.Docs.External/docs/Cloud/DataApi/InsertData_ApiToken)
data_to_insert = {
    "Metrics": [
        {
            "Name": "MeasurementName",
            "Tags": {
                "SerialNumber": "123456",
                "MachineId": "Machine1"
            },
            "Fields": {
                "sensor1": 20
            },
            "Timestamp": "1585554027"
        },
        {
            "Name": "MeasurementName",
            "Tags": {
                "SerialNumber": "123457",
                "MachineId": "Machine2"
            },
            "Fields": {
                "sensor1": 30
            },
            "Timestamp": "1585554028"
        }
    ],
    "Timestamp": "1588760160"
}
success = insert_data(api_token, data_to_insert)
print("Insert success:", success)

```

---

## 2. CaptureClient (Synchronous Class)

```python
from capture.client import CaptureClient

# --- Using API token ---
client = CaptureClient(api_token="YOUR_API_TOKEN")

# --- Using user credentials ---
client = CaptureClient()
client.authenticate("your_username", "your_password")

# Query data
result = client.query(
    database="TestDB",
    query = 'SELECT \"TestField\" from \"fiveYears\".\"TestMeasurement\" LIMIT 3'

)
print("Query result (API token):", result)

# Insert data
data_to_insert = {
    "Metrics": [
        {
            "Name": "MeasurementName",
            "Tags": {
                "SerialNumber": "123456",
                "MachineId": "Machine1"
            },
            "Fields": {
                "sensor1": 20
            },
            "Timestamp": "1585554027"
        },
        {
            "Name": "MeasurementName",
            "Tags": {
                "SerialNumber": "123457",
                "MachineId": "Machine2"
            },
            "Fields": {
                "sensor1": 30
            },
            "Timestamp": "1585554028"
        }
    ],
    "Timestamp": "1588760160"
}
insert_result = client.insert_data(data_to_insert, database="TestDB", retention="autogen")
print("Insert result:", insert_result)

```

---

## 3. CaptureAsyncClient (Asynchronous Class)

```python
import asyncio
from capture.client import CaptureAsyncClient

async def main():
    # --- Using API token ---
    async with CaptureAsyncClient(api_token="YOUR_API_TOKEN") as client:
        result = await client.query(
            database="TestDB",
            query = 'SELECT \"TestField\" from \"fiveYears\".\"TestMeasurement\" LIMIT 3'

        )
        print("Query result (API token):", result)

        data_to_insert = {
            "Metrics": [
                {
                    "Name": "MeasurementName",
                    "Tags": {
                        "SerialNumber": "123456",
                        "MachineId": "Machine1"
                    },
                    "Fields": {
                        "sensor1": 20
                    },
                    "Timestamp": "1585554027"
                },
                {
                    "Name": "MeasurementName",
                    "Tags": {
                        "SerialNumber": "123457",
                        "MachineId": "Machine2"
                    },
                    "Fields": {
                        "sensor1": 30
                    },
                    "Timestamp": "1585554028"
                }
            ],
            "Timestamp": "1588760160"
        }
        insert_result = await client.insert(data_to_insert, database="InfrastructureMetrics", retention="autogen")
        print("Insert result (API token):", insert_result)

    # --- Using user credentials ---
    async with CaptureAsyncClient() as client:
        await client.authenticate("your_username", "your_password")
        result = await client.query(
            database="InfrastructureMetrics",
            query='SHOW TAG VALUES WITH KEY = "Company"'
        )
        print("Query result (user creds):", result)

        insert_result = await client.insert(data_to_insert)
        print("Insert result (user creds):", insert_result)

asyncio.run(main())
```

---

**Replace** `"YOUR_API_TOKEN"`, `"your_username"`, `"your_password"`, and adjust the `data_to_insert` as needed for your use case.  
These examples demonstrate both authentication methods, querying, and inserting data.