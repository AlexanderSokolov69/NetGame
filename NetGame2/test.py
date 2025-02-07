import http.client
conn = http.client.HTTPConnection("ifconfig.me")
conn.request("GET", "/ip")
responce = conn.getresponse().read()
print(responce)

import socket

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(local_ip, hostname)
