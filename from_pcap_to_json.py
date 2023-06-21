from scapy.all import *
import json
from time import time


start = time()
n_sample = "4"
print("Extracting data...")
scapy_cap = rdpcap("data/sample_" + n_sample + ".pcap")
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
with open("data/json_data_" + n_sample + ".json", "w") as outfile:
    outfile.write(data_string)

end = time()
print("Done in", (end - start) / 60, "min")
