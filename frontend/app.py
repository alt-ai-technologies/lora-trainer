#!/usr/bin/env python3
"""
Simple Flask UI for launching Modal LoRA training.
"""

import os
import subprocess
import yaml
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "ai-toolkit-z_image_turbo" / "config"
EXAMPLE_CONFIG = CONFIG_DIR / "examples" / "modal" / "modal_train_lora_zimage_turbo_24gb.yaml"
DATASET_DIR = PROJECT_ROOT / "dataset"
AI_TOOLKIT_DATASET_DIR = PROJECT_ROOT / "ai-toolkit-z_image_turbo" / "datasets"


@app.route('/')
def index():
    """Render the main UI."""
    return render_template('index.html')


@app.route('/api/datasets', methods=['GET'])
def list_datasets():
    """List available datasets."""
    datasets = []
    
    # Check project root dataset directory
    if DATASET_DIR.exists():
        for item in DATASET_DIR.iterdir():
            if item.is_dir():
                datasets.append({
                    'name': item.name,
                    'path': f"/root/datasets/{item.name}",
                    'local_path': str(item)
                })
    
    # Check ai-toolkit-z_image_turbo/datasets directory
    if AI_TOOLKIT_DATASET_DIR.exists():
        for item in AI_TOOLKIT_DATASET_DIR.iterdir():
            if item.is_dir():
                datasets.append({
                    'name': item.name,
                    'path': f"/root/datasets/{item.name}",
                    'local_path': str(item)
                })
    
    return jsonify(datasets)


@app.route('/api/config/create', methods=['POST'])
def create_config():
    """Create a training config file from form data."""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('lora_name'):
            return jsonify({
                'success': False,
                'error': 'LoRA name is required'
            }), 400
        
        if not data.get('dataset_path'):
            return jsonify({
                'success': False,
                'error': 'Dataset path is required'
            }), 400
        
        # Validate training steps
        try:
            steps = int(data.get('steps', 2000))
            if steps < 100 or steps > 10000:
                return jsonify({
                    'success': False,
                    'error': 'Training steps must be between 100 and 10000'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Training steps must be a valid number'
            }), 400
        
        # Validate learning rate
        try:
            lr = float(data.get('learning_rate', 1e-4))
            if lr <= 0 or lr > 1:
                return jsonify({
                    'success': False,
                    'error': 'Learning rate must be between 0 and 1'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Learning rate must be a valid number'
            }), 400
        
        # Read the example config
        with open(EXAMPLE_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update config with user inputs
        config['config']['name'] = data.get('lora_name', 'my_lora_v1')
        config['config']['process'][0]['datasets'][0]['folder_path'] = data.get('dataset_path', '/root/datasets/my_style')
        
        # Update training parameters
        train_config = config['config']['process'][0]['train']
        train_config['steps'] = int(data.get('steps', 2000))
        train_config['lr'] = float(data.get('learning_rate', 1e-4))
        train_config['batch_size'] = int(data.get('batch_size', 1))
        
        # Update save frequency
        if 'save_every' in data:
            config['config']['process'][0]['save']['save_every'] = int(data.get('save_every', 250))
        
        # Update sample frequency
        if 'sample_every' in data:
            config['config']['process'][0]['sample']['sample_every'] = int(data.get('sample_every', 250))
        
        # Optional trigger word
        if data.get('trigger_word'):
            config['config']['process'][0]['trigger_word'] = data.get('trigger_word')
        
        # Save the config file
        config_filename = data.get('config_filename', 'my_training.yaml')
        config_path = CONFIG_DIR / config_filename
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)
        
        return jsonify({
            'success': True,
            'message': f'Config file created: {config_path}',
            'config_path': str(config_path),
            'config_filename': config_filename
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/training/launch', methods=['POST'])
def launch_training():
    """Launch Modal training."""
    try:
        data = request.json
        config_filename = data.get('config_filename', 'my_training.yaml')
        custom_name = data.get('custom_name')
        
        # Find modal command
        import shutil
        modal_cmd = shutil.which('modal')
        if not modal_cmd:
            # Try venv location first (most common)
            venv_modal = PROJECT_ROOT / '.venv' / 'bin' / 'modal'
            if venv_modal.exists():
                modal_cmd = str(venv_modal)
            else:
                # Try common locations
                possible_paths = [
                    os.path.expanduser('~/.local/bin/modal'),
                    '/usr/local/bin/modal',
                    '/usr/bin/modal',
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        modal_cmd = path
                        break
        
        if not modal_cmd:
            return jsonify({
                'success': False,
                'error': 'Modal CLI not found. Please install Modal: pip install modal'
            }), 500
        
        # Build the command
        cmd = [modal_cmd, 'run', 'modal_train_deploy.py', f'config/{config_filename}']
        
        if custom_name:
            cmd.extend(['--name', custom_name])
        
        # Change to project root directory
        os.chdir(PROJECT_ROOT)
        
        # Launch training in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # Try to extract Modal app URL from output (non-blocking)
        modal_url = None
        try:
            # Read initial output to get Modal URL
            import select
            import time
            if select.select([process.stdout], [], [], 0.5)[0]:
                output = process.stdout.read(1000)  # Read first 1000 chars
                # Look for Modal URL pattern
                import re
                url_pattern = r'https://modal\.com/apps/[^\s\)]+'
                match = re.search(url_pattern, output)
                if match:
                    modal_url = match.group(0)
        except:
            pass  # If we can't get URL, that's okay
        
        response_data = {
            'success': True,
            'message': 'Training launched successfully',
            'pid': process.pid,
            'command': ' '.join(cmd)
        }
        
        if modal_url:
            response_data['modal_url'] = modal_url
        
        return jsonify(response_data)
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Launch training error: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500


@app.route('/api/training/status', methods=['GET'])
def training_status():
    """Check Modal training status."""
    try:
        # Check for running Modal processes
        result = subprocess.run(
            ['modal', 'app', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return jsonify({
            'success': True,
            'output': result.stdout,
            'apps_running': 'zimage-turbo-training' in result.stdout
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/validate', methods=['POST'])
def validate():
    """Validate form inputs."""
    try:
        data = request.json
        errors = []
        
        if not data.get('lora_name'):
            errors.append('LoRA name is required')
        
        if not data.get('dataset_path'):
            errors.append('Dataset path is required')
        
        try:
            steps = int(data.get('steps', 2000))
            if steps < 100:
                errors.append('Training steps must be at least 100 (you entered: {})'.format(steps))
            elif steps > 10000:
                errors.append('Training steps must be at most 10000 (you entered: {})'.format(steps))
        except (ValueError, TypeError):
            errors.append('Training steps must be a valid number')
        
        try:
            lr = float(data.get('learning_rate', 1e-4))
            if lr <= 0 or lr > 1:
                errors.append('Learning rate should be between 0 and 1')
        except ValueError:
            errors.append('Learning rate must be a number')
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        })
    
    except Exception as e:
        return jsonify({
            'valid': False,
            'errors': [str(e)]
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

