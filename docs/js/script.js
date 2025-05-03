// Load companies from JSON config
let companies = [];
let locations = {};

// Load both companies and locations config
Promise.all([
    fetch('./companies_config.json').then(response => response.json()),
    fetch('./locations_config.json').then(response => response.json())
])
.then(([companiesData, locationsData]) => {
    companies = Object.keys(companiesData.companies);
    locations = locationsData.locations;
    console.log('Loaded locations:', locations); // Debug log
    
    // Initialize the UI with the loaded data
    populateCompanies();
    populateLocations();
})
.catch(error => {
    console.error('Error loading config files:', error);
    showMessage('Error loading configuration. Please refresh the page.', true);
});

// Populate companies grid
function populateCompanies(selectedCompanies = [], searchTerm = '') {
    const selectedContainer = document.getElementById('selected-companies');
    const availableContainer = document.getElementById('available-companies');
    const noSelectedMessage = document.getElementById('no-selected');
    
    // Clear existing content
    selectedContainer.innerHTML = '';
    availableContainer.innerHTML = '';
    
    // Add no selection message (will be hidden if there are selections)
    selectedContainer.appendChild(noSelectedMessage);
    
    let selectedCount = 0;
    let availableCount = 0;
    
    // Create arrays to store labels for sorting
    const availableLabels = [];
    const selectedLabels = [];
    
    companies.forEach(company => {
        const label = document.createElement('label');
        label.className = 'company-checkbox-label';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = company;
        checkbox.className = 'company-checkbox';
        
        const span = document.createElement('span');
        span.textContent = company.charAt(0).toUpperCase() + company.slice(1);
        
        label.appendChild(checkbox);
        label.appendChild(span);
        
        // Add to appropriate container or array
        if (selectedCompanies.includes(company)) {
            // Always show selected companies regardless of search term
            checkbox.checked = true;
            selectedLabels.push({
                label: label,
                company: company.toLowerCase()
            });
            selectedCount++;
        } else {
            // Only show available companies that match the search term
            if (!searchTerm || company.toLowerCase().includes(searchTerm.toLowerCase())) {
                availableLabels.push({
                    label: label,
                    company: company.toLowerCase()
                });
                availableCount++;
            }
        }
        
        // Add click handler to move between containers
        checkbox.addEventListener('change', () => {
            const parentContainer = label.parentElement;
            if (checkbox.checked) {
                selectedContainer.appendChild(label);
                selectedCount++;
                availableCount--;
            } else {
                // When unchecking, insert into available container in sorted order
                const companies = Array.from(availableContainer.children)
                    .map(label => label.querySelector('input').value.toLowerCase());
                companies.push(company.toLowerCase());
                companies.sort();
                const index = companies.indexOf(company.toLowerCase());
                
                if (index === companies.length - 1) {
                    availableContainer.appendChild(label);
                } else {
                    const nextCompany = companies[index + 1];
                    const nextLabel = Array.from(availableContainer.children)
                        .find(l => l.querySelector('input').value.toLowerCase() === nextCompany);
                    availableContainer.insertBefore(label, nextLabel);
                }
                selectedCount--;
                availableCount++;
            }
            
            // Update counts
            document.getElementById('selected-count').textContent = selectedCount;
            document.getElementById('available-count').textContent = availableCount;
            
            // Toggle no selection message
            noSelectedMessage.style.display = selectedCount === 0 ? 'block' : 'none';
        });
    });
    
    // Sort and append available labels
    availableLabels.sort((a, b) => a.company.localeCompare(b.company));
    availableLabels.forEach(item => {
        availableContainer.appendChild(item.label);
    });

    // Sort and append selected labels
    selectedLabels.sort((a, b) => a.company.localeCompare(b.company));
    selectedLabels.forEach(item => {
        selectedContainer.appendChild(item.label);
    });
    
    // Set initial counts
    document.getElementById('selected-count').textContent = selectedCount;
    document.getElementById('available-count').textContent = availableCount;
    
    // Show/hide no selection message
    noSelectedMessage.style.display = selectedCount === 0 ? 'block' : 'none';
    noSelectedMessage.textContent = 'Please select at least one company to start receiving emails.';

    // Show message when no available companies match the search
    if (availableCount === 0 && searchTerm) {
        const noMatchesMessage = document.createElement('div');
        noMatchesMessage.className = 'no-companies';
        noMatchesMessage.textContent = 'No available companies match your search';
        availableContainer.appendChild(noMatchesMessage);
    }
}

// Function to populate location checkboxes
function populateLocations(selectedLocations = []) {
    const locationContainer = document.getElementById('location-types-grid');
    if (!locationContainer) {
        console.error('Location container not found');
        return;
    }
    
    locationContainer.innerHTML = ''; // Clear existing checkboxes
    
    // Add only the country/location name, no info icon or tooltip
    Object.entries(locations).forEach(([key, location]) => {
        const label = document.createElement('label');
        label.className = 'job-type-checkbox-label';
        label.innerHTML = `
            <input type="checkbox" class="location-checkbox" value="${key}">
            <span>${location.name}</span>
        `;
        locationContainer.appendChild(label);
    });
    
    // Set initial checked states
    if (selectedLocations) {
        document.querySelectorAll('.location-checkbox').forEach(checkbox => {
            checkbox.checked = selectedLocations.includes(checkbox.value);
        });
    }
}

