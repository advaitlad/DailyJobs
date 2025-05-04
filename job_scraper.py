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
from greenhouse_scraper import scrape_greenhouse_jobs, load_companies
from dateutil import parser

# Load environment variables
load_dotenv()

# Initialize Firebase with JSON directly
cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
if cred_json:
    cred = credentials.Certificate(json.loads(cred_json))
else:
    FIREBASE_CREDS_PATH = 'config/firebase-adminsdk-fbsvc-ac74291157.json'
    cred = credentials.Certificate(FIREBASE_CREDS_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load companies from config
COMPANIES = load_companies()
GREENHOUSE_COMPANIES = list(COMPANIES.keys())

def scrape_jobs():
    new_jobs = []
    total_jobs_found = 0
    
    # Get all users and their preferences
    users = db.collection('users').get()
    user_preferences = {}
    for user in users:
        user_data = user.to_dict()
        # Only include verified users with non-empty preferences and email
        preferences = user_data.get('preferences', [])
        job_types = user_data.get('jobTypes', [])  # Default to empty array if not specified
        if (user_data.get('emailVerified', False) and preferences and user_data.get('email')):
            user_preferences[user_data['email']] = {
                'companies': preferences,
                'jobTypes': job_types,
                'experienceLevels': user_data.get('experienceLevels', []),  # Get experience level preferences
                'locationPreferences': user_data.get('locationPreferences', [])  # Get location preferences
            }
    
    # Scrape Greenhouse jobs
    print("\nScraping Greenhouse jobs...")
    all_new_jobs = []
    for company_name, board_token in COMPANIES.items():
        print(f"Scraping jobs from {company_name}...")
        company_jobs = scrape_greenhouse_jobs(company_name, board_token)
        total_jobs_found += len(company_jobs)
        
        for job in company_jobs:
            # Create the job document with timestamp
            job_doc = {
                **job,  # Include all existing job fields
                'last_updated': job['updated_at'],  # Use the datetime object directly
                'added_to_db': firestore.SERVER_TIMESTAMP  # When we added it to the database
            }
            
            # Remove the temporary updated_at field since we now have last_updated
            job_doc.pop('updated_at', None)
            
            # Check if job already exists in database using job_id
            job_ref = db.collection('jobs').where('job_id', '==', job['job_id']).get()
            
            if not job_ref:
                # Add to database
                db.collection('jobs').add(job_doc)
                all_new_jobs.append(job)
                print(f"Added new job: {job['title']} at {job['company']} (ID: {job['job_id']}) {job['experience_level']}- Last Updated {job['hours_ago']} hours ago")
    
    # Send personalized emails to each verified user based on their preferences
    verified_users = len(user_preferences)
    print(f"\nFound {verified_users} verified users with preferences")
    
    for email, prefs in user_preferences.items():
        # Get the user's name (first word only)
        user_name = None
        user_doc = db.collection('users').where('email', '==', email).get()
        if user_doc:
            user_data = user_doc[0].to_dict()
            name = user_data.get('name', '').strip()
            if name:
                user_name = name.split()[0]
        if not user_name:
            user_name = 'there'
        # Filter jobs based on user preferences (company, job type, and experience level)
        user_jobs = filter_jobs_for_user(all_new_jobs, prefs)
        # Always send email notification, even if no new jobs
        send_email_notification(user_jobs, email, user_name)
        if user_jobs:
            print(f"Sent notification to {email} with {len(user_jobs)} matching jobs")
        else:
            print(f"Sent 'no new jobs' notification to {email}")
    
    if all_new_jobs:
        print(f"\nFound {len(all_new_jobs)} new jobs in total!")
    else:
        print("\nNo new jobs found.")

def filter_jobs_for_user(jobs, user_preferences):
    """Filter jobs based on user preferences."""
    filtered_jobs = []
    
    for job in jobs:
        # Check company preference
        if user_preferences.get('companies') and job['company'].lower() not in user_preferences['companies']:
            continue
            
        # Check job type preference
        if user_preferences.get('jobTypes') and job['role_type'] not in user_preferences['jobTypes']:
            continue
            
        # Check experience level preference
        if user_preferences.get('experienceLevels') and job['experience_level'] not in user_preferences['experienceLevels']:
            continue
            
        # Check location preference
        if user_preferences.get('locationPreferences'):
            # If "Any Location" is selected, skip location filtering
            if 'any' in user_preferences['locationPreferences']:
                filtered_jobs.append(job)
                continue
                
            job_countries = job.get('countries', [])
            user_locations = user_preferences['locationPreferences']
            
            # If job has no countries or none match user preferences, skip
            if not job_countries or not any(country in user_locations for country in job_countries):
                continue
        
        filtered_jobs.append(job)
    
    return filtered_jobs

def create_html_table(jobs, user_name=None):
    """Create an HTML table for the jobs with a friendly intro message"""
    intro = f"""
    <div style='margin-bottom:1.5rem;'>
        <p style='font-size:1.1rem; color:#222;'>
            Hello {user_name or 'there'},<br><br>
            We're always on the lookout for the freshest roles, so you don't have to be.<br>
            Here are roles that PingMeJobs found in the last 6 hours that match your preferences.<br>
            <b>Check them out and apply early to get ahead of the crowd!</b>
        </p>
    </div>
    """
    html = f"""
    <html>
    <head>
    <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }}
        th {{
            background-color: #2E7D32;
            color: white;
            text-align: left;
            padding: 16px;
            font-size: 14px;
            font-weight: 600;
        }}
        td {{
            padding: 16px;
            border-bottom: 1px solid #E0E0E0;
            font-size: 14px;
            line-height: 1.4;
        }}
        .company-header {{
            background-color: #F5F5F5;
            font-weight: 600;
            padding: 16px;
            font-size: 16px;
            color: #1A1A1A;
        }}
        .apply-button {{
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
        }}
        .apply-button:visited {{
            color: white !important;
        }}
        .apply-button:hover {{
            background-color: #1B5E20;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-1px);
        }}
        tr:hover {{
            background-color: #F9F9F9;
        }}
    </style>
    </head>
    <body>
    {intro}
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

def send_email_notification(jobs, recipient_email, user_name=None):
    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASSWORD')
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = recipient_email
    if jobs:
        msg['Subject'] = f"PingMeJobs Found {len(jobs)} positions"
        # Create both plain text and HTML versions
        text_content = (
            f"Hi {user_name},\n\n"
            f"We're always on the lookout for the freshest roles, so you don't have to be.\n"
            f"Here are roles that PingMeJobs found in the last 6 hours that match your preferences.\n"
            f"Check them out and apply early to get ahead of the crowd!\n\n"
        )
        for job in jobs:
            text_content += f"Company: {job['company']}\n"
            text_content += f"Position: {job['title']}\n"
            text_content += f"Location: {job['location']}\n"
            text_content += f"Apply: {job['url']}\n"
            text_content += "-" * 50 + "\n\n"
        html_content = create_html_table(jobs, user_name)
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
    else:
        msg['Subject'] = "Jobs Update - No New Positions"
        body = "No new positions were updated in the last 6 hours that match your preferences. We'll keep looking 👀\n\n"
        body += "Keep checking back for new opportunities!"
        msg.attach(MIMEText(body, 'plain'))
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