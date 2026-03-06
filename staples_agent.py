import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from tools import SendEmailTool, WaitAndExtractReleaseCodeTool

# Load environment variables from .env
load_dotenv()

def setup_logging():
    """Configure logging for CrewAI agents to console + rotating log file."""
    log_format = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(name)s — %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Root logger — catches everything
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Console handler (INFO and above)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(log_format)

    # Rotating file handler — keeps last 3 × 5 MB logs
    file_handler = RotatingFileHandler(
        'crew.log', maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)

    root.addHandler(console)
    root.addHandler(file_handler)

    # Enable verbose logging from CrewAI's own logger
    for name in ('crewai', 'langchain', 'openai', 'httpx'):
        logging.getLogger(name).setLevel(logging.DEBUG)

    logging.info('CrewAI logging initialised — writing to crew.log')

setup_logging()

# Define the Specialist
print_specialist = Agent(
    role="Staples Print Automation Coordinator",
    goal="1. Receive a PDF and the user's destination email. 2. Forward the PDF to staplesmobile@printme.com. 3. Monitor for the automated response from Staples. 4. Extract the 8-digit Release Code and email it directly to the user.",
    backstory=(
        "You are a highly efficient administrative assistant specializing in document logistics. "
        "Your sole focus is bridging the gap between a user's digital files and physical printing services. "
        "You are an expert at handling sensitive PDF documents, communicating with automated print servers (PrintMe), "
        "and monitoring incoming communications to ensure users receive their pick-up codes without delay. "
        "You understand that timing is critical and accuracy in reporting the Release Code is your top priority. "
        "IMPORTANT: Delete the local copy of the PDF once the transmission is confirmed to maintain data security."
    ),
    tools=[SendEmailTool(), WaitAndExtractReleaseCodeTool()],
    verbose=True,
    allow_delegation=False,
    llm="gpt-4o-mini"
)

# Define the Task
def create_print_task(pdf_path, user_email):
    return Task(
        description=(
            f"1. Initial Submission: Take the provided PDF file at '{pdf_path}' and compose a new email to staplesmobile@printme.com. Ensure the PDF is attached correctly.\n"
            f"2. Confirmation Monitoring: Wait for the confirmation email from the PrintMe service.\n"
            f"3. Data Extraction: Once the email arrives, parse the body of the message to find the unique Release Code (typically an 8-character alphanumeric string).\n"
            f"4. User Notification: Compose a final email to '{user_email}'.\n"
            "   Subject: Your Staples Print Release Code\n"
            "   Body: \"Your document is ready for printing at any Staples self-service kiosk. Please use the following Release Code: [Release Code].\"\n"
            f"5. Privacy: Delete the local copy of the PDF at '{pdf_path}' once the transmission is confirmed."
        ),
        expected_output="A confirmation log showing the timestamp the PDF was sent to Staples and a copy of the final notification email sent to the user containing the specific Release Code.",
        agent=print_specialist
    )

def run_print_flow(pdf_path, user_email):
    logger = logging.getLogger(__name__)
    logger.info(f'Starting print flow — pdf={pdf_path} email={user_email}')
    task = create_print_task(pdf_path, user_email)
    crew = Crew(
        agents=[print_specialist],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    result = crew.kickoff()
    logger.info(f'Print flow complete — result: {str(result)[:200]}')
    return result

if __name__ == "__main__":
    # Example usage (requires environment variables to be set)
    # os.environ["EMAIL_USER"] = "your_email@gmail.com"
    # os.environ["EMAIL_PASSWORD"] = "your_app_password"
    # os.environ["EMAIL_SMTP_SERVER"] = "smtp.gmail.com"
    # os.environ["EMAIL_IMAP_SERVER"] = "imap.gmail.com"
    
    print("Staples Print Automation Agent is ready.")
    print("Please ensure EMAIL_USER, EMAIL_PASSWORD, and EMAIL_IMAP_SERVER are set.")
