# Modal UI Integration Guide

This document explains how to use the frontend UI to deploy training jobs to Modal.

## Overview

The AI Toolkit UI now includes a **"Deploy to Modal"** feature that allows you to:
1. Create training jobs using the web UI
2. Automatically convert the job config to Modal-compatible format
3. Upload datasets to Modal volumes (optional)
4. Trigger Modal deployment directly from the UI

## How to Use

### Step 1: Start the UI

```bash
cd ai-toolkit-z_image_turbo/ui
npm run build_and_start
```

Access the UI at `http://localhost:8675`

### Step 2: Create a Training Job

1. Click **"New Training Job"** in the UI
2. Fill in all the training parameters:
   - Training name
   - Model selection (Z-Image Turbo recommended)
   - Dataset selection
   - Training parameters (steps, learning rate, etc.)
   - Sample prompts
3. Click **"Create Job"** to save the job

### Step 3: Deploy to Modal

1. Navigate to the job detail page
2. Click the **⚙️ (Settings)** icon in the top bar
3. Select **"Deploy to Modal"** from the dropdown menu
4. Choose your deployment option:
   - **"Deploy with Upload"** (Recommended): Uploads dataset to Modal volume automatically
   - **"Cancel"** (Deploy without Upload): Deploys without uploading dataset (you'll need to upload manually)

### Step 4: Monitor Training

After deployment, you'll see a success message with information about your deployment. The UI will attempt to capture and display the Modal dashboard URL automatically.

**Finding Your Modal URL:**

1. **In the Success Alert** - If captured, the Modal dashboard URL will be displayed directly in the success message. Click the link to open it.

2. **Terminal Output** - Check the terminal where the UI is running. Modal prints the deployment URL when it starts:
   ```
   ✓ Created app.
   → View app at https://modal.com/apps/...
   ```

3. **Modal Dashboard** - Visit [https://modal.com/apps](https://modal.com/apps) to see all your running deployments

4. **CLI Command** - Run this in a terminal to list active apps:
   ```bash
   modal app list
   ```

**Monitoring Your Training:**
- View real-time logs and progress in the Modal dashboard
- Check training outputs saved to Modal volume: `zimage-training-outputs`
- Monitor GPU usage and resource consumption

## What Happens Behind the Scenes

When you click "Deploy to Modal":

1. **Config Conversion**: The UI job config is converted to Modal-compatible YAML format
   - Dataset paths are converted from local paths to Modal paths (`/root/datasets/<dataset_name>`)
   - Training folder is set to `/root/modal_output`
   - All other settings are preserved

2. **Config File Creation**: A new config file is saved at:
   ```
   ai-toolkit-z_image_turbo/config/<job_name>_modal.yaml
   ```

3. **Dataset Upload** (if selected): Dataset is uploaded to Modal volume:
   ```bash
   modal volume upload zimage-datasets <local_path> /root/datasets/<dataset_name>
   ```

4. **Modal Deployment**: Training is started on Modal:
   ```bash
   modal run modal_train_deploy.py config/<job_name>_modal.yaml
   ```
   
5. **URL Capture**: The system attempts to capture the Modal deployment URL from the output and displays it in the success message. If not captured, helpful instructions are provided.

## Prerequisites

Before using this feature, ensure:

1. **Modal is set up**:
   ```bash
   pip install modal
   modal setup
   ```

2. **HuggingFace secret is configured**:
   ```bash
   modal secret create huggingface HF_TOKEN=your_token_here
   ```

3. **Modal volumes exist** (created automatically on first use):
   - `zimage-training-outputs` - For training outputs
   - `zimage-datasets` - For datasets (if using volume upload)
   - `hf-model-cache` - For model caching

## Configuration Details

### Path Conversions

The integration automatically converts paths:

| Local Path | Modal Path |
|-----------|------------|
| `./datasets/my_style` | `/root/datasets/my_style` |
| `C:\datasets\my_style` | `/root/datasets/my_style` |
| Any local dataset path | `/root/datasets/<dataset_name>` |

### Config File Location

Config files are saved to:
```
ai-toolkit-z_image_turbo/config/<job_name>_modal.yaml
```

You can manually edit these files if needed, or use them directly with:
```bash
modal run modal_train_deploy.py config/<job_name>_modal.yaml
```

## Troubleshooting

### Dataset Upload Fails

If dataset upload fails, you can upload manually:
```bash
modal volume upload zimage-datasets ./datasets/my_style /root/datasets/my_style
```

Then deploy without upload option.

### Modal Command Not Found

Ensure Modal is installed and in your PATH:
```bash
which modal
# Should show: /path/to/modal

# If not found, install:
pip install modal
```

### Config File Not Found

The config file is saved relative to `ai-toolkit-z_image_turbo/` directory. If Modal can't find it:
1. Check the file exists: `ls ai-toolkit-z_image_turbo/config/<job_name>_modal.yaml`
2. Use absolute path in Modal command if needed

### Permission Errors

Ensure the UI process has permission to:
- Write to `ai-toolkit-z_image_turbo/config/` directory
- Execute `modal` command
- Access dataset directories

## Manual Deployment

If you prefer to deploy manually:

1. Use the UI to create and configure your job
2. Find the generated config file at: `ai-toolkit-z_image_turbo/config/<job_name>_modal.yaml`
3. Deploy manually:
   ```bash
   modal run modal_train_deploy.py config/<job_name>_modal.yaml
   ```

## Downloading Results

After training completes, download results:

```bash
modal volume download zimage-training-outputs \
  /root/modal_output/<job_name> \
  ./outputs/<job_name>
```

## Next Steps

- Monitor training progress in Modal dashboard
- Download trained LoRAs from Modal volumes
- Use the trained models for inference

---

## Features

### Automatic URL Capture

The integration attempts to automatically capture the Modal deployment URL from the command output and display it in the success message. This makes it easy to jump directly to monitoring your training.

If the URL isn't captured automatically (which can happen due to timing), the UI provides clear instructions on how to find it using the methods listed above.

---

**Last Updated:** 2025-11-30

