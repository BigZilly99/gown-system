/*
University Gown Management System - Main JavaScript
*/

document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initTheme();
    
    // Initialize sidebar toggle
    initSidebar();
    
    // Initialize tooltips
    initTooltips();
    
    // Auto-hide alerts
    initAutoHideAlerts();
});

/* Theme Management */
function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    
    // Check localStorage or system preference
    const savedTheme = localStorage.getItem('theme');
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const currentTheme = savedTheme || systemTheme;
    
    html.setAttribute('data-bs-theme', currentTheme);
    updateThemeIcon(currentTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const current = html.getAttribute('data-bs-theme');
            const newTheme = current === 'dark' ? 'light' : 'dark';
            
            html.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;
    
    const icon = themeToggle.querySelector('i');
    if (theme === 'dark') {
        icon.classList.remove('bi-moon');
        icon.classList.add('bi-sun');
    } else {
        icon.classList.remove('bi-sun');
        icon.classList.add('bi-moon');
    }
}

/* Sidebar Toggle */
function initSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 992) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }
}

/* Tooltips */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/* Auto-hide alerts */
function initAutoHideAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/* Student Search Autocomplete */
async function searchStudents(query) {
    if (query.length < 2) return [];
    
    try {
        const response = await fetch(`/students/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        return data.results || [];
    } catch (error) {
        console.error('Search error:', error);
        return [];
    }
}

/* Gown Lookup */
async function lookupGown(serialNumber) {
    try {
        const response = await fetch(`/gowns/lookup/${encodeURIComponent(serialNumber)}`);
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('Lookup error:', error);
        return null;
    }
}

/* Student Lookup */
async function lookupStudent(indexNumber) {
    try {
        const response = await fetch(`/students/lookup/${encodeURIComponent(indexNumber)}`);
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('Lookup error:', error);
        return null;
    }
}

/* Quick Issue */
async function quickIssue(studentIndex, gownSerial, returnDate) {
    try {
        const formData = new FormData();
        formData.append('student_index', studentIndex);
        formData.append('gown_serial', gownSerial);
        formData.append('return_date', returnDate);
        
        const response = await fetch('/transactions/quick-issue', {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    } catch (error) {
        console.error('Quick issue error:', error);
        return { success: false, error: 'Network error' };
    }
}

/* Quick Return */
async function quickReturn(gownSerial) {
    try {
        const formData = new FormData();
        formData.append('gown_serial', gownSerial);
        
        const response = await fetch('/transactions/quick-return', {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    } catch (error) {
        console.error('Quick return error:', error);
        return { success: false, error: 'Network error' };
    }
}

/* Utility: Format Currency */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/* Utility: Format Date */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/* Export to CSV (Client-side helper) */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // Escape quotes and wrap in quotes
            let data = cols[j].innerText.replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        
        csv.push(row.join(','));
    }
    
    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

/* Confirm Delete */
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

/* Print Receipt */
function printReceipt() {
    window.print();
}

/* Mobile Menu Toggle */
function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('show');
    }
}

// Expose functions globally
window.searchStudents = searchStudents;
window.lookupGown = lookupGown;
window.lookupStudent = lookupStudent;
window.quickIssue = quickIssue;
window.quickReturn = quickReturn;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.exportTableToCSV = exportTableToCSV;
window.confirmDelete = confirmDelete;
window.printReceipt = printReceipt;
window.toggleMobileMenu = toggleMobileMenu;
