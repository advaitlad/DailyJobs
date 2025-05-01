import requests
from datetime import datetime, timedelta
import json
import os
import time
from typing import List, Dict
from dateutil import parser
from dateutil.tz import tzutc  # Add this import

def is_product_role(title):
    """Check if a job title is a product management role"""
    product_keywords = [
        'product manager',
        'product owner',
        'technical product manager',
        'product management'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in product_keywords)

def is_program_role(title):
    """Check if a job title is a program management role"""
    program_keywords = [
        'program manager',
        'programme manager',
        'technical program manager',
        'program management'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in program_keywords)

def is_data_analyst_role(title):
    """Check if a job title is a data analyst role"""
    data_keywords = [
        'data analyst',
        'analytics analyst',
        'data analytics',
        'Insights Analyst',
        'Product Analyst',
        'Product Insights Analyst'
        'Data Analytics',
        'Product Analytics',
        'Experimentation Analyst'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in data_keywords)

def is_business_analyst_role(title):
    """Check if a job title is a business analyst role"""
    business_keywords = [
        'business analyst'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in business_keywords)

def is_data_scientist_role(title):
    """Check if a job title is a data scientist role"""
    scientist_keywords = [
        'data scientist'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in scientist_keywords)

def is_bi_engineer_role(title):
    """Check if a job title is a BI/Data Visualization Engineer role"""
    bi_keywords = [
        'business intelligence engineer',
        'data visualization engineer',
        'business intelligence analyst',
        'data visualization analyst'
        'tableau developer',
        'power bi developer',
        'data visualization specialist',
        'Tableau Analyst',
        'Power BI Analyst',
        'Tableau Specialist',
        'Power BI Specialist',
        'BI Analyst',
        'BI Engineer',
        'Business Intelligence Analyst',
        'data visualization analyst',
        'Data Reporting Analyst',
        'Business Analytics'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in bi_keywords)

def is_data_engineer_role(title):
    """Check if a job title is a data engineering role"""
    data_eng_keywords = [
        'data engineer',
        'etl engineer'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in data_eng_keywords)

def is_software_engineer_role(title):
    """Check if a job title is a software engineering role"""
    swe_keywords = [
        'software engineer',
        'full stack engineer',
        'backend engineer',
        'frontend engineer',
        'devops engineer',
        'software developer',
        'full stack developer',
        'backend developer',
        'frontend developer',
        'web developer',
        'cloud engineer',
        'systems engineer',
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in swe_keywords)

def is_sre_engineer_role(title):
    """Check if a job title is a software engineering role"""
    sre_keywords = [
        'sre engineer',
        'site reliability engineer',
        'site reliability',
        'sre',
        'site reliability',
        'DevOps Engineer'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in sre_keywords)

def is_ml_engineer_role(title):
    """Check if a job title is a software engineering role"""
    ml_keywords = [
        'machine learning engineer',
        'ml engineer',
        'ml ops',
        'artificial intelligence engineer',
        'ai engineer'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in ml_keywords)

def get_role_type(title):
    """Determine the role type based on the job title"""
    if is_product_role(title):
        return 'product'
    elif is_program_role(title):
        return 'program'
    elif is_data_analyst_role(title):
        return 'data'
    elif is_business_analyst_role(title):
        return 'business'
    elif is_data_scientist_role(title):
        return 'scientist'
    elif is_bi_engineer_role(title):
        return 'bi'
    elif is_data_engineer_role(title):
        return 'dataeng'
    elif is_software_engineer_role(title):
        return 'swe'
    elif is_sre_engineer_role(title):
        return 'sre'
    return None

def parse_greenhouse_date(date_str: str) -> datetime:
    """Parse datetime from Greenhouse API which can be in different formats"""
    try:
        return parser.parse(date_str)
    except (ValueError, TypeError) as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None

def get_experience_level(title):
    """Efficiently determine experience level from job title"""
    if not title:
        return 'unknown'
        
    title_lower = title.lower()
    
    # Define experience level keywords with their variations
    senior_keywords = {
        'senior', 'lead', 'principal', 'staff', 'sr.', 'head', 'chief',
        'director', 'vp', 'vice president', 'senior manager', 'lead manager',
        'principal manager', 'staff manager', 'head manager', 'group'
    }
    
    junior_keywords = {
        'junior', 'entry', 'associate', 'jr.', 'assistant',
        'graduate', 'new grad', 'new graduate', 'entry level',
        'entry-level', 'early career', 'early-career'
    }
    
    intern_keywords = {
        'intern', 'internship', 'co-op', 'coop', 'student', 'apprentice',
        'trainee', 'fellowship', 'fellow'
    }
    
    # Check for senior level first (most specific)
    if any(keyword in title_lower for keyword in senior_keywords):
        return 'senior'
    
    # Check for intern level
    if any(keyword in title_lower for keyword in intern_keywords):
        return 'intern'
    
    # Check for junior level
    if any(keyword in title_lower for keyword in junior_keywords):
        return 'junior'

    # Default to mid-level for ambiguous titles
    return 'mid-level'

