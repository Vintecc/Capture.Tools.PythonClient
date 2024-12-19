from typing import Dict, List


def make_insert_ready(data: List[Dict]):
    for record in data:
        if 'Tags' in record:
            for tag in record['Tags']:
                record['Tags'][tag] = str(record['Tags'][tag])
        else :
            record['Tags'] = {}
            
        if 'Fields' in record:
            for field in record['Fields']:
                if not isinstance(record['Fields'][field], str):
                    record['Fields'][field] = float(record['Fields'][field])
        else:
            raise ValueError("Fields are required in each record.")
        
        if 'Timestamp' in record:
            record['Timestamp'] = str(record['Timestamp'])
        else:
            raise ValueError("Timestamp is required in each record.")
        
        if 'Name' not in record:
            raise ValueError("Name is required in each record.")
        
    return data