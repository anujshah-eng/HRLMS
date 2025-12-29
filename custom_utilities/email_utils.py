import os
from sib_api_v3_sdk.rest import ApiException
import sib_api_v3_sdk
from custom_utilities.custom_exception import CustomException

class EmailUtility:
    @staticmethod
    def send_email(email: str, subject: str, html_content: str):
        """
        Send a general-purpose email using the Sendinblue (Brevo) API.

        Args:
            email (str): The recipient's email address.
            subject (str): The subject of the email.
            html_content (str): The content of the email.

        Returns:
            dict: Status of the email sending process.
        """
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("SENDER_EMAIL")

        if not configuration.api_key["api-key"]:
            raise CustomException("API key is not set. Please check the environment variable.", status_code=403)

        if not sender_email:
            raise CustomException("Sender email is not set. Please check the environment variable.", status_code=403)

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email}],
            sender={"email": sender_email},
            subject=subject,
            html_content=html_content,
        )

        try:
            api_instance.send_transac_email(send_smtp_email)
            return {"status": "success", "message": "Email sent", "email": email}
        except ApiException as e:
            raise CustomException("Email sending failed", status_code=500)
          
    @staticmethod
    def send_otp_email(email, subject, html_content):
        """
        Send OTP via email using the Sendinblue (Brevo) API.

        Args:
            email (str): The recipient's email address.
            subject (str): The subject of the email.
            html_content (str): The content of the email.

        Returns:
            dict: A dictionary containing the status and message of the email sending process.
        """
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("SENDER_EMAIL")
        if not configuration.api_key["api-key"]:
            raise CustomException("API key is not set. Please check the environment variable.",
                                  status_code=403)
        if not sender_email:
            raise CustomException("Sender email is not set. Please check the environment variable.",
                                  status_code=403)
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email}],
            sender={"email": sender_email},
            subject=subject,
            html_content=html_content,
        )
        try:
            api_instance.send_transac_email(send_smtp_email)
            return {"status": "success", "message": "OTP sent via email", "email": email}
        except ApiException as e:
            raise e
