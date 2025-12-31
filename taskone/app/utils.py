import smtplib
from email.message import EmailMessage
from twilio.rest import Client

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")




from app.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_EMAIL,
    SMTP_PASSWORD,
    TWILIO_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE
)

# ================= EMAIL OTP =================
def send_email_otp(to_email: str, otp: str):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your OTP Code"
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg.set_content(f"Your Email OTP is: {otp}")

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email OTP Error:", e)


# ================= SMS OTP =================
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def send_sms_otp(to_phone: str, otp: str):
    try:
        client.messages.create(
            body=f"Your OTP is: {otp}",
            from_=TWILIO_PHONE,
            to=to_phone
        )
    except Exception as e:
        print("SMS OTP Error:", e)