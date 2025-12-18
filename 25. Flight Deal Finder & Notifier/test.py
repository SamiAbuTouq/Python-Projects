from notification_manager import NotificationManager
notification_manager = NotificationManager()




customer_email_list = ["samiabutouq117@gmail.com","samiabutouq666@gmail.com","samiabuobida8@gmail.com"]
message="hi there"


notification_manager.send_whatsapp(message_body=message)
notification_manager.send_telegram(message_body=message)
print('hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii')
# Send emails to everyone on the list
notification_manager.send_emails(email_list=customer_email_list, email_body=message)


