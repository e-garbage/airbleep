import subprocess
import re
from pythonosc import udp_client
from time import sleep
from rich.live import Live
from rich.table import Table
import mido
import random
import logging
import argparse
import os

### INITIALIZE ###
logging.basicConfig(level=logging.DEBUG, format="{asctime} [{levelname}] {message}", style="{", datefmt="%H:%M:%S") #Define logging config
mac_to_midi_note = {}  # Dictionary to map MAC address to MIDI note
station_volume = {} # Dictionary to store last known PWR for each BSSID to avoid repeated OSC messages
bssid_midi_notes = {} # Store the last known MIDI note per BSSID to avoid repeat sends
client_data = {}  # Dictionary to store client information by Station MAC address

def osc_setup(osc_ip, osc_port):
    """
    create osc udp client on given port and ip. 
    """
    logging.info("OSC setup...")
    osc_client = udp_client.SimpleUDPClient(osc_ip, osc_port)
    logging.debug(f"OSC udp open on port {osc_port} for interface {osc_ip}")
    return (osc_client)

def midi_setup ():
    """ 
    MIDI setup: Open all midi port available and broadcast on them 
    """
    logging.info("Midi setup..")
    logging.debug ("Following Midi interfaces availables. Send Midi msg to all")
    logging.debug((mido.get_output_names()))
    midi_ports = [mido.open_output(name) for name in mido.get_output_names()]
    return midi_ports

def clear():
    """
    clear system console
    """
    # for windows
    if os.name == 'nt':
        os.system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        os.system('clear')

def launch_airodump(interface):
    """
    Launch airodump-ng and capture its output.
    """
    process = subprocess.Popen(
        ['sudo', 'airodump-ng', interface, '--write-interval', '1', '--berlin', '1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        #text=True
    )
    try:
        for line in process.stdout:
            # Decode with errors ignored to handle non-UTF-8 characters
            decoded_line = line.decode('utf-8', errors='ignore')
            client_info = extract_client_info(decoded_line)
            if client_info:
                yield client_info
    except KeyboardInterrupt:
        process.terminate()
    finally:
        process.terminate()

def extract_client_info(output):
    """
    Extract BSSID, Station, PWR, Rate, Lost, Frames, Notes, and Probes from the airodump-ng output.
    """
    client_regex = re.compile(
        r'^\s*([0-9A-Fa-f:]{17}|\(not associated\))\s+'  # BSSID
        r'([0-9A-Fa-f:]{17})\s+'                         # Station
        r'(-?\d+)\s+'                                    # PWR
        r'(\d+\s-?\s\d+)\s+'                             # Rate
        r'(\d+)?\s*'                                     # Lost
        r'(\d+)?\s*'                                     # Frames
        r'(.*?)\s*'                                      # Notes
        r'(.*?)$'                                        # Probes
    )

    match = client_regex.search(output)
    if match:
        bssid = match.group(1).strip()
        station = match.group(2).strip()
        pwr = match.group(3).strip()
        rate = match.group(4).strip() if match.group(4) else ""
        lost = match.group(5).strip() if match.group(5) else ""
        frames = match.group(6).strip() if match.group(6) else ""
        notes = match.group(7).strip()  if match.group(7) else ""
        # Filter out non-allowed characters from probes
        probes = re.sub(r'[^0-9A-Za-z\s!@#$%^&*()_+\-=,.?]', '', match.group(8).strip())
        
        # Set probes to "unknown" if it is empty or only whitespace
        if not probes:
            probes = "unknown"
        if probes == "0K":
            probes = "unknown"
        # Strip "0k" if it appears at the end of the probes string
        if probes.endswith("0K"):
            probes = probes[:-2]
        return (bssid, station, pwr, rate, lost, frames, notes, probes)

    return None

def create_table(data):
    """
    Create a rich Table for displaying client data.
    Device = Station
    """
    table = Table(title="Wi-Fi Clients")
    table.add_column("BSSID", justify="center")
    table.add_column("Device", justify="center")
    table.add_column("PWR", justify="right")
    table.add_column("Rate", justify="right")
    table.add_column("Lost", justify="right")
    table.add_column("Frames", justify="right")
    table.add_column("Notes", justify="left")
    table.add_column("Probes", justify="left")

    # Add data rows
    for entry in data.values():
        bssid, station, pwr, rate, lost, frames, notes, probes = entry
        table.add_row(bssid, station, pwr, rate, lost, frames, notes, probes)

    return table

def send_midi(midi_ports, bssid, pwr):
    """
    Send a MIDI note based on the Station BSSID and power level. This MIDI note comes from the hashed value of the BSSID modulo 128.
    This means the corresponding note to a specific MAC address will change at each python run.
    """
    # Generate a MIDI note from the MAC address hash
    midi_note = (hash(bssid) % 128)  # Hash BSSID to get a MIDI note in range 0-127
    velocity = max(0, min(127, int((int(pwr) + 100) * 1.27)))  # Scale PWR to a 0-127 range

    # Create a MIDI note_on message
    msg = mido.Message('note_on', note=midi_note, velocity=velocity, channel=6)

    # Send the MIDI message to all connected ports
    for port in midi_ports:
        port.send(msg)

def bssid_pwr_to_osc(client_data, osc_client):
    """
    Send OSC messages for each Station BSSID (called client here).
    3 OSC channel are send everytime:
        - /client: str containg station BSSID
        - /pwr: float singal power 0-1
        - /probes: str with probes for each station
    """
    for entry in client_data.values():
        bssid, station, pwr, rate, lost, frames, notes, probes, *_ = entry
        try:
            pwr = int(pwr)
            volume = max(0, min(1, (pwr + 100) / 100))  # Normalize PWR to volume range (0 to 1)
            # Only send if volume has changed significantly to reduce traffic
            if station not in station_volume or abs(station_volume[station] - volume) > 0.001:
                station_volume[station] = volume
                osc_client.send_message("/client", station)
                osc_client.send_message("/pwr", volume)
                osc_client.send_message("/probes", probes)
                #logging.info(f"OSC sent for Device {station} with pwr {volume} . This device tries to connect to {probes} networks")

        except ValueError:
            continue  # Skip if PWR is not a valid integer

def main():
    clear()
    parser =argparse.ArgumentParser()
    parser.add_argument("-ip","--osc_ip", type=str, default="127.0.0.1", help="set the IP of the machine you want to send OSC messages to. By default it is set to localhost 127.0.0.1, this allow to loopback OSC messages on the same computer and make script communicate with another program such as Max4Live, PureData, TouchDesigner running locally.")
    parser.add_argument("-p", "--osc_port", type=int, default=10000, help="set the port of the machine you want to send OSC messages to. By Default it is set to port 10000")
    parser.add_argument("-i", "--interface", type=str, default="wlan0mon", help="Monitoring wifi interface name . It must already be in monitor mode. To do so use sudo airmon-ng start *interface_name*")
    args=parser.parse_args()
    osc_client=osc_setup(args.osc_ip, args.osc_port)
    midi_ports=midi_setup()
    logging.info(f"Monitoring nearby Wi-Fi clients on interface {args.interface}...")

    with Live(auto_refresh=True, refresh_per_second=10) as live:
        for client_info in launch_airodump(args.interface):
            station = client_info[1]
            pwr = client_info[2]
            client_data[station] = client_info
            table = create_table(client_data)
            bssid_pwr_to_osc(client_data, osc_client)
            send_midi(midi_ports, station, pwr)
            live.update(table)  # Update the live table with new data
if __name__ == "__main__":
    main()