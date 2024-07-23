#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paramiko
import sys
import smtplib
import socket
import os
import configparser
import datetime
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 程序banner
BANNER = """
SSH连接和文件传输工具
版本: 1.4
时间: 2024/7/23
"""

def check_config_file():
    if not Path('config.ini').exists():
        logging.warning("未找到 config.ini 文件。邮件通知功能将不可用。")

def get_config(section, key):
    """从配置文件中读取配置"""
    config = configparser.ConfigParser()
    config_path = Path('config.ini')
    if not config_path.exists():
        raise FileNotFoundError(f"未找到配置文件: {config_path}")
    config.read(config_path)
    return config.get(section, key)

def ssh_connect(hostname, port, username, password=None, key_filename=None):
    """建立SSH连接"""
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if key_filename:
            ssh_client.connect(hostname, port=port, username=username, key_filename=key_filename)
        else:
            ssh_client.connect(hostname, port=port, username=username, password=password)
        return ssh_client
    except paramiko.AuthenticationException:
        return None
    except paramiko.SSHException:
        return None
    except socket.error:
        return None
    except Exception:
        return None

def ssh_client_connection(hostname):
    """尝试SSH客户端连接"""
    with open("username.txt", 'r') as f:
        usernames = f.read().splitlines()
    with open("password.txt", 'r') as f:
        passwords = f.read().splitlines()

    max_attempts = 50
    attempt_count = 0
    failed_attempts = 0

    for username in usernames:
        for password in passwords:
            if attempt_count >= max_attempts:
                logging.warning(f"达到最大尝试次数 {max_attempts}，停止尝试")
                logging.info(f"总共失败 {failed_attempts} 次")
                return False
            
            ssh_client = ssh_connect(hostname, 22, username, password)
            if ssh_client:
                stdin, stdout, stderr = ssh_client.exec_command('whoami', timeout=10)
                print(stdout.read().decode('utf-8'))
                ssh_client.close()
                logging.info(f"连接成功！用户名: {username}, 密码: {password}")
                logging.info(f"在成功之前失败了 {failed_attempts} 次")
                return True
            
            failed_attempts += 1
            attempt_count += 1
            
            if attempt_count % 10 == 0:  # 每10次尝试报告一次
                logging.info(f"已尝试 {attempt_count} 次，失败 {failed_attempts} 次")
            
            time.sleep(5)  # 在每次尝试之间添加5秒延迟
    
    logging.warning(f"所有组合都已尝试，连接失败。总共失败 {failed_attempts} 次")
    return False

def ssh_rsa_connection(hostname):
    """尝试SSH RSA密钥连接"""
    path = input("请输入您的id_rsa文件的绝对路径：")
    flag1 = input("您是否需要指定密码？如需要，请输入y；否则输入n：").lower()

    with open("username.txt", 'r') as f:
        usernames = f.read().splitlines()

    failed_attempts = 0

    if flag1 == 'y':
        with open("password.txt", 'r') as f:
            passwords = f.read().splitlines()
        for password in passwords:
            for username in usernames:
                ssh_client = ssh_connect(hostname, 22, username, key_filename=path, password=password)
                if ssh_client:
                    stdin, stdout, stderr = ssh_client.exec_command('hostname', timeout=10)
                    print(stdout.read().decode())
                    ssh_client.close()
                    logging.info(f"连接成功！用户名: {username}, 密码: {password}")
                    logging.info(f"在成功之前失败了 {failed_attempts} 次")
                    return True
                failed_attempts += 1
    elif flag1 == 'n':
        for username in usernames:
            ssh_client = ssh_connect(hostname, 22, username, key_filename=path)
            if ssh_client:
                stdin, stdout, stderr = ssh_client.exec_command('hostname', timeout=10)
                print(stdout.read().decode())
                ssh_client.close()
                logging.info(f"连接成功！用户名: {username}")
                logging.info(f"在成功之前失败了 {failed_attempts} 次")
                return True
            failed_attempts += 1
    else:
        logging.error("输入无效！")
    
    logging.warning(f"RSA密钥连接失败。总共失败 {failed_attempts} 次")
    return False