// Save preferences to Firestore
async function savePreferences() {
    const user = auth.currentUser;
    if (!user) return;

    const saveBtn = document.getElementById('save-preferences');
    if (saveBtn) {
        saveBtn.disabled = true;
    }

    try {
        // Get selected companies
        const selectedCompanies = Array.from(document.querySelectorAll('#selected-companies .company-item'))
            .map(item => item.dataset.company.toLowerCase());

        // Get selected job types
        const selectedJobTypes = Array.from(document.querySelectorAll('.job-type-checkbox:checked'))
            .map(checkbox => checkbox.value);

        // Get selected experience levels
        const selectedExperienceLevels = Array.from(document.querySelectorAll('.experience-level-checkbox:checked'))
            .map(checkbox => checkbox.value);

        // Get selected locations
        const selectedLocations = Array.from(document.querySelectorAll('.location-checkbox:checked'))
            .map(checkbox => checkbox.value);

        // Update user document
        await db.collection('users').doc(user.uid).update({
            preferences: selectedCompanies,
            jobTypes: selectedJobTypes,
            experienceLevels: selectedExperienceLevels,
            locationPreferences: selectedLocations
        });

        // Visual feedback: turn button green and show message
        if (saveBtn) {
            saveBtn.classList.add('saved');
            saveBtn.textContent = '✓ Preferences saved successfully!';
        }
        setTimeout(() => {
            if (saveBtn) {
                saveBtn.classList.remove('saved');
                saveBtn.textContent = 'Save Preferences';
                saveBtn.disabled = false;
            }
        }, 2000);
    } catch (error) {
        console.error('Error saving preferences:', error);
        showMessage('Error saving preferences. Please try again.', true);
        if (saveBtn) {
            saveBtn.disabled = false;
        }
    }
}

