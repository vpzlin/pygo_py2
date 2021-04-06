# -*- coding: UTF-8 -*-
import os
import sys
import socket
import time

import paramiko

""" 使用前需先执行：
        yum install -y python-paramiko.noarch
"""

SEPARATOR = '|@|'


def get_python_version():
    version = '{major}.{minor}'.format(major=sys.version_info.major, minor=sys.version_info.minor)
    return version


def change_user_password():
    path_hosts_info_file = sys.argv[2]
    if os.path.exists(path_hosts_info_file) is False:
        raise Exception('【错误】服务器配置文件 {path_hosts_info_file} 不存在！'.format(path_hosts_info_file=path_hosts_info_file))

    """ 读取服务器用户名、密码等信息 """
    servers_info = []
    with open(path_hosts_info_file, "r") as hosts_info_file:
        line_no = 0
        for line in hosts_info_file.readlines():
            line_no += 1
            line = line.strip()
            if len(line) == 0 or line[0] == '#':
                continue

            str_line_info = '需将每行服务器信息用分隔符 {sep} 拆成多列。\n' \
                            '格式参考：192.168.1.1{sep}22{sep}root{sep}pasword_old{sep}password_new \n' \
                            '    第1列：服务器IP或hostname \n' \
                            '    第2列：连接服务器的ssh端口 \n' \
                            '    第3列：要修改密码的用户名 \n' \
                            '    第4列：原始密码 \n' \
                            '    第5列：新密码'.format(sep=SEPARATOR)
            line_info = line.split(SEPARATOR)
            if len(line_info) != 5:
                raise Exception('【错误】第{line_no}行的列信息不符合规范！\n{str_line_info}'
                                .format(line_no=line_no, str_line_info=str_line_info))
            server_info = {'host': line_info[0].strip(),
                           'port': int(line_info[1].strip()),
                           'username': line_info[2].strip(),
                           'password_old': line_info[3],
                           'password_new': line_info[4]}
            servers_info.append(server_info)

    """ 批量修改用户名、密码 """
    for server_info in servers_info:
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # 连接服务器
            ssh_client.connect(hostname=server_info.get('host'), port=server_info.get('port'),
                               username=server_info.get('username'), password=server_info.get('password_old'))
            # 进程休眠1分钟，否则会有缓冲区问题而报错
            time.sleep(1)
            # 修改密码
            ssh_client.exec_command('echo "%s"|passwd --stdin root' % server_info.get('password_new'))
            ssh_client.close()
            print '【成功】已修改服务器 {host} 用户 {username} 的密码为新密码 {password_new}'. \
                format(host=server_info.get('host'), username=server_info.get('username'), password_new=server_info.get('password_new'))
        except paramiko.ssh_exception.AuthenticationException:
            print '【失败】修改服务器 {host} 用户 {username} 的密码失败，用户名或密码错误！' \
                .format(host=server_info.get('host'), username=server_info.get('username'))
        except socket.error:
            print '【失败】连接服务器 {host}:{port} 失败！请检服务器 {host}:{port} 是否能正常连接。' \
                .format(host=server_info.get('host'), port=server_info.get('port'))
        except paramiko.ssh_exception.NoValidConnectionsError:
            print '【失败】连接服务器 {host}:{port} 失败！请检端口 {port} 是否配置正确。' \
                .format(host=server_info.get('host'), port=server_info.get('port'))
        except Exception as e:
            print '【失败】连接服务器 {host}:{port} 失败！{error}'\
                .format(host=server_info.get('host'), port=server_info.get('port'), error=e.message)


if __name__ == '__main__':
    if get_python_version() != '2.7':
        raise Exception('【错误】请以Python2.7运行该脚本！')

    str_tip = '【脚本运行方法】\n' \
              '    python2 {scripts_name} change_user_password 配置文件路径'.format(scripts_name=sys.argv[0])

    if len(sys.argv) <= 1:
        print str_tip
        raise Exception('【错误】脚本运行参数不能为空！')
    run_method = sys.argv[1].upper()
    if run_method == 'CHANGE_USER_PASSWORD':
        if len(sys.argv) < 3:
            raise Exception('【错误】脚本运行参数错误：缺少参数”配置文件路径“！')
        change_user_password()
    else:
        print '【错误】脚本运行参数错误！'
        print str_tip
