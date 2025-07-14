document.addEventListener('DOMContentLoaded', function() {
  const loginForm = document.getElementById('loginForm');
  const errorAlert = document.getElementById('errorAlert');
  const loginButton = loginForm?.querySelector('button[type="submit"]');
  const togglePasswordButtons = document.querySelectorAll('.toggle-password');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');

  // Toggle password visibility
  if (togglePasswordButtons.length > 0) {
    togglePasswordButtons.forEach(button => {
      button.addEventListener('click', function() {
        const passwordInput = this.parentElement.querySelector('input[type="password"], input[type="text"]');
        if (passwordInput) {
          const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
          passwordInput.setAttribute('type', type);
          const icon = this.querySelector('i');
          if (icon) {
            icon.classList.toggle('fa-eye');
            icon.classList.toggle('fa-eye-slash');
          }
        }
      });
    });
  }

  if (!loginForm) return;

  loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Show loading state
    if (loginButton) {
      loginButton.disabled = true;
      loginButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Signing in...';
    }

    // Get CSRF token from form or meta tag
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value ||
                     document.querySelector('meta[name="csrf-token"]')?.content;

    if (!csrfToken) {
      console.error('CSRF token not found');
      showError('Security error. Please refresh the page and try again.');
      resetLoginButton();
      return;
    }

    try {
      const formData = new FormData(loginForm);

      // Add CSRF token to form data if not already included
      if (!formData.has('csrf_token')) {
        formData.append('csrf_token', csrfToken);
      }

      const response = await fetch(loginForm.action, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData,
        credentials: 'same-origin',
        redirect: 'manual' // Prevent automatic redirect
      });

      // Check if response is JSON
      const contentType = response.headers.get('content-type');
      let data = {};

      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // If not JSON, it might be a redirect
        if (response.redirected || response.status === 302) {
          const redirectUrl = response.headers.get('Location') || '/';
          window.location.href = redirectUrl;
          return;
        }
        throw new Error('Unexpected response from server');
      }

      if (response.ok) {
        // Handle successful login
        console.log('Login successful:', data);

        // If there's a redirect URL in the response, use it
        if (data.redirect) {
          window.location.href = data.redirect;
        } else if (response.redirected) {
          window.location.href = response.url;
        } else {
          // Default redirect if none provided
          window.location.href = '/';
        }
      } else {
        // Handle login error
        console.error('Login error:', data);
        const errorMessage = data.message || data.error || 'Invalid email/username or password';
        showError(errorMessage);
      }
    } catch (error) {
      console.error('Login error:', error);
      showError('An error occurred. Please try again.');
    } finally {
      resetLoginButton();
    }
  });

  function showError(message) {
    if (!message) return;

    if (errorAlert) {
      errorAlert.textContent = message;
      errorAlert.style.display = 'block';

      // Hide error after 5 seconds
      setTimeout(() => {
        if (errorAlert) {
          errorAlert.style.display = 'none';
        }
      }, 5000);
    } else {
      alert(message); // Fallback if error alert element is not found
    }
  }

  function resetLoginButton() {
    if (loginButton) {
      loginButton.disabled = false;
      loginButton.innerHTML = 'Sign In';
    }
  }

  // Hide error message when user starts typing
  if (emailInput) {
    emailInput.addEventListener('input', () => {
      if (errorAlert) {
        errorAlert.style.display = 'none';
      }
    });
  }

  if (passwordInput) {
    passwordInput.addEventListener('input', () => {
      if (errorAlert) {
        errorAlert.style.display = 'none';
      }
    });
  }
});