// Load preferences from Firestore
async function loadPreferences() {
    const user = auth.currentUser;
    if (!user) return;

    try {
        const doc = await db.collection('users').doc(user.uid).get();
        if (doc.exists) {
            const data = doc.data();
            
            // Load company preferences
            if (data.preferences) {
                populateCompanies(data.preferences);
            } else {
                populateCompanies([]);
            }

            // Load job type preferences
            if (data.jobTypes) {
                document.querySelectorAll('.job-type-checkbox').forEach(checkbox => {
                    checkbox.checked = data.jobTypes.includes(checkbox.value);
                });
            }

            // Load experience level preferences
            if (data.experienceLevels) {
                document.querySelectorAll('.experience-level-checkbox').forEach(checkbox => {
                    checkbox.checked = data.experienceLevels.includes(checkbox.value);
                });
            }

            // Load location preferences
            if (data.locationPreferences) {
                populateLocations(data.locationPreferences);
            } else {
                populateLocations([]);
            }
        }
    } catch (error) {
        console.error('Error loading preferences:', error);
        showMessage('Error loading preferences. Please try again.', true);
    }
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
    // Add search functionality
    const searchInput = document.getElementById('company-search');
    if (searchInput) {
        let debounceTimeout;
        searchInput.addEventListener('input', (e) => {
            // Clear the previous timeout
            clearTimeout(debounceTimeout);
            
            // Set a new timeout to update the list
            debounceTimeout = setTimeout(() => {
                const selectedCompanies = Array.from(document.querySelectorAll('#selected-companies .company-checkbox'))
                    .map(checkbox => checkbox.value);
                populateCompanies(selectedCompanies, e.target.value.trim());
            }, 300); // Wait 300ms after user stops typing
        });
    }

    // Add All button functionality
    const addAllBtn = document.getElementById('add-all-btn');
    if (addAllBtn) {
        addAllBtn.addEventListener('click', () => {
            // Get all visible checkboxes in available companies
            const availableCheckboxes = document.querySelectorAll('#available-companies .company-checkbox');
            
            // Click each checkbox that isn't already checked
            availableCheckboxes.forEach(checkbox => {
                if (!checkbox.checked) {
                    checkbox.click(); // This will trigger the existing change event
                }
            });
        });
    }

    // Remove All button functionality
    const removeAllBtn = document.getElementById('remove-all-btn');
    if (removeAllBtn) {
        removeAllBtn.addEventListener('click', () => {
            // Get all checkboxes in selected companies
            const selectedCheckboxes = document.querySelectorAll('#selected-companies .company-checkbox');
            
            // Click each checked checkbox to unselect it
            selectedCheckboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    checkbox.click(); // This will trigger the existing change event
                }
            });
        });
    }

    // Toggle between signup and login forms
    const authToggle = document.getElementById('authToggle');
    if (authToggle) {
        authToggle.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-btn')) {
                document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                
                const formToShow = e.target.dataset.form;
                if (formToShow === 'signup') {
                    document.getElementById('signupForm').classList.remove('hidden');
                    document.getElementById('loginForm').classList.add('hidden');
                } else {
                    document.getElementById('loginForm').classList.remove('hidden');
                    document.getElementById('signupForm').classList.add('hidden');
                }
            }
        });
    }

    // Signup Form Handler
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Get form elements
            const nameInput = document.getElementById('name');
            const emailInput = document.getElementById('signupEmail');
            const passwordInput = document.getElementById('signupPassword');
            const confirmPasswordInput = document.getElementById('signupConfirmPassword');

            // Validate form elements exist
            if (!nameInput || !emailInput || !passwordInput || !confirmPasswordInput) {
                showMessage('Form elements not found. Please refresh the page.', true);
                return;
            }

            // Get form values
            const name = nameInput.value.trim();
            const email = emailInput.value.trim();
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;

            // Validate inputs
            if (!name || !email || !password || !confirmPassword) {
                showMessage('Please fill in all fields', true);
                return;
            }

            if (password !== confirmPassword) {
                showMessage('Passwords do not match', true);
                return;
            }

            try {
                await signupWithEmailPassword(name, email, password);
            } catch (error) {
                showMessage(error.message, true);
            }
        });
    }

    // Login Form Handler
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Get form elements
            const emailInput = document.getElementById('loginEmail');
            const passwordInput = document.getElementById('loginPassword');

            // Validate form elements exist
            if (!emailInput || !passwordInput) {
                showMessage('Form elements not found. Please refresh the page.', true);
                return;
            }

            // Get form values
            const email = emailInput.value.trim();
            const password = passwordInput.value;

            // Validate inputs
            if (!email || !password) {
                showMessage('Please fill in all fields', true);
                return;
            }

            try {
                await loginWithEmailPassword(email, password);
            } catch (error) {
                showMessage(error.message, true);
            }
        });
    }

    // Save preferences button
    const savePreferencesBtn = document.getElementById('save-preferences');
    if (savePreferencesBtn) {
        savePreferencesBtn.addEventListener('click', savePreferences);
    }

    // Sign out button handler
    const signOutBtn = document.getElementById('sign-out');
    if (signOutBtn) {
        signOutBtn.addEventListener('click', async () => {
            try {
                await signOut();
                // The auth state observer will handle UI updates
            } catch (error) {
                console.error('Error signing out:', error);
                showMessage('Failed to sign out. Please try again.', true);
            }
        });
    }

    // Initialize auth state observer
    auth.onAuthStateChanged((user) => {
        if (user) {
            if (user.emailVerified) {
                document.getElementById('auth-container').classList.add('hidden');
                document.getElementById('verification-container').classList.add('hidden');
                document.getElementById('preferences-container').classList.remove('hidden');
                
                // Set user info
                document.getElementById('userDisplayName').textContent = user.displayName || 'User';
                document.getElementById('userEmail').textContent = user.email;
                
                // Load preferences
                loadPreferences();
            } else {
                document.getElementById('auth-container').classList.add('hidden');
                document.getElementById('preferences-container').classList.add('hidden');
                document.getElementById('verification-container').classList.remove('hidden');
            }
        } else {
            document.getElementById('auth-container').classList.remove('hidden');
            document.getElementById('preferences-container').classList.add('hidden');
            document.getElementById('verification-container').classList.add('hidden');
        }
    });

    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const userInfo = document.querySelector('.user-info');
    const preferencesContainer = document.querySelector('.preferences-container');
    const stickyFooter = document.querySelector('.sticky-footer');

    if (sidebarToggle && userInfo && preferencesContainer && stickyFooter) {
        // Check local storage for saved state
        const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (isSidebarCollapsed) {
            userInfo.classList.add('collapsed');
            sidebarToggle.classList.add('collapsed');
            preferencesContainer.classList.add('sidebar-collapsed');
            stickyFooter.classList.add('sidebar-collapsed');
        }

        sidebarToggle.addEventListener('click', () => {
            userInfo.classList.toggle('collapsed');
            sidebarToggle.classList.toggle('collapsed');
            preferencesContainer.classList.toggle('sidebar-collapsed');
            stickyFooter.classList.toggle('sidebar-collapsed');
            // Save state to local storage
            localStorage.setItem('sidebarCollapsed', userInfo.classList.contains('collapsed'));
        });
    }

    // Handle "Any Location" checkbox
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('location-checkbox')) {
            const anyLocationCheckbox = document.querySelector('.location-checkbox[value="any"]');
            const otherLocationCheckboxes = document.querySelectorAll('.location-checkbox:not([value="any"])');
            
            if (e.target === anyLocationCheckbox) {
                // If "Any Location" is checked, uncheck all others
                if (e.target.checked) {
                    otherLocationCheckboxes.forEach(checkbox => {
                        checkbox.checked = false;
                    });
                }
            } else {
                // If any other location is checked, uncheck "Any Location"
                if (e.target.checked) {
                    anyLocationCheckbox.checked = false;
                }
            }
        }
    });
}); 