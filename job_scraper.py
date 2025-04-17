import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from greenhouse_scraper import scrape_greenhouse_jobs, COMPANIES

# Load environment variables
load_dotenv()

# Initialize Firebase
cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_user_preferences():
    """Fetch all users and their company preferences from Firestore"""
    users = []
    users_ref = db.collection('users').stream()
    for user in users_ref:
        user_data = user.to_dict()
        users.append({
            'id': user.id,
            'name': user_data.get('name'),
            'email': user_data.get('email'),
            'companies': user_data.get('companies', [])
        })
    return users

def scrape_jobs():
    """Scrape jobs and send personalized emails to users"""
    # Get all users and their preferences
    users = get_user_preferences()
    if not users:
        print("No users found in database")
        return
    
    # Scrape jobs for all companies
    all_jobs = {}
    for company_name, board_token in COMPANIES.items():
        print(f"Scraping jobs from {company_name}...")
        company_jobs = scrape_greenhouse_jobs(company_name, board_token)
        all_jobs[company_name] = company_jobs
    
    # For each user, find new jobs from their selected companies
    for user in users:
        user_new_jobs = []
        for company in user['companies']:
            if company in all_jobs:
                company_jobs = all_jobs[company]
                for job in company_jobs:
                    # Check if job already exists in database
                    job_ref = db.collection('jobs').where('job_id', '==', job['job_id']).get()
                    if not job_ref:
                        # Add to database
                        db.collection('jobs').add(job)
                        user_new_jobs.append(job)
        
        # Send email to user if there are new jobs
        if user_new_jobs:
            send_email_notification(user['email'], user['name'], user_new_jobs)
            print(f"Sent email to {user['email']} with {len(user_new_jobs)} new jobs")
        else:
            print(f"No new jobs found for {user['email']}")

def create_html_table(jobs):
    """Create an HTML table for the jobs"""
    html = """
    <html>
    <head>
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        th {
            background-color: #2E7D32;
            color: white;
            text-align: left;
            padding: 16px;
            font-size: 14px;
            font-weight: 600;
        }
        td {
            padding: 16px;
            border-bottom: 1px solid #E0E0E0;
            font-size: 14px;
            line-height: 1.4;
        }
        .company-header {
            background-color: #F5F5F5;
            font-weight: 600;
            padding: 16px;
            font-size: 16px;
            color: #1A1A1A;
        }
        .apply-button {
            background-color: #43b548;
            color: white !important;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 6px;
            display: inline-block;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 100px;
        }
        .apply-button:visited {
            color: white !important;
        }
        .apply-button:hover {
            background-color: #1B5E20;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-1px);
        }
        tr:hover {
            background-color: #F9F9F9;
        }
    </style>
    </head>
    <body>
    <table>
        <tr>
            <th>Title</th>
            <th>Location</th>
            <th>Job Link</th>
        </tr>
    """
    
    # Group jobs by company
    companies = {}
    for job in jobs:
        if job['company'] not in companies:
            companies[job['company']] = []
        companies[job['company']].append(job)
    
    # Add jobs to table, grouped by company
    for company in sorted(companies.keys()):
        html += f"""
        <tr>
            <td colspan="3" class="company-header">{company}</td>
        </tr>
        """
        for job in companies[company]:
            html += f"""
            <tr>
                <td>{job['title']}</td>
                <td>{job['location']}</td>
                <td><a href="{job['url']}" class="apply-button">Apply Now</a></td>
            </tr>
            """
    
    html += """
    </table>
    </body>
    </html>
    """
    return html

def send_email_notification(recipient_email, recipient_name, jobs):
    """Send email notification to a specific user"""
    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASSWORD')
    
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    msg['Subject'] = f"New Product Manager Openings Found ({len(jobs)} positions)"
    
    # Create both plain text and HTML versions
    text_content = f"Hi {recipient_name},\n\n"
    text_content += "New Product Manager positions found:\n\n"
    for job in jobs:
        text_content += f"Company: {job['company']}\n"
        text_content += f"Position: {job['title']}\n"
        text_content += f"Location: {job['location']}\n"
        text_content += f"Apply: {job['url']}\n"
        text_content += "-" * 50 + "\n\n"
    
    # Create HTML version
    html_content = f"""
    <html>
    <body>
    <p>Hi {recipient_name},</p>
    <p>We found {len(jobs)} new Product Manager positions that match your preferences:</p>
    {create_html_table(jobs)}
    <p>Best regards,<br>Job Updates Team</p>
    </body>
    </html>
    """
    
    # Attach both versions
    msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Email notification sent successfully to {recipient_email}!")
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {str(e)}")

if __name__ == "__main__":
    print("Starting job scraper...")
    scrape_jobs()
    print("Job scraping completed!") 