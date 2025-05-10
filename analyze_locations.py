import requests
import json
import os
from collections import Counter, defaultdict
from typing import Dict, List, Set
import re
import pycountry
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time

# US state codes mapping
US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
}

# Common US cities
US_CITIES = {
    'New York', 'San Francisco', 'Los Angeles', 'Chicago', 'Boston',
    'Seattle', 'Austin', 'Denver', 'Portland', 'Miami', 'Philadelphia',
    'Washington DC', 'Atlanta', 'Raleigh', 'Palo Alto', 'San Jose',
    'Mountain View', 'Sunnyvale'
}

# Major international cities mapping
INTERNATIONAL_CITIES = {
    'Sydney': 'Australia',
    'Melbourne': 'Australia',
    'Brisbane': 'Australia',
    'Gurugram': 'India',
    'Bangalore': 'India',
    'Bengaluru': 'India',
    'Mumbai': 'India',
    'Delhi': 'India',
    'Hyderabad': 'India',
    'Chennai':'India',
    'Mexico City': 'Mexico',
    'Monterrey': 'Mexico',
    'Guadalajara': 'Mexico',
    'Dublin': 'Ireland',
    'London': 'United Kingdom',
    'Manchester': 'United Kingdom',
    'Edinburgh': 'United Kingdom',
    'Barcelona': 'Spain',
    'Madrid': 'Spain',
    'Toronto': 'Canada',
    'Vancouver': 'Canada',
    'Montreal': 'Canada',
    'Paris': 'France',
    'Berlin': 'Germany',
    'Munich': 'Germany',
    'Amsterdam': 'Netherlands',
    'Copenhagen': 'Denmark',
    'Warsaw': 'Poland',
    'Taipei': 'Taiwan, Province of China'
}

# Cache for country lookups
@lru_cache(maxsize=1000)
def get_country_from_name(name: str) -> str:
    """Cached function to get country name from pycountry"""
    try:
        return pycountry.countries.search_fuzzy(name)[0].name
    except (LookupError, IndexError):
        return 'Unknown'

# def load_companies() -> Dict[str, str]:
#     """Load companies from config file"""
#     config_path = os.path.join('docs', 'greenhouse_companies_config.json')
#     with open(config_path, 'r') as f:
#         return json.load(f)['companies']

# def categorize_location(location: str) -> str:
#     """Categorize location format"""
#     if location == 'N/A':
#         return 'N/A'
#     if location == 'Remote':
#         return 'Remote'
        
    # Common country patterns
    countries = {'United States', 'Canada', 'UK', 'India', 'Australia', 'Germany'}
    if location in countries:
        return 'Country only'
        
    # US state pattern (City, ST)
    if re.match(r'^[\w\s]+,\s*[A-Z]{2}$', location):
        return 'US City, State'
        
    # US state pattern with country (City, ST, United States)
    if re.match(r'^[\w\s]+,\s*[A-Z]{2},\s*United States$', location):
        return 'US City, State, Country'
        
    # International city with country
    if ',' in location and not any(state in location for state in ['CA', 'NY', 'TX', 'WA']):
        return 'International City, Country'
        
    return 'Other'

# def analyze_locations():
#     companies = load_companies()
#     location_stats = Counter()
#     format_stats = Counter()
#     countries = defaultdict(int)
#     state_analysis = defaultdict(list)
#     total_jobs = 0
    
#     print("Analyzing job locations...")
    
#     for company_name, board_token in companies.items():
#         url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
#         try:
#             response = requests.get(url)
#             response.raise_for_status()
#             jobs_data = response.json()['jobs']
            
#             for job in jobs_data:
#                 total_jobs += 1
#                 location = job.get('location', {}).get('name', 'N/A')
#                 location_stats[location] += 1
                
#                 # Analyze format
#                 format_type = categorize_location(location)
#                 format_stats[format_type] += 1
                
#                 # Extract country if present
#                 if 'United States' in location or ', US' in location:
#                     countries['United States'] += 1
#                 elif any(country in location for country in ['Canada', 'UK', 'India', 'Australia', 'Germany']):
#                     for country in ['Canada', 'UK', 'India', 'Australia', 'Germany']:
#                         if country in location:
#                             countries[country] += 1
#                             break
                
