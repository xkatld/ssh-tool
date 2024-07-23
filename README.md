# SSH连接工具使用教程

## 1. 准备工作

在使用此工具之前，请确保您的系统满足以下要求：

1. 安装了 Python 3.6 或更高版本。
2. 安装了必要的 Python 库。您可以通过以下命令安装：
   ```
   pip install paramiko cryptography
   ```

## 2. 文件准备

在运行脚本之前，您需要准备以下文件：

1. `username.txt`：包含要尝试的用户名列表，每行一个用户名。
2. `password.txt`：包含要尝试的密码列表，每行一个密码。
3. `config.ini`：（可选）如果您想使用邮件通知功能，需要创建此配置文件。

将这些文件放在与脚本相同的目录下。

### config.ini 示例

如果您想使用邮件通知功能，请修改 `config.ini` 文件，内容如下：

```ini
[smtp]
server = smtp.example.com
port = 587
use_tls = true
sender = your_email@example.com
password = your_email_password
receivers = receiver1@example.com, receiver2@example.com
```

请根据您的实际邮箱设置修改这些值。

## 3. 使用方法

1. 打开终端或命令提示符。
2. 导航到脚本所在的目录。
3. 运行以下命令：

   ```
   python sshtool.py [-C] <hostname>
   ```

   其中，`<hostname>` 是目标主机的 IP 地址或域名。`-C` 参数是可选的。

   例如：
   ```
   python sshtool.py 192.168.1.100
   ```
   或
   ```
   python sshtool.py -C example.com
   ```

## 4. 运行过程

1. 脚本开始运行后，会显示一个 banner，包含版本信息。
2. 然后，它会开始尝试使用 `username.txt` 和 `password.txt` 中的组合连接目标主机。
3. 在尝试过程中，屏幕上会实时显示当前的尝试次数。
4. 如果成功建立连接，脚本会立即显示成功信息，包括正确的用户名和密码，以及尝试次数。
5. 如果配置了邮件通知，脚本会尝试发送一封包含成功信息的邮件。
6. 成功后，程序会自动退出。
