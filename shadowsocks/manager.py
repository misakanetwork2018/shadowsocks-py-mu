#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 clowwindy
# Copyright 2016 Howard Liu
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import, division, print_function, \
    with_statement

import errno
import traceback
import socket
import logging
import json
import collections

from shadowsocks import common, eventloop, tcprelay, udprelay, asyncdns, shell
from shadowsocks.crypto.aead import CIPHER_NONCE_LEN


BUF_SIZE = 1506
STAT_SEND_LIMIT = 50

# Get list of AEAD ciphers
aead_ciphers = CIPHER_NONCE_LEN.keys()


class Manager(object):

    def __init__(self, config):
        self._config = config
        self._relays = {}  # (tcprelay, udprelay)
        self._loop = eventloop.EventLoop()
        self._dns_resolver = asyncdns.DNSResolver()
        self._dns_resolver.add_to_loop(self._loop)

        self._statistics = collections.defaultdict(int)
        self._control_client_addr = None
        try:
            manager_address = config['manager_address']
            if ':' in manager_address:
                addr = manager_address.rsplit(':', 1)
                addr = addr[0], int(addr[1])
                addrs = socket.getaddrinfo(addr[0], addr[1])
                if addrs:
                    family = addrs[0][0]
                else:
                    logging.error('invalid address: %s', manager_address)
                    exit(1)
            else:
                addr = manager_address
                family = socket.AF_UNIX
            self._control_socket = socket.socket(family,
                                                 socket.SOCK_DGRAM)
            self._control_socket.bind(addr)
            self._control_socket.setblocking(False)
        except Exception as e:
            logging.error('Can not bind to manager address: %s' % e)
            exit(1)
        self._loop.add(self._control_socket,
                       eventloop.POLL_IN, self)
        # self._loop.add_periodic(self.handle_periodic)
        port_password = config['port_password']
        del config['port_password']
        config['crypto_path'] = config.get('crypto_path', dict())
        for port, password in port_password.items():
            a_config = config.copy()
            a_config['server_port'] = int(port)
            a_config['password'] = password
            self.add_port(a_config)

    def add_port(self, config):
        port = int(config['server_port'])
        servers = self._relays.get(port, None)
        if servers:
            logging.error("Server Exists:  P[%d], M[%s]" % (
                port, config['method']))
            return
        # Check if AEAD cipher is enforced
        if config['aead_enforcement'] and config['method'] not in aead_ciphers:
            logging.warning("AEAD Cipher Enforced - Rejected Server: P[%d], M[%s]" % (
                port, config['method']))
            return
        t = tcprelay.TCPRelay(config, self._dns_resolver, False,
                              self.stat_callback)
        u = udprelay.UDPRelay(config, self._dns_resolver, False,
                              self.stat_callback)
        t.add_to_loop(self._loop)
        u.add_to_loop(self._loop)
        self._relays[port] = (t, u)
        logging.info("Server Added:   P[%d], M[%s]" %
                     (port, config['method']))

    def remove_port(self, config):
        port = int(config['server_port'])
        servers = self._relays.get(port, None)
        if servers:
            logging.info("Server Removed: P[%d]" % port)
            t, u = servers
            t.close(next_tick=False)
            u.close(next_tick=False)
            del self._relays[port]
        else:
            logging.error("Svr Not Exists: P[%d], M[%s]" % (
                port, config['method']))

    def stat_port(self, config):
        port = int(config['server_port'])
        servers = self._relays.get(port, None)
        if servers:
            # Server is now running
            self._send_control_data(b'{"stat":"ok", "password":"%s", "method":"%s"}' % (
                servers[0]._config['password'], servers[0]._config['method']))
        else:
            # Server is not running
            self._send_control_data(b'{"stat":"ko"}')

    def handle_event(self, sock, fd, event):
        if sock == self._control_socket and event == eventloop.POLL_IN:
            data, self._control_client_addr = sock.recvfrom(BUF_SIZE)
            parsed = self._parse_command(data)
            if parsed:
                command, config = parsed
                a_config = self._config.copy()
                if command == 'transfer':
                    self.handle_periodic()
                else:
                    if config:
                        # let the command override the configuration file
                        a_config.update(config)
                    if 'server_port' not in a_config:
                        logging.error('can not find server_port in config')
                    else:
                        if command == 'add':
                            self.add_port(a_config)
                            self._send_control_data(b'ok')
                        elif command == 'remove':
                            self.remove_port(a_config)
                            self._send_control_data(b'ok')
                        elif command == 'stat':
                            self.stat_port(a_config)
                        elif command == 'ping':
                            self._send_control_data(b'pong')
                        else:
                            logging.error('unknown command %s', command)

    def _parse_command(self, data):
        # commands:
        # add: {"server_port": 8000, "password": "foobar"}
        # remove: {"server_port": 8000"}
        data = common.to_str(data)
        parts = data.split(':', 1)
        if len(parts) < 2:
            return data, None
        command, config_json = parts
        try:
            config = shell.parse_json_in_str(config_json)
            if 'method' in config:
                config['method'] = common.to_str(config['method'])
            return command, config
        except Exception as e:
            logging.error(e)
            return None

    def stat_callback(self, port, data_len):
        self._statistics[port] += data_len

    def handle_periodic(self):
        r = {}
        i = 0

        def send_data(data_dict):
            if data_dict:
                # use compact JSON format (without space)
                data = common.to_bytes(json.dumps(data_dict,
                                                  separators=(',', ':')))
                self._send_control_data(data)

        for k, v in self._statistics.items():
            r[k] = v
            i += 1
            # split the data into segments that fit in UDP packets
            if i >= STAT_SEND_LIMIT:
                send_data(r)
                r.clear()
                i = 0
        if len(r) > 0:
            send_data(r)
        self._send_control_data('e')
        self._statistics.clear()

    def _send_control_data(self, data):
        if not self._control_client_addr:
            return

        try:
            if type(data) is str:
                data = data.encode()
            self._control_socket.sendto(data, self._control_client_addr)
        except (socket.error, OSError, IOError) as e:
            error_no = eventloop.errno_from_exception(e)
            if error_no in (errno.EAGAIN, errno.EINPROGRESS,
                            errno.EWOULDBLOCK):
                return
            else:
                shell.print_exception(e)
                if self._config['verbose']:
                    traceback.print_exc()

    def run(self):
        self._loop.run()


