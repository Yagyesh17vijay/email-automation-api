
from flask import Blueprint, jsonify, request
from database import get_db_connection

history_bp = Blueprint("history", __name__)


@history_bp.route("/email-history", methods=["GET"])
def get_email_history():
    connection = None
    cursor = None

    try:
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=10, type=int)

        status = request.args.get("status", "").strip().upper()
        recipient = request.args.get("recipient", "").strip()

        if page < 1 or per_page < 1:
            return jsonify({
                "error": "page and per_page must be positive integers"
            }), 400

        if per_page > 100:
            return jsonify({
                "error": "per_page cannot exceed 100"
            }), 400

        if status and status not in {"SENT", "FAILED"}:
            return jsonify({
                "error": "status must be either SENT or FAILED"
            }), 400

        # Build filters safely using parameterized queries
        conditions = []
        values = []

        if status:
            conditions.append("status = %s")
            values.append(status)

        if recipient:
            conditions.append("recipient LIKE %s")
            values.append(f"%{recipient}%")

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        offset = (page - 1) * per_page

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Count records matching the filters
        count_query = (
            "SELECT COUNT(*) AS total FROM email_activity"
            + where_clause
        )
        cursor.execute(count_query, tuple(values))
        total_records = cursor.fetchone()["total"]

        # Retrieve the requested page
        history_query = """
            SELECT
                email_id,
                recipient,
                subject,
                status,
                timestamp,
                error_message
            FROM email_activity
        """ + where_clause + """
            ORDER BY timestamp DESC, email_id DESC
            LIMIT %s OFFSET %s
        """

        cursor.execute(
            history_query,
            tuple(values) + (per_page, offset)
        )
        records = cursor.fetchall()

        return jsonify({
            "page": page,
            "per_page": per_page,
            "total_records": total_records,
            "total_pages": (total_records + per_page - 1) // per_page,
            "filters": {
                "status": status or None,
                "recipient": recipient or None
            },
            "email_history": records
        }), 200

    except Exception:
        return jsonify({
            "error": "Unable to retrieve email history"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


@history_bp.route("/email-stats", methods=["GET"])
def get_email_stats():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                COUNT(*) AS total_emails,
                SUM(CASE WHEN status = 'SENT' THEN 1 ELSE 0 END)
                    AS successful_emails,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END)
                    AS failed_emails
            FROM email_activity
        """

        cursor.execute(query)
        stats = cursor.fetchone()

        total = stats["total_emails"]
        successful = stats["successful_emails"]
        failed = stats["failed_emails"]

        success_rate = (
            round((successful / total) * 100, 2)
            if total > 0 else 0
        )

        return jsonify({
            "total_emails": total,
            "successful_emails": successful,
            "failed_emails": failed,
            "success_rate_percent": success_rate
        }), 200

    except Exception:
        return jsonify({
            "error": "Unable to retrieve email statistics"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

