#!/usr/bin/env python3

from pprint import pprint
import pynetbox
import json
import os

# Define variables
tagScope = os.environ["NETBOX_DHCP_SCOPE"]
token    = os.environ["NETBOX_TOKEN"]
url      = os.environ["NETBOX_URL"]
nb       = pynetbox.api(url, token=token)

# Loop over in-scope ranges
dhcp_prefixes = nb.ipam.prefixes.filter(tag=[tagScope])
for prefix in dhcp_prefixes:
  print("Fetching IP Addresses for prefix " + str(prefix))
  # Initialize the list of reservations
  reservations = []
  subnet = str(prefix).split("/")[0]

  addresses = nb.ipam.ip_addresses.filter(parent=prefix.prefix)
  for address in addresses:
    # Initialize the specific reservation and add the IP address.
    # Split the address, since netbox stores it in CIDR notation
    reservation = {}
    splitadd = address.address.split("/")
    reservation['ip-address'] = splitadd[0]

    # Also store additional information needed below.
    if address.assigned_object_id and address.assigned_object_type == 'dcim.interface':

      # IP Address has an assigned interface
      device = nb.dcim.interfaces.get(id=address.assigned_object_id)
      if device.mac_address is not None:
         reservation['hw-address'] = device.mac_address
      else:
         reservation.clear()
         continue

      if device.device.name is not None:
         reservation['hostname'] = device.device.name

      # Append the new found reservation to the list
      # if the entry exists, i.e. was not cleared.
      if reservation:
        reservations.append (reservation)

  with open ("/etc/kea/" + subnet + ".json", 'w') as outfile:
    json.dump (reservations, outfile, indent=4)
