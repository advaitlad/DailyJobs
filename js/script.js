// List of companies (same as in greenhouse_scraper.py)
const companies = [
    'pinterest', 'samsara', 'carvana', 'spacex', 'mongodb', 'datadog',
    'robinhood', 'brex', 'stripe', 'airbnb', 'dropbox', 'asana',
    'squarespace', 'instacart', 'beyondfinance', 'lyft', 'udemy',
    'wrike', 'okta', 'yotpo', 'upwork', 'groupon', 'databricks',
    'twilio', 'roblox', 'esri', 'toast', 'affirm', 'airtable',
    'amplitude', 'apptronik', 'buzzfeed', '23andme', 'braze',
    'algolia', 'airbyte', 'notion', 'figma', 'retool', 'faire',
    'benchling', 'vercel', 'snyk', 'hashicorp', 'postman',
    'gitlab', 'carta', 'gusto', 'intercom', 'netlify', 'sentry',
    'webflow', 'discord', 'fivetran', 'clickhouse', 'cockroach'
];

// Populate companies grid
function populateCompanies() {
    const companiesGrid = document.getElementById('companiesGrid');
    
    companies.forEach(company => {
        const checkboxDiv = document.createElement('div');
        checkboxDiv.className = 'company-checkbox';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = company;
        checkbox.name = 'companies';
        checkbox.value = company;
        
        const label = document.createElement('label');
        label.htmlFor = company;
        label.textContent = company.charAt(0).toUpperCase() + company.slice(1);
        
        checkboxDiv.appendChild(checkbox);
        checkboxDiv.appendChild(label);
        companiesGrid.appendChild(checkboxDiv);
    });
}

// Handle form submission
document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const selectedCompanies = Array.from(document.querySelectorAll('input[name="companies"]:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedCompanies.length === 0) {
        alert('Please select at least one company');
        return;
    }
    
    try {
        // Add user to Firestore
        await db.collection('users').add({
            name,
            email,
            companies: selectedCompanies,
            createdAt: firebase.firestore.FieldValue.serverTimestamp()
        });
        
        // Show success message
        document.getElementById('successMessage').classList.remove('hidden');
        document.getElementById('signupForm').reset();
        
        // Hide success message after 5 seconds
        setTimeout(() => {
            document.getElementById('successMessage').classList.add('hidden');
        }, 5000);
        
    } catch (error) {
        console.error('Error adding user:', error);
        alert('There was an error processing your request. Please try again.');
    }
});

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    populateCompanies();
}); 