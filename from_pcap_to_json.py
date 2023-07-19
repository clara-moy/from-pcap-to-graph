"""
Takes a .pcap file and creates a .json file with data from the .pcap file

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
import dpkt
import socket
from dpkt.compat import compat_ord

import json
from scapy.all import rdpcap


def mac_addr(address):
    """Convert a MAC address to a readable/printable string

    Args:
        address (str): a MAC address in hex form (e.g. '\x01\x02\x03\x04\x05\x06')
    Returns:
        str: Printable/readable MAC address
    """
    return ":".join("%02x" % compat_ord(b) for b in address)


def inet_to_str(inet):
    """Convert inet object to a string

    Args:
        inet (inet struct): inet network address
    Returns:
        str: Printable/readable IP address
    """
    # First try ipv4 and then ipv6
    try:
        return socket.inet_ntop(socket.AF_INET, inet)
    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)


print("Extracting data...")
start = time()
file_name = sys.argv[1]
scapy_cap = rdpcap(file_name)
print("Creating dictionnary...")
data = {}
data["paquets"] = []


with open(file_name, "rb") as f:
    pcap = dpkt.pcap.Reader(f)
    index = 0
    for ts, buf in pcap:
        eth = dpkt.ethernet.Ethernet(buf)
        ip = eth.data
        data["paquets"].append(
            {
                "src": mac_addr(eth.src),
                "dst": mac_addr(eth.dst),
                "ts": str(datetime.fromtimestamp(ts)),
            }
        )

        try:
            data["paquets"][index].update({"type": eth.type})
        except AttributeError:
            data["paquets"][index].update({"type": None})

        try:
            data["paquets"][index].update({"ip_src": inet_to_str(ip.src)})
            data["paquets"][index].update({"ip_dst": inet_to_str(ip.dst)})
        except (AttributeError, IndexError):
            data["paquets"][index].update({"ip_src": None})
            data["paquets"][index].update({"ip_dst": None})

        # try:
        #     data["paquets"][index].update({"ttl": ip.ttl})
        # except (AttributeError, IndexError):
        #     data["paquets"][index].update({"ttl": None})

        try:
            tcp = ip.data
            data["paquets"][index].update({"port_src": tcp.sport})
            data["paquets"][index].update({"port_dst": tcp.dport})
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
