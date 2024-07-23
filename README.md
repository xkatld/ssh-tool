# SSH连接和文件传输工具使用教程

## 1. 准备工作

在使用本工具之前，请确保：

1. 已安装python3 3.6或更高版本。
2. 安装所需的python3库。在命令行中运行：
   ```
   pip install paramiko configparser
   ```
3. 在脚本同目录下准备以下文件：
   - `username.txt`: 包含要尝试的用户名列表，每行一个。
   - `password.txt`: 包含要尝试的密码列表，每行一个。
   - `config.ini`: 配置文件，包含SMTP服务器信息。

## 2. 配置文件设置

创建一个名为`config.ini`的文件，内容如下：

```ini
[smtp]
server = smtp.example.com
port = 587
use_tls = true
sender = your_email@example.com
password = your_password_or_app_password
receivers = receiver1@example.com, receiver2@example.com
```

根据您的邮箱服务提供商，修改相应的设置。

## 3. 使用方法

本工具有三种主要功能：SSH客户端连接、SSH RSA密钥连接和文件传输。

### 3.1 SSH客户端连接

使用用户名和密码尝试SSH连接：

```
python3 script.py -C <hostname>
```

### 3.2 SSH RSA密钥连接

使用RSA密钥尝试SSH连接：

```
python3 script.py -R <hostname>
```

执行后，程序会提示输入RSA私钥文件的路径，以及是否需要密码。

### 3.3 文件传输

进行文件上传或下载：

```
python3 script.py -T <hostname>
```

执行后，程序会提示选择上传或下载，然后输入相应的本地和远程文件路径。