#                 # Analyze state codes
#                 parts = location.split(',')
#                 if len(parts) >= 2:
#                     state_code = parts[1].strip()
#                     if state_code in US_STATES:
#                         # Store the full location string for this state code
#                         state_analysis[state_code].append(location)
                
#         except Exception as e:
#             print(f"Error fetching jobs for {company_name}: {e}")
    
#     print("\nLocation Format Analysis:")
#     print(f"Total jobs analyzed: {total_jobs}")
#     for format_type, count in format_stats.most_common():
#         print(f"{format_type}: {count} jobs ({count/total_jobs*100:.1f}%)")
    
#     print("\nTop 10 most common specific locations:")
#     for location, count in location_stats.most_common(10):
#         print(f"{location}: {count} jobs ({count/total_jobs*100:.1f}%)")
    
#     print("\nCountry distribution:")
#     for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
#         print(f"{country}: {count} jobs ({count/total_jobs*100:.1f}%)")

#     print("\nAnalysis of locations with US State Codes:")
#     print("==========================================")
    
#     total_state_matches = 0
#     for state_code in sorted(state_analysis.keys()):
#         locations = state_analysis[state_code]
#         total_state_matches += len(locations)
#         print(f"\nState code {state_code}:")
#         print(f"Total locations: {len(locations)}")
#         print("Sample locations:")
#         # Show up to 5 examples for each state
#         for loc in sorted(set(locations))[:5]:
#             print(f"  - {loc}")
    
#     print("\nSummary:")
#     print(f"Total jobs analyzed: {total_jobs}")
#     print(f"Jobs with US state codes: {total_state_matches} ({total_state_matches/total_jobs*100:.1f}%)")

def identify_single_country(location: str) -> str:
    """Helper function to identify country for a single location"""
    # First check for US state codes
    if any(state in location for state in US_STATES):
        return 'United States'
    
    # Check for common US city patterns
    if any(city in location for city in US_CITIES):
        return 'United States'
    
    # Check for international cities
    for city, country in INTERNATIONAL_CITIES.items():
        if city in location:
            return country
    
    # Split location into parts and try to find country in each part
    parts = [part.strip() for part in location.split(',')]
    
    # Try to find country in each part, starting from the end (most common format)
    for part in reversed(parts):
        country = get_country_from_name(part)
        if country != 'Unknown':
            return country
            
    # If no country found, check for common variations
    location_lower = location.lower()
    if 'united states' in location_lower or 'usa' in location_lower or 'u.s.' in location_lower:
        return 'United States'
    if 'united kingdom' in location_lower or 'uk' in location_lower or 'england' in location_lower:
        return 'United Kingdom'
    if 'bay area' in location_lower or 'sf' in location_lower:
        return 'United States'
    if 'remote' in location_lower:
        return 'Remote'
        
    return 'Unknown'

def identify_country(location: str) -> str:
    """Identify the country from a location string using pycountry"""
    if location == 'N/A':
        return location
        
    # Handle multiple locations (separated by semicolons)
    if ';' in location:
        locations = [loc.strip() for loc in location.split(';')]
        # Get countries for all locations
        countries = set()  # Using set to automatically handle duplicates
        for loc in locations:
            # Check if location contains both Remote and country info
            if 'remote' in loc.lower():
                countries.add('Remote')
                # Remove 'remote' from the string to check for country
                loc = re.sub(r'remote,?\s*', '', loc, flags=re.IGNORECASE).strip()
                if loc:
                    country = identify_single_country(loc)
                    if country != 'Unknown':
                        countries.add(country)
            else:
                country = identify_single_country(loc)
                if country != 'Unknown':
                    countries.add(country)
        
        if countries:
            return '; '.join(sorted(countries))
        return 'Unknown'
    
    # Handle single location with Remote
    if 'remote' in location.lower():
        countries = set()  # Using set to automatically handle duplicates
        countries.add('Remote')
        # Remove 'remote' from the string to check for country
        loc = re.sub(r'remote,?\s*', '', location, flags=re.IGNORECASE).strip()
        if loc:
            country = identify_single_country(loc)
            if country != 'Unknown':
                countries.add(country)
        return '; '.join(sorted(countries))
    
    # Handle single location without Remote
    country = identify_single_country(location)
    return country if country != 'Unknown' else 'Unknown'

if __name__ == "__main__":
    pass  # No main function needed as this is a utility module 