
import os
import smtplib
from email import encoders  # 파일전송을 할 때 이미지나 문서 동영상 등의 파일을 문자열로 변환할 때 사용할 패키지
from email.mime.text import MIMEText   # 본문내용을 전송할 때 사용되는 모듈
from email.mime.multipart import MIMEMultipart   # 메시지를 보낼 때 메시지에 대한 모듈
from email.mime.base import MIMEBase     # 파일을 전송할 때 사용되는 모듈

# https://hyeshinoh.github.io/2018/09/29/web_06_Send_Email/

class Email:
  def __init__(self):
    self.smtp = None

  def init(self, url, port, id, pw):
    self.smtp = smtplib.SMTP(url, port)
    self.smtp.ehlo()
    self.smtp.starttls()
    self.smtp.login(id, pw)

  def sendMsg(self, fromAddr, toArray, subject, text):
    msg = MIMEMultipart()    #msg obj.
    msg['Subject'] = subject

    part = MIMEText(text)
    msg.attach(part)

    for addr in toArray:
      msg["To"] = addr
      self.smtp.sendmail(fromAddr, addr, msg.as_string())
      
  def sendHtml(self, fromAddr, toArray, subject, html):
    msg = MIMEMultipart()    #msg obj.
    msg['Subject'] = subject

    part = MIMEText(html, 'html')
    msg.attach(part)

    for addr in toArray:
      msg["To"] = addr
      self.smtp.sendmail(fromAddr, addr, msg.as_string())
      
  def clear(self):
    self.smtp.quit()
  

'''
sendmail 쓰는 버젼 이제 쓰지 말자
class SenderSendmail:
	def __init__(self, emailFrom=None, emailTo=None):
		self.emailFrom = emailFrom
		self.emailTo = emailTo

	def sendMsg(self, subject, content, emailTo=None, emailFrom=None):
		if emailTo == None:
			emailTo = self.emailTo
		if emailFrom == None:
			emailFrom = self.emailFrom

		msg = MIMEText(content) # "EasyCollector new user\nphone:%s\nemail:%s" % (phone, email))
		msg["From"] = emailFrom	# "cjng96@inertry.com"
		msg["To"] = emailTo # "bluekara@nate.com, cjng96@gmail.com, felerdin@gmail.com"
		msg["Subject"] = subject # "[EC%s] new user[%s]" % ("test" if g.isTestMode else "", phone)
		p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
		p.communicate(msg.as_string().encode())
'''
