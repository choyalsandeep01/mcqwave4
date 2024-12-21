# import imp
# from django.conf import settings
# from django.core.mail import send_mail
# import smtplib



# def send_account_activation_email(email , email_token):

#     message = f'Hi, click on the link to activate your account http://51.20.4.28/accounts/activate/{email_token}'
    





#     smtp_server = 'smtp.gmail.com'
#     port = 587  # For starttls
#     sender_email = 'travelphoto85@gmail.com'
#     password = 'dtlxsqpoacwhmbzw'
#     receiver_email = email
#     message = message

#     try:
#         server = smtplib.SMTP(smtp_server, port)
#         server.ehlo()  # Can be omitted
#         server.starttls()  # Secure the connection
#         server.ehlo()  # Can be omitted
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message)
#         server.close()
#         print("Email sent successfully")
#         print(message)
#     except Exception as e:
#         print(f"Error: {e}")
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_account_activation_email(email, email_token):
    # Email content
    subject = "Account Activation"
    body = f"""
    Hi,

    Thank you for registering with us. Please click the link below to activate your account:
    
    <a href="http://51.20.4.28/accounts/activate/{email_token}">Activate your account</a>
    
    If you did not sign up for this account, please ignore this email.
    
    Best regards,
    MCQwave
    """

    # Create the email message
    message = MIMEMultipart()
    message['From'] = 'travelphoto85@gmail.com'
    message['To'] = email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))

    smtp_server = 'smtp.gmail.com'
    port = 587  # For starttls
    sender_email = 'travelphoto85@gmail.com'
    password = 'dtlxsqpoacwhmbzw'
    receiver_email = email

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()  # Can be omitted
        server.starttls()  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.close()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error: {e}")
