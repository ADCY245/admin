// DOM Elements
const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const loginInput = document.getElementById('login');
const passwordInput = document.getElementById('password');
const errorDiv = document.getElementById('error');
const messageDiv = document.getElementById('message');
const togglePassword = document.querySelector('.toggle-password');
const btnText = loginBtn ? loginBtn.querySelector('.btn-text') : null;
const btnLoader = loginBtn ? loginBtn.querySelector('.btn-loader') : null;

// Initialize the login form
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  
  // Check for success message in URL (after registration)
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('registered') === 'true') {
    showMessage('Registration successful! Please sign in to continue.', 'success');
  }
  
  // Auto-focus the login input
  if (loginInput) {
    loginInput.focus();
  }
});

// Toggle password visibility
function togglePasswordVisibility() {
  if (passwordInput) {
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      if (togglePassword) {
        togglePassword.innerHTML = '<i class="fas fa-eye-slash"></i>';
      }
    } else {
      passwordInput.type = 'password';
      if (togglePassword) {
        togglePassword.innerHTML = '<i class="fas fa-eye"></i>';
      }
    }
  }
}

// Setup event listeners
function setupEventListeners() {
  // Login form submission
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
  
  // Toggle password visibility
  if (togglePassword) {
    togglePassword.addEventListener('click', togglePasswordVisibility);
  }
  
  // Handle Enter key in login and password fields
  [loginInput, passwordInput].forEach(input => {
    if (input) {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleLogin(e);
        }
      });
    }
  });
}

// Handle login form submission
async function handleLogin(e) {
  if (e) e.preventDefault();
  
  const login = loginInput ? loginInput.value.trim() : '';
  const password = passwordInput ? passwordInput.value.trim() : '';
  const form = e ? e.target : document.getElementById('loginForm');
  
  // Clear previous errors and messages
  clearMessages();
  
  // Validate inputs
  if (!login) {
    showError('Please enter your email or username');
    if (loginInput) loginInput.focus();
    return false;
  }
  
  if (!password) {
    showError('Please enter your password');
    if (passwordInput) passwordInput.focus();
    return false;
  }
  
  try {
    // Show loading state
    setLoading(true);
    
    // Get the CSRF token from the form
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
    
    // Create form data from the actual form
    const formData = new FormData(form);
    
    console.log('Sending login request...');
    console.log('Form data:', Object.fromEntries(formData.entries()));
    
    // Send login request
    const response = await fetch(form.action || '/auth/login', {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin',
      redirect: 'manual' // Prevent automatic redirect
    });
    
    console.log('Response status:', response.status);
    
    // Handle redirect response
    if (response.status === 302 || response.redirected) {
      const redirectUrl = response.headers.get('Location') || '/';
      console.log('Redirecting to:', redirectUrl);
      window.location.href = redirectUrl;
      return false;
    }
    
    // Handle JSON response for API errors
    try {
      const data = await response.json();
      console.log('Response data:', data);
      
      if (response.ok && data.success) {
        // Handle successful login
        const redirectTo = data.redirect || data.redirectTo || '/';
        console.log('Login successful, redirecting to:', redirectTo);
        
        // If we're already on the welcome page, let it handle the final redirect
        if (!window.location.pathname.includes('/welcome')) {
          window.location.href = redirectTo;
        }
      } else {
        // Show error message from server or default message
        const errorMessage = data.error || data.message || 'Login failed. Please check your credentials.';
        showError(errorMessage);
        
        // Clear password field on failed login
        if (passwordInput) {
          passwordInput.value = '';
          passwordInput.focus();
        }
      }
    } catch (jsonError) {
      console.error('Error parsing JSON response:', jsonError);
      // If we can't parse JSON, it's likely a server-side redirect
      window.location.href = '/';
      return false;
    }
  } catch (error) {
    console.error('Login error:', error);
    showError('An error occurred. Please try again.');
    
    // Reset loading state
    setLoading(false);
    
    // Re-enable form submission
    if (loginForm) {
      loginForm.onsubmit = (e) => {
        e.preventDefault();
        handleLogin(e);
      };
    }
  }
}

// Show error message
function showError(message) {
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Auto-hide error after 5 seconds
    setTimeout(() => {
      if (errorDiv) {
        errorDiv.style.display = 'none';
      }
    }, 5000);
  }
  
  // Also log to console for debugging
  console.error('Login error:', message);
}

// Show success message
function showMessage(message, type = 'success') {
  if (messageDiv) {
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';
    messageDiv.className = `message ${type}`;
    messageDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Auto-hide success message after 5 seconds
    if (type === 'success') {
      setTimeout(() => {
        messageDiv.style.display = 'none';
      }, 5000);
    }
  }
}

// Clear all messages
function clearMessages() {
  if (errorDiv) {
    errorDiv.textContent = '';
    errorDiv.style.display = 'none';
  }
  
  if (messageDiv) {
    messageDiv.textContent = '';
    messageDiv.style.display = 'none';
    messageDiv.className = 'message';
  }
}

// Set loading state
function setLoading(isLoading) {
  if (!loginBtn || !btnText || !btnLoader) return;
  
  if (isLoading) {
    loginBtn.disabled = true;
    btnText.style.visibility = 'hidden';
    btnLoader.style.display = 'block';
  } else {
    loginBtn.disabled = false;
    btnText.style.visibility = 'visible';
    btnLoader.style.display = 'none';
  }
}

// Password toggle functionality added