def trans_file(hostname):
    """文件传输功能"""
    with open("username.txt", 'r') as f:
        usernames = f.read().splitlines()
    with open("password.txt", 'r') as f:
        passwords = f.read().splitlines()

    flag2 = input("如果您要上传文件，请输入1；如果您要下载文件，请输入2：")
    
    failed_attempts = 0

    for username in usernames:
        for password in passwords:
            try:
                transport = paramiko.Transport((hostname, 22))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)

                if flag2 == '1':
                    local_path = input("请输入您要上传的本地文件的绝对路径：")
                    remote_path = input("请输入您要上传的位置的绝对路径：")
                    sftp.put(localpath=local_path, remotepath=remote_path)
                    logging.info("上传成功！")
                elif flag2 == '2':
                    local_path = input("请输入您要保存的位置的绝对路径：")
                    remote_path = input("请输入您要获取的文件的绝对路径：")
                    sftp.get(remotepath=remote_path, localpath=local_path)
                    logging.info("下载成功！")
                else:
                    logging.error("输入无效！")
                    return False

                transport.close()
                logging.info(f"连接成功！用户名: {username}, 密码: {password}")
                logging.info(f"在成功之前失败了 {failed_attempts} 次")
                return True
            except Exception:
                failed_attempts += 1
    
    logging.warning(f"文件传输失败。总共失败 {failed_attempts} 次")
    return False

def send_msg():
    """发送邮件通知"""
    try:
        smtp_config = {
            'server': get_config("smtp", "server"),
            'port': int(get_config("smtp", "port")),
            'use_tls': get_config("smtp", "use_tls").lower() == 'true',
            'sender': get_config("smtp", "sender"),
            'password': get_config("smtp", "password"),
            'receivers': get_config("smtp", "receivers").split(',')
        }
        
        machine_name = socket.gethostname()

        msg_root = MIMEMultipart('mixed')
        msg_root['From'] = Header(f'{machine_name} <{smtp_config["sender"]}>')
        msg_root['To'] = Header(', '.join(smtp_config['receivers']))
        msg_root['Subject'] = Header(f'来自 {machine_name} 的消息', 'utf-8')
        
        mail_msg = f"""
        <html>
          <body>
          <p>[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]<br>
             来自 {machine_name} 的消息</p>
        <p>路径: {os.getcwd()}<br>
           参数: {' '.join(sys.argv)}</p>
           您的扫描任务已经完成。
        </body>
        </html>"""

        msg_root.attach(MIMEText(mail_msg, 'html', 'utf-8'))

        if smtp_config['use_tls']:
            smtp = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            smtp.starttls()
        else:
            smtp = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
        
        smtp.login(smtp_config['sender'], smtp_config['password'])
        smtp.sendmail(smtp_config['sender'], smtp_config['receivers'], msg_root.as_string())
        smtp.quit()
        logging.info("邮件发送成功")
    except FileNotFoundError:
        logging.warning("未找到配置文件 config.ini，跳过邮件发送")
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")

def main():
    """主函数"""
    print(BANNER)

    if len(sys.argv) != 3:
        print("用法: python script.py <-C|-R|-T> <hostname>")
        sys.exit(1)

    type_arg, hostname = sys.argv[1], sys.argv[2]

    try:
        if type_arg == '-C':
            success = ssh_client_connection(hostname)
        elif type_arg == '-R':
            success = ssh_rsa_connection(hostname)
        elif type_arg == '-T':
            success = trans_file(hostname)
        else:
            logging.error("无效参数。请使用 -C, -R, 或 -T。")
            sys.exit(1)

        if success:
            send_msg()
        else:
            logging.warning("操作失败。请检查您的输入和配置。")
    except Exception as e:
        logging.error(f"发生错误: {e}")
    finally:
        logging.info("操作完成。如果需要发送邮件通知，请确保 config.ini 文件存在并配置正确。")

if __name__ == '__main__':
    check_config_file()
    main()
