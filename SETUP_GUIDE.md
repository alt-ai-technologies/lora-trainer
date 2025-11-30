# Complete Setup Guide - Modal Training with AI Toolkit

## 🔐 1. Setting Up Secrets

### HuggingFace Token

The training script needs a HuggingFace token to download models. Set it up in Modal:

```bash
# Create the HuggingFace secret in Modal
modal secret create huggingface HF_TOKEN=your_huggingface_token_here
```

**To get your HuggingFace token:**
1. Go to https://huggingface.co/settings/tokens
2. Create a new token (read access is enough for public models)
3. Copy the token and use it in the command above

**Verify it's set:**
```bash
modal secret list
```

You should see `huggingface` in the list.

---

## 📁 2. Where to Put Training Images

### Dataset Structure

Your training images need to be organized with **images and caption files**:

```
dataset/
└── my_style/              # Your dataset name
    ├── image1.jpg
    ├── image1.txt         # Caption: "a photo of a cat"
    ├── image2.jpg
    ├── image2.txt         # Caption: "a photo of a dog"
    ├── image3.png
    ├── image3.txt         # Caption: "a beautiful sunset"
    └── ...
```

**Requirements:**
- Images: `.jpg`, `.jpeg`, or `.png` only
- Captions: `.txt` files with the **same name** as the image
- Each image must have a corresponding `.txt` file

### Option A: Local Dataset (Small datasets, < 1GB)

1. **Create your dataset locally:**
   ```bash
   mkdir -p dataset/my_style
   # Copy your images and create caption files
   ```

2. **The dataset will be automatically mounted** when you run Modal training

3. **In your config, use:**
   ```yaml
   datasets:
     - folder_path: "/root/datasets/my_style"
   ```

### Option B: Upload to Modal Volume (Large/reusable datasets)

1. **Upload your dataset to Modal volume:**
   ```bash
   # Upload entire dataset folder
   modal volume upload zimage-datasets ./dataset/my_style /root/datasets/my_style
   ```

2. **In your config, use:**
   ```yaml
   datasets:
     - folder_path: "/root/datasets/my_style"
   ```

3. **The dataset is now persistent** and reusable across training runs

---

## 🎨 3. How to Interface with AI Toolkit

### Method 1: Using Config Files (Recommended for Modal)

The AI Toolkit uses YAML configuration files to define training jobs.

#### Step 1: Create a Training Config

```bash
# Copy the example config
cp ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml \
   ai-toolkit-z_image_turbo/config/my_training.yaml
```

#### Step 2: Edit Your Config

Open `ai-toolkit-z_image_turbo/config/my_training.yaml` and update:

```yaml
config:
  name: "my_style_lora_v1"  # Change this to your LoRA name
  
  datasets:
    - folder_path: "/root/datasets/my_style"  # Update to your dataset path
      caption_ext: "txt"
      resolution: [ 512, 768, 1024 ]
  
  train:
    steps: 2000  # Adjust training steps (500-4000 typical)
    batch_size: 1
    lr: 1e-4
```

#### Step 3: Run Training

```bash
# Run a single config
uv run modal run modal_train_deploy.py config/my_training.yaml

# Run multiple configs
uv run modal run modal_train_deploy.py config/training1.yaml config/training2.yaml

# With custom name replacement
uv run modal run modal_train_deploy.py config/my_training.yaml --name custom_name
```

### Method 2: Using the Web UI (Local Development)

The AI Toolkit includes a web UI for easier dataset management and training:

```bash
cd ai-toolkit-z_image_turbo
python run.py
```

Then open your browser to the URL shown (usually `http://localhost:7860`).

**Features:**
- Upload and organize images
- Auto-captioning
- Create training configs visually
- Monitor training progress

**Note:** The UI runs locally. For Modal deployment, use config files (Method 1).

### Method 3: Python API (Advanced)

You can also use the toolkit programmatically:

```python
from toolkit.job import get_job

# Load a config
job = get_job("config/my_training.yaml")

# Run the job
job.run()
```

---

## 📋 Complete Workflow Example

### Step-by-Step: Training Your First LoRA

1. **Set up secrets:**
   ```bash
   modal secret create huggingface HF_TOKEN=your_token_here
   ```

2. **Prepare your dataset:**
   ```bash
   mkdir -p dataset/my_style
   # Add images: image1.jpg, image2.jpg, ...
   # Add captions: image1.txt, image2.txt, ...
   ```

3. **Create training config:**
   ```bash
   cp ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml \
      ai-toolkit-z_image_turbo/config/my_first_lora.yaml
   ```

4. **Edit config** (`ai-toolkit-z_image_turbo/config/my_first_lora.yaml`):
   ```yaml
   config:
     name: "my_first_lora_v1"
     datasets:
       - folder_path: "/root/datasets/my_style"
   ```

5. **Run training:**
   ```bash
   uv run modal run modal_train_deploy.py config/my_first_lora.yaml
   ```

6. **Download results:**
   ```bash
   modal volume download zimage-training-outputs \
     /root/modal_output/my_first_lora_v1 \
     ./outputs/my_first_lora_v1
   ```

---

## 📂 Important Paths

### On Modal (Inside Container)
- **Training outputs**: `/root/modal_output/`
- **Datasets**: `/root/datasets/`
- **Model cache**: `/root/.cache/huggingface/`
- **Config files**: `/root/ai-toolkit-z_image_turbo/config/`

### Locally (Your Machine)
- **Config files**: `ai-toolkit-z_image_turbo/config/`
- **Local datasets**: `dataset/` (create this folder)
- **Downloaded outputs**: `./outputs/` (create this folder)

---

## 🔍 Useful Commands

### Check Modal Secrets
```bash
modal secret list
```

### View Volume Contents
```bash
modal volume show zimage-training-outputs
modal volume show zimage-datasets
modal volume show hf-model-cache
```

### Download Training Results
```bash
modal volume download zimage-training-outputs /root/modal_output/my_lora_v1 ./outputs/
```

### Upload Dataset to Volume
```bash
modal volume upload zimage-datasets ./dataset/my_style /root/datasets/my_style
```

### View Training Logs
```bash
modal logs zimage-turbo-training
```

---

## 💡 Tips

1. **Start Small**: Test with 10-20 images first to verify everything works
2. **Good Captions**: Write descriptive captions for better results
3. **Resolution**: Z-Image Turbo supports multiple resolutions (512, 768, 1024)
4. **Training Steps**: 500-4000 is typical. Start with 2000 and adjust
5. **Model Caching**: First run downloads models (~5-10 min). Subsequent runs are much faster!

---

## 🆘 Need Help?

- Check `MODAL_QUICK_START.md` for quick reference
- See `MODAL_DEPLOYMENT_PLAN.md` for detailed information
- Example config: `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml`

