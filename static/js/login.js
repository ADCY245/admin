// DOM Elements
const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const loginInput = document.getElementById('login');
const passwordInput = document.getElementById('password');
const errorDiv = document.getElementById('error');
const messageDiv = document.getElementById('message');
const togglePassword = document.querySelector('.toggle-password');

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
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    togglePassword.innerHTML = '<i class="fas fa-eye-slash"></i>';
  } else {
    passwordInput.type = 'password';
    togglePassword.innerHTML = '<i class="fas fa-eye"></i>';
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
  
  // Handle Enter key in password field
  if (passwordInput) {
    passwordInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        handleLogin(e);
      }
    });
  }
}

// Handle login form submission
async function handleLogin(e) {
  if (e) e.preventDefault();
  
  const login = loginInput.value.trim();
  const password = passwordInput.value.trim();
  
  // Clear previous errors
  clearMessages();
  
  // Validate inputs
  if (!login) {
    showError('Please enter your email or username');
    loginInput.focus();
    return false;
  }
  
  if (!password) {
    showError('Please enter your password');
    passwordInput.focus();
    return false;
  }
  
  try {
    // Show loading state
    setLoading(true);
    
    // Create form data
    const formData = new FormData();
    formData.append('identifier', login);
    formData.append('password', password);
    
    // Send login request
    const response = await fetch('/auth/login', {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      redirect: 'manual' // Prevent automatic redirect
    });
    
    // Handle redirect response
    if (response.status === 302 || response.redirected) {
      const redirectUrl = response.headers.get('Location') || '/';
      window.location.href = redirectUrl;
      return false;
    }
    
    // Handle JSON response for API errors
    try {
      const data = await response.json();
      if (data.redirect) {
        window.location.href = data.redirect;
        return false;
      }
      
      if (response.ok && data.success) {
        window.location.href = data.redirectTo || '/';
        return false;
      } else {
        const errorMessage = data.error || data.message || 'Login failed. Please check your credentials.';
        showError(errorMessage);
        passwordInput.value = '';
        passwordInput.focus();
      }
    } catch (jsonError) {
      // If we can't parse JSON, it's likely a server-side redirect
      window.location.href = '/';
      return false;
    }
  } catch (error) {
    console.error('Login error:', error);
    showError('An error occurred. Please try again.');
  } finally {
    setLoading(false);
  }
  
  return false;
}

// Show error message
function showError(message) {
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
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
  if (!loginBtn) return;
  
  const btnText = loginBtn.querySelector('.btn-text');
  const btnLoader = loginBtn.querySelector('.btn-loader');
  
  if (isLoading) {
    loginBtn.disabled = true;
    if (btnText) btnText.style.visibility = 'hidden';
    if (btnLoader) btnLoader.style.display = 'flex';
  } else {
    loginBtn.disabled = false;
    if (btnText) btnText.style.visibility = 'visible';
    if (btnLoader) btnLoader.style.display = 'none';
  }
}

// Password toggle functionality added
