#SMS PyBot ~ txtPyBot
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

carrier = {"att":"@txt.att.net", "sprint":"@messaging.sprintpcs.com",
            "sprint2":"@pm.sprint.com", "tmobile":"@tmomail.net",
            "verizon":"@vtext.com", "boost":"myboostmobile.com",
            "cricket":"@sms.mycricket.com", "metropcs":"@mymetropcs.com",
            "tracfone":"@mmst5.tracfone.com", "uscellular":"@email.uscc.net",
            "virgin":"@vmobl.com"}

#Avihna email
email = "TODO Put email here"
pas = "TODO Put pass here"
smtp = "smtp.gmail.com" #Gmail smtp
port = 587

#Contact Setup
contact = "+19255180463"+carrier["verizon"]

#Setup of email port/login
server = smtplib.SMTP(smtp,port)
server.starttls()
server.login(email,pas)

#Message creation using MIME
msg = MIMEMultipart()
msg['From'] = email
msg['To'] = contact
msg['Subject'] = "txtPyBot Test\n"
body = "This is a test of the txtPyBot subsystem.\n" +
        "This should be on a seperate line"
msg.attach(MIMEText(body, 'plain'))
sms = msg.as_string()

#Sending the message/email
server.sendmail(email,contact,sms)

#Shutting down server connection
server.quit()
