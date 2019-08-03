#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, sky-joker
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: server_certificate_info
short_description: Get a certificate information from the server
author:
    - sky-joker (@sky-joker)
version_added: ''
description:
    - Get certificate subject, issuer, expiration date etc from server.
requirements:
    - python >= 2.7
    - pyOpenSSL
options:
    server:
        description:
            - FQDN or IP address to get the certificate.
        required: True
        type: str
    port:
        description:
            - HTTPS port number to connect.
        default: 443
        type: int
    method:
        description:
            - SSL/TLS version to use.(see https://docs.python.org/3/library/ssl.html#ssl.SSLContext)
        choices:
            - SSLv2_METHOD
            - SSLv3_METHOD
            - SSLv23_METHOD
            - TLSv1_METHOD
            - TLSv1_1_METHOD
            - TLSv1_2_METHOD
        default: SSLv23_METHOD
        type: str
    proxy_host:
        description:
            - Proxy host name or IP address to use.
        type: str
    proxy_port:
        description:
            - Proxy port number to connect.
        default: 8080
        type: int
'''

EXAMPLE = '''
- name: Get certificate information from server.
  server_certificate_info:
    server: www.example.com
    register: r

- debug: var=r

- name: Get certificate information from server using proxy.
  server_certificate_info:
    server: www.example.com
    http_proxy: 192.168.0.254
    http_port: 3128
    register: r

- debug: var=r
'''

RETURN = '''
certificate_info:
    description: Certificate information
    returned: success
    type: dict
    sample: {
                "algorithm": "sha256WithRSAEncryption",
                "changed": false,
                "issuer": {
                    "C": "US",
                    "CN": "DigiCert SHA2 Secure Server CA",
                    "O": "DigiCert Inc"
                },
                "not_after": "2020-12-02 12:00:00",
                "not_before": "2018-11-28 00:00:00",
                "serial_number": 21020869104500376438182461249190639870,
                "subject": {
                    "C": "US",
                    "CN": "www.example.org",
                    "L": "Los Angeles",
                    "O": "Internet Corporation for Assigned Names and Numbers",
                    "OU": "Technology",
                    "ST": "California"
                },
                "version": 2
            }
'''

import traceback

try:
    from OpenSSL import SSL
    HAS_OpenSSL = True
except ImportError:
    OpenSSL_IMP_ERR = traceback.format_exc()
    HAS_OpenSSL = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from datetime import datetime
import socket


def verify_callback(conn, cert, errnum, errdepth, ok):
    if ok:
        return True
    else:
        return False


def generate_certificate_info_structure(certificate_info):
    certificate_info_structure = {}
    for info in certificate_info:
        certificate_info_structure[info[0].decode("utf-8")] = info[1].decode("utf-8")

    return certificate_info_structure


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server=dict(type='str', required=True),
            port=dict(type='int', default=443),
            method=dict(type='str', default='SSLv23_METHOD', choices=['SSLv2_METHOD', 'SSLv3_METHOD', 'SSLv23_METHOD',
                                                                      'TLSv1_METHOD', 'TLSv1_1_METHOD',
                                                                      'TLSv1_2_METHOD']),
            proxy_host=dict(type='str'),
            proxy_port=dict(type='int', default=8080),
        ),
        supports_check_mode=False
    )

    if not HAS_OpenSSL:
        module.fail_json(msg=missing_required_lib('pyOpenSSL'), url='https://www.pyopenssl.org/en/stable/',
                         exception=OpenSSL_IMP_ERR)

    server = module.params['server']
    port = module.params['port']
    method = module.params['method']
    proxy_host = module.params['proxy_host']
    proxy_port = module.params['proxy_port']

    connection_fail = {}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        ctx = SSL.Context(getattr(SSL, method))
        ctx.set_verify(SSL.VERIFY_NONE, verify_callback)

        if proxy_host:
            try:
                connect = "CONNECT %s:%s HTTP/1.0\r\nConnection: close\r\n\r\n" % (server, port)
                sock.connect((proxy_host, proxy_port))
                sock.send(connect.encode())
                sock.recv(4096)
                ssl_conn = SSL.Connection(ctx, sock)
            except Exception as e:
                connection_fail[server] = e

        else:
            try:
                ssl_conn = SSL.Connection(ctx, sock)
                ssl_conn.connect((server, port))
            except Exception as e:
                connection_fail[server] = e

        if not connection_fail:
            ssl_conn.set_connect_state()
            ssl_conn.do_handshake()
            certificate = ssl_conn.get_peer_certificate()

            version = certificate.get_version()
            algorithm = certificate.get_signature_algorithm().decode('utf-8')
            issuer = generate_certificate_info_structure(certificate.get_issuer().get_components())
            subject = generate_certificate_info_structure(certificate.get_subject().get_components())
            not_before = datetime.strptime(certificate.get_notBefore().decode('ascii'), "%Y%m%d%H%M%SZ")
            not_after = datetime.strptime(certificate.get_notAfter().decode('ascii'), "%Y%m%d%H%M%SZ")
            serial_number = certificate.get_serial_number()

            certificate_info_result = {
                "connection": True,
                "server": server,
                "version": version,
                "algorithm": algorithm,
                "issuer": issuer,
                "subject": subject,
                "not_before": not_before.strftime('%Y-%m-%d %H:%M:%S'),
                "not_after": not_after.strftime('%Y-%m-%d %H:%M:%S'),
                "serial_number": ('0%x' % serial_number).upper()
            }
        else:
            certificate_info_result = {
                "connection": False,
                "server": server,
                "msg": str(connection_fail[server])
            }

        result = dict(changed=False)
        module.exit_json(**result, certificate_info=certificate_info_result)


if __name__ == "__main__":
    main()
