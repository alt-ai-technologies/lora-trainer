// Global state
let configCreated = false;

// Load datasets on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDatasets();
});

// Load available datasets
async function loadDatasets() {
    try {
        const response = await fetch('/api/datasets');
        const datasets = await response.json();
        
        const select = document.getElementById('dataset_select');
        select.innerHTML = '<option value="">Select a dataset...</option>';
        
        datasets.forEach(dataset => {
            const option = document.createElement('option');
            option.value = dataset.path;
            option.textContent = `${dataset.name} (${dataset.path})`;
            option.dataset.localPath = dataset.local_path;
            select.appendChild(option);
        });
        
        showStatus('Datasets loaded successfully', 'success');
    } catch (error) {
        showStatus('Error loading datasets: ' + error.message, 'error');
    }
}

// Update dataset path when selection changes
function updateDatasetPath() {
    const select = document.getElementById('dataset_select');
    const pathInput = document.getElementById('dataset_path');
    
    if (select.value) {
        pathInput.value = select.value;
    }
}

// Validate form and create config
async function validateAndCreateConfig() {
    const form = document.getElementById('trainingForm');
    const formData = new FormData(form);
    
    // Convert FormData to object
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    // Validate
    try {
        const validateResponse = await fetch('/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!validateResponse.ok) {
            const errorText = await validateResponse.text();
            showStatus('❌ Validation request failed: ' + errorText, 'error');
            console.error('Validation request error:', validateResponse.status, errorText);
            return;
        }
        
        const validation = await validateResponse.json();
        console.log('Validation result:', validation);
        
        if (!validation.valid) {
            const errorMsg = validation.errors && validation.errors.length > 0 
                ? validation.errors.join(', ') 
                : 'Validation failed';
            showStatus('❌ Validation errors: ' + errorMsg, 'error');
            return;
        }
    } catch (error) {
        showStatus('Validation error: ' + error.message, 'error');
        return;
    }
    
    // Create config
    try {
        showStatus('Creating config file...', 'info');
        
        const response = await fetch('/api/config/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        // Check if response is ok
        if (!response.ok) {
            let errorText;
            try {
                errorText = await response.text();
            } catch (e) {
                errorText = `HTTP ${response.status} ${response.statusText}`;
            }
            showStatus(`❌ HTTP Error ${response.status}: ${errorText}`, 'error');
            console.error('HTTP Error:', response.status, errorText);
            return;
        }
        
        let result;
        try {
            result = await response.json();
            console.log('Config create response:', result);
        } catch (e) {
            const text = await response.text();
            showStatus(`❌ Invalid JSON response: ${text.substring(0, 100)}`, 'error');
            console.error('JSON parse error:', e, 'Response text:', text);
            return;
        }
        
        if (result.success) {
            configCreated = true;
            document.getElementById('launchBtn').disabled = false;
            showStatus(`✅ ${result.message}`, 'success');
        } else {
            showStatus('❌ Error: ' + (result.error || 'Unknown error'), 'error');
            console.error('Config create error:', result);
        }
    } catch (error) {
        showStatus('❌ Error creating config: ' + error.message, 'error');
        console.error('Exception creating config:', error);
    }
}

// Launch training
async function launchTraining() {
    if (!configCreated) {
        showStatus('Please create the config file first!', 'error');
        return;
    }
    
    const form = document.getElementById('trainingForm');
    const formData = new FormData(form);
    
    const data = {
        config_filename: formData.get('config_filename') || 'my_training.yaml',
        custom_name: formData.get('custom_name') || null
    };
    
    try {
        // Show progress bar
        showProgressBar();
        
        showStatus('🚀 Launching training on Modal...', 'info');
        
        const response = await fetch('/api/training/launch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            hideProgressBar();
            showStatus('❌ HTTP Error: ' + errorText, 'error');
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            // Update progress
            updateProgress(100, 'Training launched successfully!');
            
            // Show success message
            showStatus(
                `✅ Training launched successfully! Process ID: ${result.pid}\n` +
                `Command: ${result.command}`,
                'success'
            );
            
            // Show Modal link if available
            if (result.modal_url) {
                showModalLink(result.modal_url);
            } else {
                // Fallback to general Modal dashboard
                showModalLink('https://modal.com/apps');
            }
            
            // Disable launch button after successful launch
            document.getElementById('launchBtn').disabled = true;
        } else {
            hideProgressBar();
            showStatus('❌ Error launching training: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        hideProgressBar();
        showStatus('❌ Error launching training: ' + error.message, 'error');
        console.error('Launch training error:', error);
    }
}

// Progress bar functions
function showProgressBar() {
    const container = document.getElementById('progressContainer');
    container.style.display = 'block';
    updateProgress(0, 'Launching training...');
}

function hideProgressBar() {
    const container = document.getElementById('progressContainer');
    container.style.display = 'none';
}

function updateProgress(percent, text) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    progressBar.style.width = percent + '%';
    progressText.textContent = text;
}

// Modal link functions
function showModalLink(url) {
    const container = document.getElementById('modalLinkContainer');
    const link = document.getElementById('modalAppLink');
    
    link.href = url;
    container.style.display = 'block';
}

function hideModalLink() {
    const container = document.getElementById('modalLinkContainer');
    container.style.display = 'none';
}

// Show status message
function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 10000);
    }
}

