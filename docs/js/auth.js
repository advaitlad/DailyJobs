// Initialize Firebase Auth
const auth = firebase.auth();

// Auth state observer
auth.onAuthStateChanged(async (user) => {
    if (user) {
        console.log('Auth state changed:', user.email, 'Verified:', user.emailVerified); // Debug log
        
        // User is signed in
        document.getElementById('userDisplayName').textContent = user.displayName || 'User';
        document.getElementById('userEmail').textContent = user.email;

        // Force email verification check
        await user.reload(); // Reload user to get latest verification status
        
        // Check if email is verified
        if (!user.emailVerified) {
            console.log('Email not verified, showing verification container'); // Debug log
            // Hide all containers except verification
            document.getElementById('auth-container').classList.add('hidden');
            document.getElementById('preferences-container').classList.add('hidden');
            document.getElementById('verification-container').classList.remove('hidden');
            
            // Show verification required message
            showMessage('Please verify your email address before continuing. Check your inbox and spam folder.', false);
            return;
        }

        console.log('Email verified, showing preferences'); // Debug log
        // Email is verified, show preferences
        document.getElementById('auth-container').classList.add('hidden');
        document.getElementById('verification-container').classList.add('hidden');
        document.getElementById('preferences-container').classList.remove('hidden');
        
        // Load user preferences
        await loadUserPreferences(user.uid);
    } else {
        console.log('User signed out'); // Debug log
        // User is signed out
        document.getElementById('auth-container').classList.remove('hidden');
        document.getElementById('verification-container').classList.add('hidden');
        document.getElementById('preferences-container').classList.add('hidden');
    }
});

// Email/Password Login
async function loginWithEmailPassword(email, password) {
    try {
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        await ensureUserDocument(userCredential.user);
        showMessage('Successfully logged in!');
    } catch (error) {
        console.error('Login error:', error);
        let errorMessage = 'Failed to log in. Please try again.';
        if (error.code === 'auth/user-not-found') {
            errorMessage = 'No account found with this email. Please sign up first.';
        } else if (error.code === 'auth/wrong-password') {
            errorMessage = 'Incorrect password. Please try again.';
        }
        showMessage(errorMessage, true);
    }
}

// Email/Password Sign Up
async function signupWithEmailPassword(fullName, email, password) {
    try {
        console.log('Starting signup process for:', email); // Debug log
        
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;

        console.log('User created:', user.uid); // Debug log

        // Update user profile first
        await user.updateProfile({
            displayName: fullName
        });
        console.log('Profile updated with name:', fullName); // Debug log

        // Get the current domain
        const currentDomain = 'https://advaitlad.github.io/DailyJobs';
        console.log('Current domain:', currentDomain); // Debug log

        // Send email verification
        const actionCodeSettings = {
            url: currentDomain,
            handleCodeInApp: false
        };
        console.log('Verification settings:', actionCodeSettings); // Debug log

        // Ensure verification email is sent
        await user.sendEmailVerification(actionCodeSettings);
        console.log('Verification email sent successfully to:', email); // Debug log
        
        // Create user document with verified status explicitly set to false
        await ensureUserDocument(user, fullName, false);
        console.log('User document created/updated for:', user.uid); // Debug log
        
        // Force a reload of the user to ensure we have the latest state
        await user.reload();
        console.log('User state reloaded, verified:', user.emailVerified); // Debug log
        
        showMessage('✓ Account created! Please check your email (including spam folder) to verify your account.', false);
        
        // Show verification container immediately
        document.getElementById('auth-container').classList.add('hidden');
        document.getElementById('preferences-container').classList.add('hidden');
        document.getElementById('verification-container').classList.remove('hidden');
        
    } catch (error) {
        console.error('Signup error details:', {
            code: error.code,
            message: error.message,
            fullError: error
        });
        
        let errorMessage = 'Failed to create account. Please try again.';
        if (error.code === 'auth/email-already-in-use') {
            errorMessage = 'An account already exists with this email. Please sign in.';
        } else if (error.code === 'auth/invalid-email') {
            errorMessage = 'Invalid email address. Please check and try again.';
        } else if (error.code === 'auth/operation-not-allowed') {
            errorMessage = 'Email/password accounts are not enabled. Please contact support.';
        } else if (error.code === 'auth/weak-password') {
            errorMessage = 'Password is too weak. Please use a stronger password.';
        }
        showMessage(errorMessage, true);
        throw error;
    }
}

// Sign Out
async function signOut() {
    try {
        await auth.signOut();
        showMessage('Successfully signed out!');
    } catch (error) {
        console.error('Sign out error:', error);
        showMessage('Failed to sign out. Please try again.', true);
    }
}

