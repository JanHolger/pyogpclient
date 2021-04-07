import socket

def VarBitArray(bits):
    if type(bits) == list:
        vba = b''
        for bi in range(len(bits)):
            b = bits[bi]
            cb = 0
            for i in range(7):
                if i < len(b) and b[i]:
                    cb = cb + 2 ** i
            if bi < len(bits) - 1:
                cb = cb + 2 ** 7
            vba = vba + cb.to_bytes(1, 'little')
        return vba
    elif type(bits) == bytes:
        ba = []
        has_next = True
        while has_next:
            cb = bits[len(ba)]
            has_next = ((cb >> 7) % 2) == 1
            ca = []
            for i in range(0, 7):
                ca.append(True if ((cb >> i) % 2) == 1 else False)
            ba.append(ca)
        return ba
    else:
        raise TypeError()

FULL_OGP_QUERY = VarBitArray([[1, 1, 1, 1, 1], [1]]) + VarBitArray([[1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1]]) + VarBitArray([[1, 1, 1, 1, 1]]) + VarBitArray([[1, 1, 1, 1, 1, 1]]) + VarBitArray([[1, 1, 1, 1, 1, 1]]) + VarBitArray([[1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1]]) + VarBitArray([[1, 1, 1, 1]])

class OGPClient:

    TYPE_PING = b'\x00'
    TYPE_QUERY = b'\x01'
    TYPE_RCON = b'\x02' # Not documented
    TYPE_MASTER_SERVER_UPLINK = b'\x03'
    TYPE_ERROR = b'\xFF'

    ERROR_BANNED = b'\x00'
    ERROR_INVALID_TYPE = b'\x01'
    ERROR_INVALID_VALUE = b'\x02'
    ERROR_INVALID_CHALLENGE_NUMBER = b'\x03'
    ERROR_INVALID_QUERY = b'\x04'

    def __init__(self, ip, port, timeout = 0.5):
        self.with_flags = False
        self.ip = ip
        self.port = port
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        self.challenge_number = 0

    def request_challenge_number(self):
        self.send_request(OGPClient.TYPE_QUERY)
        self.challenge_number = int.from_bytes(self.recv_response()["message"][-4:], 'little')

    def parse_var_uint(self, message):
        value = message[0]
        if value < 254:
            return (message[1:], value)
        elif value == 254:
            return (message[3:], int.from_bytes(message[1:3]))
        else:
            return (message[5:], int.from_bytes(message[1:5]))

    def parse_sz_string(self, message):
        pos = 0
        while message[pos] != 0:
            pos = pos + 1
        return (message[pos+1:], message[:pos].decode("utf-8"))

    def parse_modinfo(self, message):
        parsed = {
            "id": None,
            "size": None,
            "version": None,
            "url": None,
            "author": None
        }
        message, parsed["name"] = self.parse_sz_string(message)
        flags = VarBitArray(message)
        message = message[len(flags):]
        if flags[0][0]:
            message, parsed["id"] = self.parse_sz_string(message)
        if flags[0][1]:
            parsed["size"] = int.from_bytes(message[:4], 'little')
            message = message[4:]
        if flags[0][2]:
            message, parsed["version"] = self.parse_sz_string(message)
        if flags[0][3]:
            message, parsed["url"] = self.parse_sz_string(message)
        if flags[0][4]:
            message, parsed["author"] = self.parse_sz_string(message)
        return (message, parsed)

    def parse_mapinfo(self, message, flags):
        parsed = {}
        message, parsed["name"] = self.parse_sz_string(message)
        if flags[0][0]:
            message, parsed["file_name"] = self.parse_sz_string(message)
        if flags[0][1]:
            parsed["file_size"] = int.from_bytes(message[:4], 'little')
            message = message[4:]
        if flags[0][2]:
            parsed["file_md5"] = message[:16]
            message = message[16:]
        if flags[0][3]:
            message, parsed["version"] = self.parse_sz_string(message)
        if flags[0][4]:
            message, parsed["url"] = self.parse_sz_string(message)
        if flags[0][5]:
            message, parsed["author"] = self.parse_sz_string(message)
        return (message, parsed)

    def parse_colorinfo(self, message):
        message, size = self.parse_var_uint(message)
        colors = []
        for i in range(size):
            message, pos = self.parse_var_uint(message)
            color = {
                "position": pos,
                "value": message[0],
                "value16": None
            }
            message = message[1:]
            if color["value"] >= 0x90 or color["value"] <= 0x9f:
                color["value16"] = int.from_bytes(message[0:2], 'little')
                message = message[2:]
            colors.append(color)
        return colors

    def parse_serverinfo(self, message, coloredNames = False):
        flags = VarBitArray(message)
        parsed = {
            "game_name": None,
            "type": None,
            "type_name": None,
            "password": None,
            "proxy": None,
            "os": None,
            "os_name": None,
            "host_name": None,
            "host_name_color": None,
            "connect_port": None,
            "mod": None,
            "game_type": None,
            "game_mode": None,
            "map": None,
            "next_map": None,
            "player_count": None,
            "slot_max": None,
            "bot_count": None,
            "reserved_slots": None
        }
        message = message[len(flags):]
        if self.with_flags:
            parsed["flags"] = flags
        if flags[0][0]:
            message, parsed["game_name"] = self.parse_sz_string(message)
        if flags[0][1]:
            gameFlags = VarBitArray(message)
            message = message[len(gameFlags):]
            parsed["type"] = (1 if gameFlags[0][1] else 0) + (2 if gameFlags[0][0] else 0)
            parsed["type_name"] = {
                0: "Unknown",
                1: "Listen",
                2: "Dedicated"
            }[parsed["type"]]
            parsed["password"] = gameFlags[0][2]
            parsed["proxy"] = gameFlags[0][3]
            parsed["os"] = (1 if gameFlags[0][6] else 0) + (2 if gameFlags[0][5] else 0)
            parsed["os_name"] = {
                0: "Unknown",
                1: "Windows",
                2: "Linux",
                3: "Mac"
            }[parsed["os"]]
        if flags[0][2]:
            message, parsed["host_name"] = self.parse_sz_string(message)
            if coloredNames:
                message, parsed["host_name_color"] = self.parse_colorinfo(message)
        if flags[0][3]:
            parsed["connect_port"] = int.from_bytes(message[0:2], 'little')
            message = message[2:]
        if flags[1][0]:
            message, parsed["mod"] = self.parse_modinfo(message)
        if flags[1][1]:
            message, parsed["game_type"] = self.parse_sz_string(message)
        if flags[1][2]:
            message, parsed["game_mode"] = self.parse_sz_string(message)
        if flags[1][3]:
            mapFlags = VarBitArray(message)
            message = message[len(mapFlags):]
            message, parsed["map"] = self.parse_mapinfo(message, mapFlags)
            if flags[1][4]:
                message, parsed["next_map"] = self.parse_mapinfo(message, mapFlags)
        if flags[2][0]:
            message, parsed["player_count"] = self.parse_var_uint(message)
        if flags[2][1]:
            message, parsed["slot_max"] = self.parse_var_uint(message)
        if flags[2][2]:
            message, parsed["bot_count"] = self.parse_var_uint(message)
        if flags[2][3]:
            message, parsed["reserved_slots"] = self.parse_var_uint(message)
        return (message, parsed)

    def parse_teams(self, message):
        return (message, [])

    def parse_players(self, message):
        return (message, [])

    def parse_rules(self, message):
        return (message, [])

    def parse_addons(self, message):
        return (message, [])

    def parse_limits(self, message):
        return (message, [])

    def query(self, query = FULL_OGP_QUERY,):
        if self.challenge_number == 0:
            self.request_challenge_number()
        self.send_request(OGPClient.TYPE_QUERY, query)
        response = self.recv_response()
        if response["type"] == OGPClient.TYPE_ERROR:
            raise Exception(response["error_message"])
        if response["type"] != OGPClient.TYPE_QUERY:
            raise Exception("Invalid response type")
        message = response["message"]
        parsed = {
            "game_id": int.from_bytes(message[0:2], 'little'),
            "info": None,
            "teams:": None,
            "players": None,
            "rules": None,
            "addons": None,
            "limits": None
        }
        flags = VarBitArray(message[2:])
        message = message[2+len(flags):]
        if len(flags) == 1:
            flags.append([False])
        if self.with_flags:
            parsed["flags"] = flags
        if flags[0][0]:
            message, parsed["info"] = self.parse_serverinfo(message, flags[1][0])
        if flags[0][1]:
            message, parsed["teams"] = self.parse_teams(message)
        if flags[0][2]:
            message, parsed["players"] = self.parse_players(message)
        if flags[0][3]:
            message, parsed["rules"] = self.parse_rules(message)
        if flags[0][4]:
            message, parsed["addons"] = self.parse_addons(message)
        if flags[0][5]:
            message, parsed["limits"] = self.parse_limits(message)
        return parsed

    def recv_response(self):
        response, addr = self.sock.recvfrom(1024)
        if response[0:8] != b'\xFF\xFF\xFF\xFFOGP\x00':
            raise Exception('Invalid response')
        hsize = response[8]
        parsed = {
            "type": response[9:10],
            "flags": VarBitArray(response[10:]),
            "request_id": 0,
            "message": response[8+hsize:]
        }
        offset = 10+len(parsed["flags"])
        if parsed["flags"][0][1]:
            parsed["challenge_number"] = int.from_bytes(response[offset:offset+5], 'little')
            offset = offset + 4
        if parsed["flags"][0][2]:
            parsed["request_id"] = int.from_bytes(response[offset:offset+5], 'little')
            offset = offset + 4
        if parsed["type"] == OGPClient.TYPE_ERROR:
            parsed["error"] = parsed["message"][0:1]
            parsed["error_message"] = {
                OGPClient.ERROR_BANNED: 'Banned',
                OGPClient.ERROR_INVALID_TYPE: 'Invalid Type',
                OGPClient.ERROR_INVALID_VALUE: 'Invalid Value',
                OGPClient.ERROR_INVALID_CHALLENGE_NUMBER: 'Invalid Challenge Number',
                OGPClient.ERROR_INVALID_QUERY: 'Invalid Query'
            }[parsed["error"]]
        return parsed

    def send_request(self, message_type, message = b''):
        request = b'\xFF\xFF\xFF\xFFOGP\x00\x07' + message_type + VarBitArray([[0,1,0,0,1]]) + self.challenge_number.to_bytes(4, 'little') + message
        self.sock.sendto(request, (self.ip, self.port))
