# mail.py
import os
import base64
import pickle
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_high_severity_entries():
    high_links = []
    try:
        with open("output.txt", "r") as f:
            lines = f.readlines()
            current_entry = []

            for line in lines:
                if line.strip() == "":
                    entry_text = " ".join(current_entry).lower()
                    severity_found = False
                    num_match = re.search(r"severity[:\s]*([0-9]*\.?[0-9]+)", entry_text)
                    if num_match:
                        try:
                            score = float(num_match.group(1))
                            if score >= 7.0:
                                high_links.append("".join(current_entry))
                                severity_found = True
                        except ValueError:
                            pass
                    if not severity_found:
                        if "severity: high" in entry_text or "severity: critical" in entry_text:
                            high_links.append("".join(current_entry))
                    current_entry = []
                else:
                    current_entry.append(line)

            if current_entry:
                entry_text = " ".join(current_entry).lower()
                severity_found = False
                num_match = re.search(r"severity[:\s]*([0-9]*\.?[0-9]+)", entry_text)
                if num_match:
                    try:
                        score = float(num_match.group(1))
                        if score >= 7.0:
                            high_links.append("".join(current_entry))
                            severity_found = True
                    except ValueError:
                        pass
                if not severity_found:
                    if "severity: high" in entry_text or "severity: critical" in entry_text:
                        high_links.append("".join(current_entry))
    except FileNotFoundError:
        pass
    return high_links

def send_email():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    high_severity_entries = get_high_severity_entries()

    if not high_severity_entries:
        print("No high severity entries to send.")
        return

    html_body = """
    <html>
    <body>
        <h2 style="color: red;">🚨 High Severity Vulnerabilities Alert</h2>
        <ul>
    """

    for entry in high_severity_entries:
        html_body += f"<li><pre>{entry}</pre></li>"

    html_body += """
        </ul>
        <p style="color: gray;">— Alert System</p>
    </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['To'] = 'shubha03ka@gmail.com'
    msg['Subject'] = 'ThreatWatch Email Alert'
    msg.attach(MIMEText(html_body, 'html'))

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    message_body = {'raw': raw_message}

    try:
        message = service.users().messages().send(userId='me', body=message_body).execute()
        print(f'✅ Email sent! Message ID: {message["id"]}')
    except Exception as e:
        print(f'❌ Email failed. Error: {str(e)}')
