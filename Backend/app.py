from pathlib import Path
from datetime import datetime, timezone
import os
import sqlite3

import firebase_admin
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

from flames import RELATIONSHIPS, calculate_flames


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "Frontend"
load_dotenv(PROJECT_ROOT / ".env")

database_path = Path(
    os.getenv("FLAMES_DB_PATH", str(PROJECT_ROOT / "Backend" / "flames.db"))
)
if not database_path.is_absolute():
    database_path = PROJECT_ROOT / database_path

firebase_project_id = (
    os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or ""
).strip()
firebase_credentials_path = Path(
    os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "Backend/firebase-service-account.json")
)
if not firebase_credentials_path.is_absolute():
    firebase_credentials_path = PROJECT_ROOT / firebase_credentials_path

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")


def store_calculation(name1: str, name2: str, code: str, relationship: str) -> tuple[int, str]:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name1 TEXT NOT NULL,
                    name2 TEXT NOT NULL,
                    result_code TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor = connection.execute(
                """
                INSERT INTO calculations
                    (name1, name2, result_code, relationship, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name1, name2, code, relationship, created_at),
            )
            record_id = cursor.lastrowid
            if record_id is None:
                raise sqlite3.DatabaseError("The calculation record was not created.")
    finally:
        connection.close()

    return record_id, created_at


def sync_to_firestore(
    record_id: int,
    name1: str,
    name2: str,
    code: str,
    relationship: str,
    created_at: str,
) -> bool:
    if not firebase_project_id:
        return False

    try:
        try:
            firebase_app = firebase_admin.get_app()
        except ValueError:
            firebase_credential = (
                credentials.Certificate(str(firebase_credentials_path))
                if firebase_credentials_path.is_file()
                else credentials.ApplicationDefault()
            )
            firebase_app = firebase_admin.initialize_app(
                firebase_credential,
                {"projectId": firebase_project_id},
            )

        firestore.client(firebase_app).collection("calculations").document(
            str(record_id)
        ).set(
            {
                "name1": name1,
                "name2": name2,
                "resultCode": code,
                "relationship": relationship,
                "createdAt": created_at,
                "localRecordId": record_id,
            }
        )
        return True
    except Exception:
        app.logger.exception("Could not sync calculation %s to Firestore", record_id)
        return False


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "flames.html")


@app.post("/api/calculate")
def calculate():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Send the names as a JSON object."), 400

    name1 = payload.get("name1")
    name2 = payload.get("name2")
    if not isinstance(name1, str) or not isinstance(name2, str):
        return jsonify(error="Both names must be text."), 400

    name1 = name1.strip()
    name2 = name2.strip()
    if not name1 or not name2:
        return jsonify(error="Enter both names to calculate a result."), 400
    if len(name1) > 80 or len(name2) > 80:
        return jsonify(error="Names must be 80 characters or fewer."), 400
    if not any(char.isalpha() for char in name1) or not any(
        char.isalpha() for char in name2
    ):
        return jsonify(error="Each name must contain at least one letter."), 400

    code = calculate_flames(name1, name2)
    relationship, explanation = RELATIONSHIPS[code]
    try:
        record_id, created_at = store_calculation(name1, name2, code, relationship)
    except sqlite3.Error:
        app.logger.exception("Could not save FLAMES calculation locally")
        return jsonify(error="The result could not be saved. Please try again."), 500

    firebase_synced = sync_to_firestore(
        record_id, name1, name2, code, relationship, created_at
    )
    firebase_configured = bool(firebase_project_id)
    return jsonify(
        name1=name1,
        name2=name2,
        code=code,
        relationship=relationship,
        explanation=explanation,
        record_id=record_id,
        firebase_configured=firebase_configured,
        firebase_synced=firebase_synced,
    )


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, debug=False)