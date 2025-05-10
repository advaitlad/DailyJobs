import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from dateutil import parser
import time
import re
import json
import os
from analyze_locations import identify_country

def load_ashby_companies() -> Dict[str, str]:
    """Load Ashby companies from config file"""
    config_path = os.path.join('docs', 'ashby_companies_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)['companies']

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

def is_ml_engineer_role(title):
    """Check if a job title is a machine learning engineering role"""
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

def is_ux_researcher_role(title):
    """Check if a job title is a UX Researcher role"""
    ux_researcher_keywords = [
        'ux researcher',
        'ui researcher',
        'user researcher',
        'user experience researcher',
        'user interface researcher',
        'uxr',
        'ux research',
        'ui research',
        'user research',
        'product research',
        'product researcher'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in ux_researcher_keywords)

def is_ui_designer_role(title):
    """Check if a job title is a UI Designer role"""
    ui_designer_keywords = [
        'User Interface Designer',
        'UI Designer',
        'Product Designer',
        'Frontend Designer',
        'UX Designer',
        'Interaction Designer',
        'UI/UX Designer',
        'UX/ UI Designer',
        'Web Designer',
        'UI/UX Developer'
        'UX/UI Developer'
        'UI Developer',
        'UX Developer'
    ]
    
    if not title:
        return False
        
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in ui_designer_keywords)

def get_role_type(title):
    """Determine the role type based on the job title"""
    if is_product_role(title):
        return 'product'
    elif is_program_role(title):
        return 'program'
    elif is_data_analyst_role(title):
        return 'data'
    elif is_software_engineer_role(title):
        return 'swe'
    elif is_ml_engineer_role(title):
        return 'ml'
    elif is_ux_researcher_role(title):
        return 'uxresearcher'
    elif is_ui_designer_role(title):
        return 'uidesigner'
    return None

def get_experience_level(title: str) -> str:
    """Extract experience level from job title"""
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

def scrape_ashby_jobs(company_name: str, board_token: str, experience_levels: Optional[List[str]] = None) -> List[Dict]:
    """Generic function to scrape jobs from any Ashby board

    Args:
        company_name: Name of the company (e.g., 'notion', 'openai')
        board_token: The board token from the company's Ashby URL
        experience_levels: List of experience levels to filter by (e.g., ['junior', 'mid-level'])
    """
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board_token}?includeCompensation=true"
    current_time = datetime.now(timezone.utc)
    last_6h = current_time - timedelta(hours=6)  # Calculate timestamp from 6 hours ago

    try:
        response = requests.get(url)
        response.raise_for_status()
        #print(f"Response status code: {response.status_code}")
        #print(f"Response keys: {response.json().keys()}")

        job_postings = response.json().get('jobs', [])
        #print(f"Found {len(job_postings)} job postings")

        processed_jobs = []

        for job in job_postings:
            # Extract basic job details
            title = job.get('title', '')
            
            # Get role type and skip if not matching our categories
            role_type = get_role_type(title)
            if not role_type:
                continue
            
            # Get experience level
            experience_level = get_experience_level(title)
            
            # Skip if experience level doesn't match preferences
            if experience_levels and experience_level not in experience_levels:
                continue
            
            # Parse and check published time
            published_date = parser.parse(job.get('publishedAt', ''))
            if not published_date or published_date <= last_6h:  # Skip jobs older than 6 hours
                continue
            
            department = job.get('department', '')
            location = job.get('location', 'Remote')
            
            # Calculate hours ago
            hours_ago = int((current_time - published_date).total_seconds() / 3600)

            # Get job URL
            job_url = job.get('jobUrl', '')

            # Analyze location for countries
            countries = set()
            if ';' in location:
                locations = [loc.strip() for loc in location.split(';')]
                for loc in locations:
                    if 'remote' in loc.lower():
                        countries.add('Remote')
                        loc = re.sub(r'remote,?\s*', '', loc, flags=re.IGNORECASE).strip()
                        if loc:
                            country = identify_country(loc)
                            if country != 'Unknown':
                                countries.add(country)
                    else:
                        country = identify_country(loc)
                        if country != 'Unknown':
                            countries.add(country)
            else:
                if 'remote' in location.lower():
                    countries.add('Remote')
                    loc = re.sub(r'remote,?\s*', '', location, flags=re.IGNORECASE).strip()
                    if loc:
                        country = identify_country(loc)
                        if country != 'Unknown':
                            countries.add(country)
                else:
                    country = identify_country(location)
                    if country != 'Unknown':
                        countries.add(country)

            # Convert countries set to a map with numeric indices
            countries_map = {str(i): country for i, country in enumerate(sorted(countries))}

            # Create job entry
            job_entry = {
                'company': company_name.title(),
                'title': title,
                'location': location,
                'countries': countries_map,
                'department': department,
                'job_id': f"{company_name}_{job.get('id', 'N/A')}",
                'hours_ago': hours_ago,
                'url': job_url,
                'role_type': role_type,
                'published_at': published_date,
                'experience_level': experience_level
            }

            processed_jobs.append(job_entry)

        return processed_jobs

    except requests.exceptions.RequestException as e:
        print(f"Error fetching jobs: {str(e)}")
        return []
    except Exception as e:
        print(f"Error processing jobs data: {str(e)}")
        return []

def scrape_all_ashby_jobs(experience_levels: Optional[List[str]] = None) -> List[Dict]:
    """Scrape jobs from all Ashby companies in the config file

    Args:
        experience_levels: List of experience levels to filter by (e.g., ['junior', 'mid-level'])
    """
    companies = load_ashby_companies()
    all_jobs = []
    
    for company_name, board_token in companies.items():
        print(f"\nScraping jobs from {company_name.title()}...")
        jobs = scrape_ashby_jobs(company_name, board_token, experience_levels)
        if jobs:
            all_jobs.extend(jobs)
            #print(f"Found {len(jobs)} jobs")
        else:
            print("No jobs found or there was an error fetching jobs.")
        
        # Add delay between requests to avoid rate limiting
        time.sleep(1.0)
    
    return all_jobs 