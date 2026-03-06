import os
import time
import imaplib
import email
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from crewai.tools import BaseTool
from typing import Optional

class SendEmailTool(BaseTool):
    name: str = "send_email_tool"
    description: str = "Sends an email with an optional attachment. Useful for sending PDFs to Staples for printing."

    def _run(self, recipient: str, subject: str, contents: str, attachment_path: Optional[str] = None) -> str:
        # MOCKED: Pretend to send the email immediately
        time.sleep(1)  # Simulate short network delay
        
        attached = attachment_path and os.path.exists(attachment_path)
        return (
            f"Email sent successfully to {recipient} (MOCKED). "
            f"PDF attachment {'included' if attached else 'NOT included (file not found)'}."
        )

class WaitAndExtractReleaseCodeTool(BaseTool):
    name: str = "wait_and_extract_release_code_tool"
    description: str = "Polls the inbox for a confirmation email from Staples (PrintMe) and extracts the 8-digit release code."

    def _run(self, wait_time_seconds: int = 60, poll_interval: int = 10) -> str:
        import random
        import string
        
        # MOCKED: Pretend to wait for the email
        time.sleep(2)  # Simulate short polling delay
        
        # Generate random 8 character alphanumeric code
        release_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"Release Code extracted: {release_code}"
