# -*-coding:UTF-8 -*-

import os
import tempfile
import urllib2
import time

import sys
from cloudify import ctx
from cloudify.decorators import operation
# import the NonRecoverableError class
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause


def verify_server_is_up(port):
    for attempt in range(15):
        try:
            response = urllib2.urlopen("http://localhost:{0}".format(port))
            response.read()
            break
        except BaseException:
            _, last_ex, last_tb = sys.exc_info()
            time.sleep(1)
    else:
        raise NonRecoverableError(
            "Failed to start HTTP webserver",
            causes=[exception_to_error_cause(last_ex, last_tb)])


@operation
def start(**kwargs):
    webserver_root = tempfile.mkdtemp()
    ctx.instance.runtime_properties['webserver_root'] = webserver_root

    webserver_port = ctx.node.properties['port']

    with open(os.path.join(webserver_root, 'index.html'), 'w') as f:
        f.write('<p>Hello Cloudify!</p>')

    command = 'cd {0}; nohup python -m SimpleHTTPServer {1} > /dev/null 2>&1' \
              ' & echo $! > python-webserver.pid'.format(webserver_root, webserver_port)

    ctx.logger.info('Starting HTTP server using: {0}'.format(command))
    os.system(command)

    # verify
    verify_server_is_up(webserver_port)


@operation
def stop(**kwargs):
    # setting this runtime property allowed us to refer to properties which
    # are set during runtime from different time in the node instance's lifecycle
    webserver_root = ctx.instance.runtime_properties['webserver_root']
    try:
        with open(os.path.join(webserver_root, 'python-webserver.pid'), 'r') as f:
            pid = f.read().strip()
        ctx.logger.info('Stopping HTTP server [pid={0}]'.format(pid))
        os.system('kill -9 {0}'.format(pid))
    except IOError:
        ctx.logger.info('HTTP server is not running!')
