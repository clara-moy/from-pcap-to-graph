"""Program that takes a .pcap file and creates a .json file with data from the .pcap file

Usage:
=====
    python3 from_pcap_to_json.py file_name

    file_name: name of the file (with the relative path) from which we want data
"""

__authors__ = "Clara Moy"
__contact__ = "c.m0y@yahoo.com"
__copyright__ = "MIT"
__date__ = "2023-06-26"


from datetime import datetime
import sys
from time import time

import json
from scapy.all import rdpcap


print("Extracting data...")
start = time()
file_name = sys.argv[1]
scapy_cap = rdpcap(file_name)
print("Creating dictionnary...")
data = {}
data["paquets"] = []


index = 0
for packet in scapy_cap:
    data["paquets"].append({"src": packet[0].src, "dst": packet[0].dst})

    try:
        data["paquets"][index].update({"type": packet[0].type})
    except AttributeError:
        data["paquets"][index].update({"type": None})

    try:
        data["paquets"][index].update({"ip_src": packet[1].psrc})
        data["paquets"][index].update({"ip_dst": packet[1].pdst})
    except (AttributeError, IndexError):
        data["paquets"][index].update({"ip_src": None})
        data["paquets"][index].update({"ip_dst": None})

    try:
        data["paquets"][index].update({"ip_src": packet[1].src})
        data["paquets"][index].update({"ip_dst": packet[1].dst})
    except (AttributeError, IndexError):
        pass

    try:
        data["paquets"][index].update({"proto": packet[1].proto})
    except (AttributeError, IndexError):
        data["paquets"][index].update({"proto": None})

    try:
        data["paquets"][index].update({"ttl": packet[1].ttl})
    except (AttributeError, IndexError):
        data["paquets"][index].update({"ttl": None})

    try:
        data["paquets"][index].update({"port_src": packet[2].sport})
        data["paquets"][index].update({"port_dst": packet[2].dport})
    except (AttributeError, IndexError):
        data["paquets"][index].update({"port_src": None})
        data["paquets"][index].update({"port_dst": None})

    index += 1


data_string = json.dumps(data)

print("Creating json file...")
dt_string = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
with open("data/json_data_" + dt_string + ".json", "w") as outfile:
    outfile.write(data_string)
end = time()
print("Done in", (end - start) / 60, "min")
