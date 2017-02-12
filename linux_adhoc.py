#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import socket
import struct

from subprocess import check_call


WIFI_SSID = 'KnowledgeNet'  # ad-hoc network SSID
WIFI_FREQUENCY = 2417  # ad-hoc network frequency in MHz

ETHERNET_PROTOCOL = 0x0700  # non-standard ethernet protocol number
BROADCAST_ADDRESS = b'\xff' * 6  # ethernet broadcast address

_ethernet_frame = struct.Struct('! 6s 6s H')  # binary ethernet frame format


def _make_frame(source, destination, payload):
    """ Make an ethernet frame. """
    return _ethernet_frame.pack(destination, source, ETHERNET_PROTOCOL) + payload


def format_mac(mac_address):
    """ Returns the colon separated hex representation. """
    return ':'.join(f'{byte:02x}' for byte in mac_address)


def configure(interface):
    """ Configure the WLAN interface appropriately. """
    # disable network-manager for all WIFI interfaces
    check_call(['nmcli', 'r', 'wifi', 'off'])
    # unblock the WLAN interface
    check_call(['rfkill', 'unblock', 'wlan'])
    # shut network link down
    check_call(['ip', 'link', 'set', interface, 'down'])
    # reconfigure the WLAN interface to IBSS (ad-hoc) mode
    check_call(['iw', interface, 'set', 'type', 'ibss'])
    # set up the network link
    check_call(['ip', 'link', 'set', interface, 'up'])
    # join the IBSS (ad-hoc) network
    check_call(['iw', interface, 'ibss', 'join', WIFI_SSID, str(WIFI_FREQUENCY)])


class DataLink:
    """ Interface to the 802.11 data link layer. """

    def __init__(self, interface):
        self.interface = interface
        protocol = socket.ntohs(ETHERNET_PROTOCOL)
        self.socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, protocol)
        self.socket.bind((interface, 0))
        self.address = self.socket.getsockname()[4]

    def broadcast(self, payload):
        """ Broadcast to all nodes within range. """
        self.socket.send(_make_frame(self.address, BROADCAST_ADDRESS, payload))

    def send(self, address, payload):
        """ Send a packet to a specific node in range. """
        self.socket.send(_make_frame(self.address, address, payload))

    def recv(self):
        """ Receive data sent by other nodes in range. """
        data, address = self.socket.recvfrom(4096)
        destination, source, protocol = _ethernet_frame.unpack(data[:_ethernet_frame.size])
        payload = data[_ethernet_frame.size:]
        return destination, source, payload
