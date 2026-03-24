import sqlite3
import time

from app.settings import anomaly, config


class AnomalyDetector:
    def check(self, uid, username, balance):
        if not anomaly.enable:
            return "safe", None

        conn = sqlite3.connect(config.DATABASE)
        cursor = conn.cursor()

        cursor.execute("SELECT counter, warnings FROM keys WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return "safe", None

        stored_counter, warnings = row
        now = int(time.time())

        if warnings >= anomaly.max_warnings:
            conn.close()
            return "ban", "user_banned"

        if balance != stored_counter:
            reason = f"value_mismatch:{balance}vs{stored_counter}"
            new_warnings = warnings + 1
            cursor.execute(
                "UPDATE keys SET counter = ?, warnings = ? WHERE uid = ?",
                (balance, new_warnings, uid),
            )
            cursor.execute(
                "INSERT INTO anomalies (uid, timestamp, reason, resolved) VALUES (?, ?, ?, 0)",
                (uid, now, reason),
            )
            conn.commit()
            conn.close()
            if new_warnings >= anomaly.max_warnings:
                return "ban", reason
            return "warn", reason

        if anomaly.single_reader and anomaly.interval > 0:
            cursor.execute(
                "SELECT timestamp FROM events WHERE uid = ? AND event_type IN ('success', 'suspicious', 'warning') ORDER BY timestamp DESC LIMIT 1",
                (uid,),
            )
            last = cursor.fetchone()
            if last and (now - last[0]) < anomaly.interval:
                reason = f"rapid_access:{now - last[0]}s"
                cursor.execute(
                    "INSERT INTO anomalies (uid, timestamp, reason, resolved) VALUES (?, ?, ?, 0)",
                    (uid, now, reason),
                )
                conn.commit()
                conn.close()
                return "suspicious", reason

        conn.close()
        return "safe", None


detector = AnomalyDetector()