def scrape_greenhouse_jobs(company_name: str, board_token: str, experience_levels: List[str] = None) -> List[Dict]:
    """Generic function to scrape jobs from any Greenhouse board

    Args:
        company_name: Name of the company (e.g., 'pinterest', 'stripe')
        board_token: The board token from the company's Greenhouse URL
        experience_levels: List of experience levels to filter by (e.g., ['junior', 'mid-level'])
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    last_24h = datetime.now(tzutc()) - timedelta(hours=24)

    try:
        response = requests.get(url)
        response.raise_for_status()

        jobs_data = response.json()['jobs']
        processed_jobs = []

        for job in jobs_data:
            title = job.get('title', 'N/A')
            
            # Skip if not a product/program role
            role_type = get_role_type(title)
            if not role_type:
                continue
            
            # Get experience level
            experience_level = get_experience_level(title)
            
            # Skip if experience level doesn't match preferences
            if experience_levels and experience_level not in experience_levels:
                continue
            
            # Parse and check update time
            updated_at_str = job.get('updated_at', '')
            updated_at = parse_greenhouse_date(updated_at_str)
            if not updated_at or updated_at <= last_24h:
                continue
                
            try:
                department = job.get('departments', [{}])[0].get('name', 'N/A')
            except (IndexError, KeyError):
                department = 'N/A'

            location = job.get('location', {}).get('name', 'N/A')

            # Format the update time for display
            time_ago = datetime.now(tzutc()) - updated_at
            hours_ago = round(time_ago.total_seconds() / 3600, 1)

            job_info = {
                'company': company_name.title(),
                'title': title,
                'location': location,
                'department': department,
                'job_id': f"{company_name}_{job.get('id', 'N/A')}",
                'hours_ago': hours_ago,
                'url': job.get('absolute_url', 'N/A'),
                'role_type': role_type,
                'updated_at': updated_at,
                'experience_level': experience_level
            }
            processed_jobs.append(job_info)

        return processed_jobs

    except requests.exceptions.RequestException as e:
        print(f"Error fetching jobs for {company_name}: {e}")
        return []
    except (KeyError, ValueError) as e:
        print(f"Error processing jobs for {company_name}: {e}")
        return []

def load_companies() -> Dict[str, str]:
    """Load companies from config file"""
    config_path = os.path.join('docs', 'companies_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)['companies']

def main():
    # Load all companies from config
    all_companies = load_companies()
    total_companies = len(all_companies)
    all_jobs = []

    print(f"Checking {total_companies} companies for jobs posted/updated in the last 24 hours...")

    # Scrape jobs from each company
    for idx, (company_name, board_token) in enumerate(all_companies.items(), 1):
        print(f"\nChecking {company_name.title()} ({idx}/{total_companies})...")
        jobs = scrape_greenhouse_jobs(company_name, board_token)
        if jobs:
            all_jobs.extend(jobs)
            print(f"Found {len(jobs)} new jobs")
            
        # Add delay between requests to avoid rate limiting
        if idx < total_companies:
            time.sleep(1.0)

    if not all_jobs:
        print("\nNo new jobs found in the last 24 hours.")
        return

    # Sort jobs by update time (most recent first)
    all_jobs.sort(key=lambda x: x['hours_ago'])

    # Print all jobs
    print("\nJobs Updated in Last 24 Hours:")
    print("=" * 80)
    for job in all_jobs:
        print(f"\nCompany: {job['company']}")
        print(f"Title: {job['title']}")
        print(f"Location: {job['location']}")
        print(f"Department: {job['department']}")
        print(f"Experience Level: {job['experience_level']}")
        print(f"Updated: {job['updated_at']} ({job['hours_ago']} hours ago)")
        print(f"URL: {job['url']}")
        print("-" * 80)

    # Print summary
    print("\nSummary:")
    print(f"Total new jobs found: {len(all_jobs)}")
    companies_with_jobs = {}
    for job in all_jobs:
        companies_with_jobs[job['company']] = companies_with_jobs.get(job['company'], 0) + 1
    
    for company, count in sorted(companies_with_jobs.items()):
        print(f"{company}: {count} new jobs")

if __name__ == "__main__":
    main() 