// ============================================================================
// GLOBAL VARIABLES AND INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('ML Project Application Loaded');
    
    // Initialize all components
    initAnimations();
    initFormValidation();
    initFileUpload();
    initModelSelector();
    initPredictionForm();
    initAlerts();
    initTooltips();
});

// ============================================================================
// ANIMATIONS
// ============================================================================

function initAnimations() {
    // Fade in elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all cards and sections
    document.querySelectorAll('.content-card, .feature-card, .algo-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Animate numbers
    animateNumbers();
}

function animateNumbers() {
    const numbers = document.querySelectorAll('.stat-box h2, .metric-value');
    
    numbers.forEach(number => {
        const value = parseFloat(number.textContent);
        if (!isNaN(value)) {
            let current = 0;
            const increment = value / 50;
            const timer = setInterval(() => {
                current += increment;
                if (current >= value) {
                    number.textContent = value.toFixed(4);
                    clearInterval(timer);
                } else {
                    number.textContent = current.toFixed(4);
                }
            }, 20);
        }
    });
}

// ============================================================================
// FORM VALIDATION
// ============================================================================

function initFormValidation() {
    // Register form validation
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            if (!validateRegisterForm()) {
                e.preventDefault();
            }
        });
        
        // Real-time password matching
        const password = document.getElementById('password');
        const confirmPassword = document.getElementById('confirm_password');
        
        if (confirmPassword) {
            confirmPassword.addEventListener('input', function() {
                if (password.value !== confirmPassword.value) {
                    confirmPassword.setCustomValidity('Passwords do not match');
                    confirmPassword.classList.add('is-invalid');
                } else {
                    confirmPassword.setCustomValidity('');
                    confirmPassword.classList.remove('is-invalid');
                    confirmPassword.classList.add('is-valid');
                }
            });
        }
    }
    
    // Login form validation
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            if (!validateLoginForm()) {
                e.preventDefault();
            }
        });
    }
}

function validateRegisterForm() {
    const fullName = document.getElementById('full_name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    
    // Full name validation
    if (fullName.length < 3) {
        showAlert('Full name must be at least 3 characters long', 'error');
        return false;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showAlert('Please enter a valid email address', 'error');
        return false;
    }
    
    // Phone validation
    const phoneRegex = /^[0-9]{10}$/;
    if (!phoneRegex.test(phone.replace(/\D/g, ''))) {
        showAlert('Please enter a valid 10-digit phone number', 'error');
        return false;
    }
    
    // Username validation
    if (username.length < 4) {
        showAlert('Username must be at least 4 characters long', 'error');
        return false;
    }
    
    // Password validation
    if (password.length < 6) {
        showAlert('Password must be at least 6 characters long', 'error');
        return false;
    }
    
    // Password match validation
    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'error');
        return false;
    }
    
    return true;
}

function validateLoginForm() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    
    if (!email || !password) {
        showAlert('Please enter both email and password', 'error');
        return false;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showAlert('Please enter a valid email address', 'error');
        return false;
    }
    
    return true;
}

// ============================================================================
// FILE UPLOAD
// ============================================================================

function initFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const uploadForm = document.getElementById('uploadForm');
    
    if (uploadArea && fileInput) {
        // Click to upload
        uploadArea.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.style.borderColor = '#764ba2';
            uploadArea.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%)';
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadArea.style.borderColor = '#667eea';
            uploadArea.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)';
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.style.borderColor = '#667eea';
            uploadArea.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect(files[0]);
            }
        });
        
        // File input change
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }
}

