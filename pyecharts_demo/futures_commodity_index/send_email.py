import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket

host_name = socket.gethostname()
host = socket.gethostbyname(host_name)  # 获取电脑的ip地址


# QQ发邮件
def send_email(content):
    msg_from = '1522073396@qq.com'  # 发送方邮箱
    passwd = 'zncqycoahpmzibjf'  # 发送方的邮箱授权码
    to = ['877896985@qq.com']  # 接受方邮箱
    msg = MIMEMultipart()
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    msg['Subject'] = f"{host} 脚本任务"  # 邮件的标题
    msg['From'] = msg_from
    s = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 连接邮件服务器
    s.login(msg_from, passwd)  # 账户登录
    s.sendmail(msg_from, to, msg.as_string())  # 发送邮件
