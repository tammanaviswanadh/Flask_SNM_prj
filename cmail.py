import smtplib
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('tammanaviswanadh.office@gmail.com','cehg kimn julj rsrg')
    msg=EmailMessage()
    msg['FROM']='tammanaviswanadh.office@gmail.com'
    msg['SUBJECT']=subject  
    msg['TO']=to
    msg.set_content(body)
    server.send_message(msg)
    server.close()