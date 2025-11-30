# LoRA Training UI

A simple web interface for launching Z-Image Turbo LoRA training on Modal.

## Features

- 🎨 Clean, modern web interface
- 📝 Create training config files from a form
- 🚀 Launch Modal training with one click
- 📂 Automatic dataset detection
- ✅ Form validation
- 📊 Real-time status updates

## Setup

### Install Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

### Run the UI

```bash
python app.py
```

Then open your browser to: `http://localhost:5000`

## Usage

1. **Fill in the form:**
   - LoRA Name: Your model name (e.g., `my_style_lora_v1`)
   - Dataset Path: Select from dropdown or enter manually (must be `/root/datasets/your_dataset`)
   - Training Steps: Number of steps (500-4000 typical)
   - Learning Rate: Default is 0.0001 (1e-4)
   - Other parameters as needed

2. **Create Config:**
   - Click "Create Config File" to generate the YAML config
   - The config will be saved to `ai-toolkit-z_image_turbo/config/`

3. **Launch Training:**
   - Once config is created, click "Launch Training"
   - Training will start on Modal
   - Check status at https://modal.com/apps

## Prerequisites

- Modal CLI installed and authenticated (`modal token new`)
- HuggingFace secret set in Modal (`modal secret create huggingface HF_TOKEN=your_token`)
- Datasets prepared in `dataset/` or `ai-toolkit-z_image_turbo/datasets/`

## API Endpoints

- `GET /api/datasets` - List available datasets
- `POST /api/config/create` - Create training config file
- `POST /api/training/launch` - Launch Modal training
- `GET /api/training/status` - Check training status
- `POST /api/validate` - Validate form inputs

## Notes

- The UI runs locally and launches training via subprocess
- Training runs on Modal's cloud infrastructure
- Config files are saved in `ai-toolkit-z_image_turbo/config/`
- Make sure you're in the project root when running the app

