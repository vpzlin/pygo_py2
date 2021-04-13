# -*- coding: UTF-8 -*-
import sys
import os
import time
import datetime
import ConfigParser
import socket
import yaml

import paramiko

"""
    [ Run Before Using ]
        yum install -y python-paramiko.noarch
        yum install -y python2-pyyaml.noarch
"""

# CONFIG_FILE_PATH = 'config.ini'
HOSTS_FILE_PATH = 'hosts.txt'
SEPARATOR = '|@|'
DEFAULT_LINUX_USERNAME = 'root'
DEFAULT_LINUX_USER_PATH = '/root'

today = str(datetime.date.today()).replace('-', '')
es_home_path = '/opt/elastic/elasticsearch'
es_new_packages_local_path = 'packages/elasticsearch-6.8.9.tar.gz'
es_data_backup_dir = '/data'


def get_servers_info():
    servers_info = []
    with open(HOSTS_FILE_PATH, 'r') as hosts_info_file:
        for line in hosts_info_file.readlines():
            line = line.strip()
            if len(line) == 0 or line[0] == '#':
                continue
            servers_info.append(line)
    return servers_info


def get_python_version():
    version = '{major}.{minor}'.format(major=sys.version_info.major, minor=sys.version_info.minor)
    return version


def sftp_put(local_path, target_path, host, port, username='', password=''):
    """
    sftp-put function
    :param local_path:
    :param target_path:
    :param host:
    :param port:
    :param username:
    :param password:
    :return:
    """
    try:
        scp = paramiko.Transport(host, port)
        if len(username) > 0:
            scp.connect(username=username, password=password)
        else:
            key = paramiko.RSAKey.from_private_key_file('{DEFAULT_LINUX_USER_PATH}/.ssh/id_rsa'.
                                                        format(DEFAULT_LINUX_USER_PATH=DEFAULT_LINUX_USER_PATH))
            scp.connect(username=DEFAULT_LINUX_USERNAME, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(scp)
        print 'Start to put file [{local_path}] to host [{host}] path [{target_path}].' \
            .format(target_path=target_path, host=host, local_path=local_path)
        sftp.put(local_path, target_path)
        print 'Finished to put file [{local_path}] to host [{host}] path [{target_path}].'\
            .format(target_path=target_path, host=host, local_path=local_path)
        return True
    except Exception as e:
        print 'Failed to put file [{local_path}] to host [{host}] path [{target_path}]. More info:\n{error_info}' \
            .format(target_path=target_path, host=host, local_path=local_path, error_info=e.message)


def sftp_get(target_path, local_path, host, port, username='', password=''):
    """
    sftp-get function
    :param target_path:
    :param local_path:
    :param host:
    :param port:
    :param username:
    :param password:
    :return:
    """
    try:
        scp = paramiko.Transport((host, port))
        if len(username) > 0:
            scp.connect(username=username, password=password)
        else:
            key = paramiko.RSAKey.from_private_key_file('{DEFAULT_LINUX_USER_PATH}/.ssh/id_rsa'.
                                                        format(DEFAULT_LINUX_USER_PATH=DEFAULT_LINUX_USER_PATH))
            scp.connect(username=DEFAULT_LINUX_USERNAME, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(scp)
        print 'Start to get file [{target_path}] from host [{host}] to local path [{local_path}].' \
            .format(local_path=local_path, host=host, target_path=target_path)
        sftp.get(target_path, local_path)
        print 'Finished to get file [{target_path}] from host [{host}] to local path [{local_path}].' \
            .format(local_path=local_path, host=host, target_path=target_path)
        return True
    except Exception as e:
        print 'Failed to get file [{target_path}] from host [{host}] to local [{local_path}]. More info:\n{error_info}'\
            .format(target_path=target_path, host=host, local_path=local_path, error_info=e.message)


def start():
    """
    start to upgrade new version
    :return:
    """
    # check es new packages
    if os.path.exists(es_new_packages_local_path) is False:
        raise Exception('Elasticsearch new version package file [{es_new_packages_path}] does not exists!'
                        .format(es_new_packages_path=es_new_packages_local_path))

    for server_info in get_servers_info():
        """ get server info 
        """
        args1 = server_info.split(SEPARATOR)
        host = args1[0].strip()
        port = 22
        if len(args1) > 1 and len(args1[1].strip()) > 0:
            port = int(args1[1].strip())
        username = ''
        password = ''
        if len(args1) > 3 and len(args1[2].strip()) > 0:
            username = args1[2].strip()
            password = args1[3].strip()

        """ scp file to host
        """
        # if sftp_put(es_new_packages_local_path, os.path.basename(es_new_packages_local_path),
        #             host, port, username, password) is False:
        #     continue

        try:
            """ connect to server """
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=host, port=port, username=username, password=password)
            # sleep 2 seconds to avoid cache errors
            time.sleep(2)

            """ read es config """
            stdin, stdout, stderr = ssh_client.exec_command('cat {es_home_path}/config/elasticsearch.yml'
                                                            .format(es_home_path=es_home_path))
            es_config = yaml.load(stdout)

            """ close connection """
            ssh_client.close()
        except paramiko.ssh_exception.AuthenticationException as e:
            print 'Failed to ssh to host [{host}]: authentication failure! More info:\n{error}'.format(host=host, error=e.message)
        except socket.error as e:
            print 'Failed to ssh to host [{host}]: socket error! More info:\n{error}'.format(host=host, error=e.message)
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            print 'Failed to ssh to host [{host}]: no valid connections! More info:\n{error}'.format(host=host, error=e.message)
        except Exception as e:
            print 'Failed on host [{host}]! More info:\n{error}'.format(host=host, error=e.message)


def rollback():
    """
    rollback to previous version
    :return:
    """


def check():
    """
    check service status
    :return:
    """


if __name__ == '__main__':
    """ check python version """
    if get_python_version() != '2.7':
        raise Exception('Please run with Python 2.7!')

    """ check config file """
    # if os.path.exists(CONFIG_FILE_PATH) is False:
    #     raise Exception('Config file [{CONFIG_FILE_PATH}] does not exists!'.format(CONFIG_FILE_PATH=CONFIG_FILE_PATH))
    # if os.path.isfile(CONFIG_FILE_PATH) is False:
    #     raise Exception('Path [{CONFIG_FILE_PATH}] is not a config file!'.format(CONFIG_FILE_PATH=CONFIG_FILE_PATH))

    """ check parameters inputted """
    if len(sys.argv) <= 1 or sys.argv[1].upper() not in ['START', 'ROLLBACK', 'CHECK']:
        print '[ Example ] \n' \
              '    python {file_path_scripts} start \n' \
              '    python {file_path_scripts} rollback \n' \
              '    python {file_path_scripts} check '.format(file_path_scripts=sys.argv[0])
        sys.exit(1)

    """ run scripts """
    if sys.argv[1].upper() == 'START':
        start()
    elif sys.argv[1].upper() == 'ROLLBACK':
        rollback()
    elif sys.argv[1].upper() == 'CHECK':
        check()