// Save user preferences
async function saveUserPreferences(preferences) {
    try {
        const user = auth.currentUser;
        if (!user) throw new Error('No user is currently signed in');

        await db.collection('users').doc(user.uid).set({
            preferences: preferences,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp()
        }, { merge: true });

        showMessage('Preferences saved successfully!', false, true);
    } catch (error) {
        console.error('Save preferences error:', error);
        showMessage('Failed to save preferences. Please try again.', true, true);
    }
}

// Load user preferences
async function loadUserPreferences(userId) {
    try {
        const doc = await db.collection('users').doc(userId).get();
        if (doc.exists) {
            const data = doc.data();
            if (data.preferences) {
                // Update UI checkboxes based on saved preferences
                const companies = document.querySelectorAll('.company-checkbox');
                companies.forEach(checkbox => {
                    checkbox.checked = data.preferences.includes(checkbox.value);
                });
            }
        }
    } catch (error) {
        console.error('Load preferences error:', error);
        showMessage('Failed to load preferences. Please refresh the page.', true);
    }
}

// Ensure user document exists and is up to date
async function ensureUserDocument(user, fullName = null, isVerified = null) {
    try {
        const userDoc = await db.collection('users').doc(user.uid).get();
        const userData = {
            email: user.email,
            name: fullName || user.displayName || 'User',
            lastSignIn: firebase.firestore.FieldValue.serverTimestamp(),
            emailVerified: isVerified !== null ? isVerified : user.emailVerified
        };

        if (!userDoc.exists) {
            // Create new user document
            await db.collection('users').doc(user.uid).set({
                ...userData,
                preferences: [],
                createdAt: firebase.firestore.FieldValue.serverTimestamp()
            });
        } else {
            // Update existing user document
            await db.collection('users').doc(user.uid).update(userData);
        }
    } catch (error) {
        console.error('Error ensuring user document:', error);
        throw error;
    }
}

