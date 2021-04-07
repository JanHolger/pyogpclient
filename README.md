# pyogpclient
Open Game Protocol Client for Python 3

## Usage
```python
from pyogpclient import OGPClient

client = OGPClient("example.com", 7776)
status = client.query()

print("Current Players: " + str(status["info"]["player_count"]) + " / " + str(status["info"]["slot_max"]))
```

## Response
- game_id
- info
    - game_name
    - type
    - type_name
    - password
    - proxy
    - os
    - os_name
    - host_name
    - host_name_color
    - connect_port
    - mod
        - name
        - id
        - size
        - version
        - url
        - author
    - game_type
    - game_mode
    - map
        - name
        - file_name
        - file_size
        - file_md5
        - version
        - url
        - author
    - next_map (see map)
    - player_count
    - slot_max
    - bot_count
    - reserved_slots

### Missing Fields (TODO)
- teams
- players
- rules
- addons
- limits