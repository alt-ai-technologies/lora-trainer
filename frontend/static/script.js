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
        
        const validation = await validateResponse.json();
        
        if (!validation.valid) {
            showStatus('Validation errors: ' + validation.errors.join(', '), 'error');
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
        
        const result = await response.json();
        
        if (result.success) {
            configCreated = true;
            document.getElementById('launchBtn').disabled = false;
            showStatus(`✅ ${result.message}`, 'success');
        } else {
            showStatus('❌ Error: ' + result.error, 'error');
        }
    } catch (error) {
        showStatus('❌ Error creating config: ' + error.message, 'error');
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
        showStatus('🚀 Launching training on Modal...', 'info');
        
        const response = await fetch('/api/training/launch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(
                `✅ Training launched successfully! Process ID: ${result.pid}\n` +
                `Command: ${result.command}\n` +
                `Check status at: https://modal.com/apps`,
                'success'
            );
            
            // Disable launch button after successful launch
            document.getElementById('launchBtn').disabled = true;
        } else {
            showStatus('❌ Error launching training: ' + result.error, 'error');
        }
    } catch (error) {
        showStatus('❌ Error launching training: ' + error.message, 'error');
    }
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

