import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import config


def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info(
        'Python ServiceBus queue trigger processed message: %s', notification_id)

    # TODO: Get connection to database
    # url = os.environ["codeninja.postgres.database.azure.com"]
    # database = os.environ["techconfdb"]
    # user = os.environ["codeninja123@codeninja"]
    # passowrd = os.environ["CanTho@123"]

    db_connection = psycopg2.connect(user="codeninja123@codeninja",
                                     password="CanTho@123",
                                     host="codeninja.postgres.database.azure.com",
                                     port="5432",
                                     database="techconfdb")
    # db_connection = psycopg2.connect(url, database, user, passowrd)
    logging.info(f'Connection to to the {db_connection} is successfull')

    try:
        # TODO: Get notification message and subject from database using the notification_id
        cursor = db_connection.cursor()
        cursor.execute(
            f"SELECT message, subject FROM notification WHERE id={str(notification_id)}")
        logging.info(
            f"NotificationID {str(notification_id)}: Get message and subject")

        for row in cursor.fetchall():
            message = row[0]
            subject = row[1]

        if not message:
            error_message = f"ID {str(notification_id)}: Message field empty"
            logging.error(error_message)
            raise Exception(error_message)

        if not subject:
            error_subject = f"ID {str(notification_id)}: Subject field empty"
            logging.error(error_subject)
            raise Exception(error_subject)

        else:
            logging.info(f"ID {str(notification_id)}: {message}, {subject}")

        # TODO: Get attendees email and name

        cursor.execute(f"SELECT first_name, last_name,email FROM attendee")
        count = 0

        # TODO: Loop through each attendee and send an email with a personalized subject
        for row in cursor.fetchall():
            first_name = row[0]
            last_name = row[1]
            email = row[2]

            logging.info(
                f"ID {str(notification_id)}: First Name: {first_name}, Last Name: {last_name}, E-mail: {email}")

            email_from = (os.environ['ADMIN_EMAIL_ADDRESS'])
            email_to = (email)
            subject = f"Hello, {first_name}"
            email_body = message

            mail = Mail(email_from, email_to, subject, email_body)
            send_grid = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
            send_grid.send(mail)

            count += 1

        # TODO: Update the notification table by setting the completed date and updating the status with the total number of attendees notified

        status = f"Notified {str(count)} attendees"
        logging.info(f"ID{str(notification_id)}: {status}@{datetime.now()}")

        command = f"UPDATE notification SET status= '{status}' WHERE id={str(notification_id)}"
        cursor.execute(command)

        command = f"UPDATE notification SET completed_date= '{str(datetime.now())}' WHERE id={str(notification_id)}"
        cursor.execute(command)
        db_connection.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        # TODO: Close connection
        db_connection.close()