function handleFileSelect(file) {
    const fileName = file.name;
    const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB
    const fileType = file.name.split('.').pop().toLowerCase();
    
    // Validate file type
    if (fileType !== 'csv' && fileType !== 'txt') {
        showAlert('Please upload a CSV or TXT file', 'error');
        return;
    }
    
    // Validate file size (max 16MB)
    if (file.size > 16 * 1024 * 1024) {
        showAlert('File size must be less than 16MB', 'error');
        return;
    }
    
    // Show file info
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.innerHTML = `
        <i class="fas fa-file-check" style="color: #10b981;"></i>
        <h3 style="color: #10b981;">File Selected!</h3>
        <p><strong>${fileName}</strong></p>
        <p>Size: ${fileSize} MB</p>
        <button type="submit" class="btn btn-gradient btn-custom mt-3">
            <i class="fas fa-upload"></i> Upload File
        </button>
    `;
}

// ============================================================================
// MODEL SELECTOR
// ============================================================================

function initModelSelector() {
    const modelButtons = document.querySelectorAll('.model-btn');
    const modelInput = document.getElementById('model_name');
    
    modelButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            modelButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update hidden input
            if (modelInput) {
                modelInput.value = this.dataset.model;
            }
        });
    });
}

// ============================================================================
// PREDICTION FORM
// ============================================================================

function initPredictionForm() {
    const predictionForm = document.getElementById('predictionForm');
    
    if (predictionForm) {
        predictionForm.addEventListener('submit', function(e) {
            // Validate all feature inputs
            const inputs = predictionForm.querySelectorAll('input[type="number"]');
            let allFilled = true;
            
            inputs.forEach(input => {
                if (input.value === '') {
                    allFilled = false;
                    input.style.borderColor = '#ef4444';
                }
            });
            
            if (!allFilled) {
                e.preventDefault();
                showAlert('Please fill all feature values', 'error');
                return false;
            }
            
            // Show loading state
            const submitBtn = predictionForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="spinner"></div> Processing...';
            
            // Re-enable after some time (in case of error)
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }, 5000);
        });
        
        // Clear error styling on input
        const featureInputs = predictionForm.querySelectorAll('input[type="number"]');
        featureInputs.forEach(input => {
            input.addEventListener('input', function() {
                this.style.borderColor = '#e5e7eb';
            });
        });
    }
    
    // Animate progress bars in algorithm page
    animateProgressBars();
}

function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-fill');
    
    progressBars.forEach(bar => {
        const width = bar.dataset.width;
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
}

// ============================================================================
// ALERTS
// ============================================================================

function initAlerts() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            fadeOut(alert);
        }, 5000);
        
        // Add close button if not present
        if (!alert.querySelector('.btn-close')) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'btn-close';
            closeBtn.setAttribute('type', 'button');
            closeBtn.onclick = () => fadeOut(alert);
            alert.appendChild(closeBtn);
        }
    });
}

function showAlert(message, type) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type}`;
    alertContainer.style.position = 'fixed';
    alertContainer.style.top = '20px';
    alertContainer.style.right = '20px';
    alertContainer.style.zIndex = '9999';
    alertContainer.style.minWidth = '300px';
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(alertContainer);
    
    setTimeout(() => {
        fadeOut(alertContainer);
    }, 5000);
}

function fadeOut(element) {
    element.style.opacity = '0';
    element.style.transform = 'translateX(100px)';
    setTimeout(() => {
        element.remove();
    }, 300);
}

// ============================================================================
// TOOLTIPS
// ============================================================================

function initTooltips() {
    // Initialize Bootstrap tooltips if available
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (typeof bootstrap !== 'undefined') {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Smooth scroll to top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard!', 'success');
    }).catch(err => {
        showAlert('Failed to copy', 'error');
    });
}

// Print page
function printPage() {
    window.print();
}

// Download data as CSV
function downloadCSV(data, filename) {
    const blob = new Blob([data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// ============================================================================
// NAVBAR SCROLL EFFECT
// ============================================================================

window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.15)';
            navbar.style.padding = '0.5rem 0';
        } else {
            navbar.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
            navbar.style.padding = '1rem 0';
        }
    }
});

// ============================================================================
// LOADING SCREEN
// ============================================================================

window.addEventListener('load', function() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.style.display = 'none';
        }, 300);
    }
});