def run(config, callback):
    try:
        Manager(config).run()
    except Exception as e:
        callback('Manager', e)
        logging.error('Unhandled exception is thrown in manager thread, exiting...')
        exit('manager thread crashed')


def test():
    import time
    import threading
    import struct
    from shadowsocks import cryptor

    logging.basicConfig(level=5,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    enc = []
    eventloop.TIMEOUT_PRECISION = 1

    def run_server():
        config = {
            'server': '127.0.0.1',
            'local_port': 1081,
            'port_password': {
                '8381': 'foobar1',
                '8382': 'foobar2'
            },
            'method': 'aes-256-cfb',
            'manager_address': '127.0.0.1:6001',
            'timeout': 60,
            'fast_open': False,
            'verbose': 2
        }
        manager = Manager(config)
        enc.append(manager)
        manager.run()

    t = threading.Thread(target=run_server)
    t.start()
    time.sleep(1)
    manager = enc[0]
    cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cli.connect(('127.0.0.1', 6001))

    # test add and remove
    time.sleep(1)
    cli.send(b'add: {"server_port":7001, "password":"asdfadsfasdf"}')
    time.sleep(1)
    assert 7001 in manager._relays
    data, addr = cli.recvfrom(1506)
    assert b'ok' in data

    cli.send(b'remove: {"server_port":8381}')
    time.sleep(1)
    assert 8381 not in manager._relays
    data, addr = cli.recvfrom(1506)
    assert b'ok' in data
    logging.info('add and remove test passed')

    # test statistics for TCP
    header = common.pack_addr(b'google.com') + struct.pack('>H', 80)
    data = cryptor.encrypt_all(b'asdfadsfasdf', 'aes-256-cfb',
                               header + b'GET /\r\n\r\n')
    tcp_cli = socket.socket()
    tcp_cli.connect(('127.0.0.1', 7001))
    tcp_cli.send(data)
    tcp_cli.recv(4096)
    tcp_cli.close()

    data, addr = cli.recvfrom(1506)
    data = common.to_str(data)
    assert data.startswith('stat: ')
    data = data.split('stat:')[1]
    stats = shell.parse_json_in_str(data)
    assert '7001' in stats
    logging.info('TCP statistics test passed')

    # test statistics for UDP
    header = common.pack_addr(b'127.0.0.1') + struct.pack('>H', 80)
    data = cryptor.encrypt_all(b'foobar2', 'aes-256-cfb',
                               header + b'test')
    udp_cli = socket.socket(type=socket.SOCK_DGRAM)
    udp_cli.sendto(data.encode(), ('127.0.0.1', 8382))
    tcp_cli.close()

    data, addr = cli.recvfrom(1506)
    data = common.to_str(data)
    assert data.startswith('stat: ')
    data = data.split('stat:')[1]
    stats = json.loads(data)
    assert '8382' in stats
    logging.info('UDP statistics test passed')

    manager._loop.stop()
    t.join()

if __name__ == '__main__':
    test()
