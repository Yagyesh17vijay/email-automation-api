
from database import get_db_connection


def save_email_activity(
    recipient,
    subject,
    message,
    status,
    error_message=None
):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO email_activity
            (recipient, subject, message, status, error_message)
            VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            recipient,
            subject,
            message,
            status,
            error_message
        )

        cursor.execute(query, values)
        connection.commit()

        return True

    except Exception:
        if connection and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