// Helper function to show messages with better visibility
function showMessage(message, isError = false, isPreferences = false) {
    const messageDiv = isPreferences ? 
        document.getElementById('preferences-message') : 
        document.getElementById('message');
    
    if (!messageDiv) return;
    
    messageDiv.textContent = message;
    messageDiv.className = isError ? 'message error' : 'message success';
    messageDiv.style.display = 'block';
    
    // Don't auto-hide verification-related messages
    if (!message.includes('verification') && !message.includes('verify')) {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}

// Track last verification email sent time and retry count
let lastVerificationEmailSent = 0;
let retryCount = 0;
const VERIFICATION_EMAIL_COOLDOWN = 60000; // 1 minute cooldown
const MAX_RETRIES = 3;
const RETRY_RESET_TIME = 3600000; // 1 hour to reset retry count

// Timer functionality
let timerInterval;

function startTimer(duration) {
    const timerDisplay = document.getElementById('timer-countdown');
    const timerContainer = document.querySelector('.verification-timer');
    let timer = duration;

    // Show timer container
    if (timerContainer) {
        timerContainer.style.display = 'flex';
    }

    // Clear any existing interval
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    timerInterval = setInterval(() => {
        const minutes = Math.floor(timer / 60);
        const seconds = timer % 60;

        if (timerDisplay) {
            timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }

        if (--timer < 0) {
            clearInterval(timerInterval);
            if (timerContainer) {
                timerContainer.style.display = 'none';
            }
            // Clear error message when timer completes
            const verificationMessage = document.getElementById('verification-message');
            if (verificationMessage) {
                verificationMessage.style.display = 'none';
            }
            
            const resendButton = document.getElementById('resend-verification');
            if (resendButton) {
                resendButton.disabled = false;
                resendButton.textContent = 'Resend Verification Email';
            }
            // Reset retry count if enough time has passed
            if (Date.now() - lastVerificationEmailSent >= RETRY_RESET_TIME) {
                retryCount = 0;
            }
        }
    }, 1000);
}

// Helper function to show verification messages
function showVerificationMessage(message, isError = false) {
    const messageDiv = document.getElementById('verification-message');
    if (!messageDiv) return;

    // Create a more prominent message for wait times
    if (message.includes('wait') || message.includes('minutes')) {
        messageDiv.innerHTML = `
            <div class="verification-wait-message">
                <div class="wait-icon">⏳</div>
                <div class="wait-text">${message}</div>
            </div>
        `;
    } else {
        messageDiv.textContent = message;
    }
    
    messageDiv.className = 'verification-message ' + (isError ? 'error' : 'success');
    messageDiv.style.display = 'block';
}

// Update resendVerificationEmail function
async function resendVerificationEmail() {
    const resendButton = document.getElementById('resend-verification');
    if (!resendButton) return;

    try {
        const user = auth.currentUser;
        if (!user) {
            console.log('No user signed in'); // Debug log
            showVerificationMessage('No user is currently signed in.', true);
            return;
        }

        console.log('Current user:', user.email); // Debug log

        // Force reload user to get latest verification status
        await user.reload();
        console.log('User reloaded, verified status:', user.emailVerified); // Debug log
        
        if (user.emailVerified) {
            console.log('User already verified'); // Debug log
            showVerificationMessage('Your email is already verified! Refreshing page...', false);
            setTimeout(() => window.location.reload(), 2000);
            return;
        }

        // Check if retry count exceeded
        if (retryCount >= MAX_RETRIES) {
            console.log('Max retries exceeded. Count:', retryCount); // Debug log
            const timeUntilReset = Math.ceil((RETRY_RESET_TIME - (Date.now() - lastVerificationEmailSent)) / 60000);
            showVerificationMessage(`Maximum retry limit reached. Please wait ${timeUntilReset} minutes before trying again.`, true);
            startTimer(timeUntilReset * 60);
            return;
        }

        // Check if enough time has passed since last email
        const now = Date.now();
        const timeElapsed = now - lastVerificationEmailSent;
        console.log('Time elapsed since last email:', timeElapsed/1000, 'seconds'); // Debug log
        
        if (timeElapsed < VERIFICATION_EMAIL_COOLDOWN) {
            const waitTime = Math.ceil((VERIFICATION_EMAIL_COOLDOWN - timeElapsed) / 1000);
            console.log('Need to wait:', waitTime, 'seconds'); // Debug log
            showVerificationMessage(`Please wait ${Math.ceil(waitTime/60)} minute(s) before requesting another verification email.`, true);
            startTimer(waitTime);
            return;
        }

        // Reset retry count if enough time has passed
        if (timeElapsed >= RETRY_RESET_TIME) {
            console.log('Resetting retry count'); // Debug log
            retryCount = 0;
        }

        // Update button state
        resendButton.disabled = true;
        resendButton.textContent = 'Sending...';

        // Get the current domain
        const currentDomain = 'https://advaitlad.github.io/DailyJobs';
        console.log('Current domain for verification:', currentDomain); // Debug log

        const actionCodeSettings = {
            url: currentDomain,
            handleCodeInApp: false
        };
        console.log('Sending verification with settings:', actionCodeSettings); // Debug log
        
        await user.sendEmailVerification(actionCodeSettings);
        console.log('Verification email sent successfully'); // Debug log
        
        lastVerificationEmailSent = now;
        retryCount++;
        console.log('Updated retry count:', retryCount); // Debug log

        // Show success message and update button
        const remainingAttempts = MAX_RETRIES - retryCount;
        showVerificationMessage(`✓ Verification email sent! Please check your inbox and spam folder. You have ${remainingAttempts} attempt(s) remaining.`, false);
        resendButton.textContent = 'Email Sent ✓';

        // Start the cooldown timer
        startTimer(VERIFICATION_EMAIL_COOLDOWN / 1000);

    } catch (error) {
        console.error('Verification error details:', {
            code: error.code,
            message: error.message,
            fullError: error
        });
        
        let errorMessage = 'Failed to send verification email. ';
        
        if (error.code === 'auth/too-many-requests') {
            const waitTime = Math.min(30, Math.pow(2, retryCount)) * 60; // Exponential backoff
            errorMessage = `Too many attempts. Please wait ${Math.ceil(waitTime/60)} minutes before trying again.`;
            startTimer(waitTime);
            retryCount++;
        } else if (error.code === 'auth/invalid-continue-uri') {
            errorMessage += 'Invalid redirect URL. Please contact support.';
            console.error('Current domain that was rejected:', window.location.origin);
        } else if (error.code === 'auth/requires-recent-login') {
            errorMessage = 'Please sign out and sign in again to verify your email.';
        } else if (error.code === 'auth/unauthorized-continue-uri') {
            errorMessage = 'This domain is not authorized. Please contact support.';
            console.error('Unauthorized domain:', window.location.origin);
        } else {
            errorMessage += 'Please try again later.';
        }
        
        showVerificationMessage(errorMessage, true);
        
        // Reset button state
        resendButton.disabled = false;
        resendButton.textContent = 'Resend Verification Email';
    }
}

// Initialize verification email functionality
document.addEventListener('DOMContentLoaded', () => {
    const resendButton = document.getElementById('resend-verification');
    if (resendButton) {
        resendButton.addEventListener('click', resendVerificationEmail);
    }

    // Hide timer initially
    const timerContainer = document.querySelector('.verification-timer');
    if (timerContainer) {
        timerContainer.style.display = 'none';
    }
});