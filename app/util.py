from itsdangerous import URLSafeTimedSerializer
from app import app

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])


def send_email(address, body):
    # TODO: make send_email send emails
    print(body)
