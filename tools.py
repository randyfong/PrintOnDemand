import os
import time
import imaplib
import email
import re
import yagmail
from crewai.tools import BaseTool
from pydantic import Field
from typing import Optional

class SendEmailTool(BaseTool):
    name: str = "send_email_tool"
    description: str = "Sends an email with an optional attachment. Useful for sending PDFs to Staples for printing."

    def _run(self, recipient: str, subject: str, contents: str, attachment_path: Optional[str] = None) -> str:
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASSWORD")
        
        if not email_user or not email_password:
            return "Error: EMAIL_USER and EMAIL_PASSWORD environment variables are not set."
        
        try:
            yag = yagmail.SMTP(email_user, email_password)
            if attachment_path:
                yag.send(to=recipient, subject=subject, contents=contents, attachments=attachment_path)
            else:
                yag.send(to=recipient, subject=subject, contents=contents)
            return f"Email sent successfully to {recipient} with subject '{subject}'."
        except Exception as e:
            return f"Error sending email: {str(e)}"

class WaitAndExtractReleaseCodeTool(BaseTool):
    name: str = "wait_and_extract_release_code_tool"
    description: str = "Polls the inbox for a confirmation email from Staples (PrintMe) and extracts the 8-digit release code."

    def _run(self, wait_time_seconds: int = 60, poll_interval: int = 10) -> str:
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASSWORD")
        imap_server = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com") # Default to Gmail

        if not email_user or not email_password:
            return "Error: EMAIL_USER and EMAIL_PASSWORD environment variables are not set."

        start_time = time.time()
        while (time.time() - start_time) < wait_time_seconds:
            try:
                mail = imaplib.IMAP4_SSL(imap_server)
                mail.login(email_user, email_password)
                mail.select("inbox")
                
                # Search for emails from Staples/PrintMe
                # Staples typically uses "PrintMe" or "staplesmobile@printme.com"
                status, messages = mail.search(None, '(FROM "PrintMe")')
                
                if status == "OK" and messages[0]:
                    mail_ids = messages[0].split()
                    # Get the most recent email
                    latest_email_id = mail_ids[-1]
                    status, data = mail.fetch(latest_email_id, "(RFC822)")
                    
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode()
                            
                            # Extract 8-digit alphanumeric release code (e.g., E554E9F9)
                            # Common pattern is 8 alphanumeric characters
                            match = re.search(r'\b([A-Z0-9]{8})\b', body)
                            if match:
                                release_code = match.group(1)
                                mail.logout()
                                return f"Release Code extracted: {release_code}"
                
                mail.logout()
            except Exception as e:
                print(f"Polling error: {str(e)}")
            
            time.sleep(poll_interval)
            
        return "Timeout: Could not find the release code in the inbox within the specified time."
