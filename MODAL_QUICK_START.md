# Modal Quick Start Guide - Z-Image Turbo LoRA Training

## 🚀 Quick Start (5 Minutes)

### Step 1: Setup Secrets

```bash
# Set up Hugging Face token (if not already done)
modal secret create huggingface HF_TOKEN=your_token_here
```

### Step 2: Prepare Your Dataset

Create a folder with images and captions:

```bash
mkdir -p dataset/my_style
# Add images: image1.jpg, image2.jpg, ...
# Add captions: image1.txt, image2.txt, ...
```

**Example structure:**
```
dataset/my_style/
├── image1.jpg
├── image1.txt  # "a photo of a cat"
├── image2.jpg
├── image2.txt  # "a photo of a dog"
└── ...
```

### Step 3: Create Training Config

```bash
# Copy the Modal example config
cp ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml \
   ai-toolkit-z_image_turbo/config/my_training.yaml
```

**Edit the config:**
```yaml
name: "my_style_lora_v1"  # Change this
datasets:
  - folder_path: "/root/datasets/my_style"  # Update this path
```

### Step 4: Run Training

```bash
# Run training on Modal
modal run modal_train_deploy.py config/my_training.yaml
```

**That's it!** Your training will:
- ✅ Download models automatically (first run only, ~5-10 min)
- ✅ Cache models for future runs
- ✅ Train your LoRA
- ✅ Save outputs to Modal volume

---

## 📥 Getting Your Results

### Download Trained LoRA

```bash
# Download the entire training output
modal volume download zimage-training-outputs \
  /root/modal_output/my_style_lora_v1 \
  ./outputs/my_style_lora_v1
```

### View Volume Contents

```bash
# List what's in the volume
modal volume show zimage-training-outputs
```

---

## 🔧 Common Tasks

### Using a Local Dataset (Small Datasets)

1. **Organize dataset locally:**
   ```bash
   dataset/
   └── my_style/
       ├── image1.jpg
       ├── image1.txt
       └── ...
   ```

2. **Update config:**
   ```yaml
   datasets:
     - folder_path: "/root/datasets/my_style"
   ```

3. **Run training** - Modal will mount your local dataset automatically

### Using a Volume Dataset (Large/Reusable Datasets)

1. **Upload dataset to volume:**
   ```bash
   # Create a script to upload (or use Modal CLI)
   modal volume upload zimage-datasets ./dataset/my_style /root/datasets/my_style
   ```

2. **Update config:**
   ```yaml
   datasets:
     - folder_path: "/root/datasets/my_style"
   ```

3. **Run training** - Dataset is already in the volume

### Running Multiple Training Jobs

```bash
# Run multiple configs sequentially
modal run modal_train_deploy.py config/training1.yaml config/training2.yaml

# Continue even if one fails
modal run modal_train_deploy.py config/training1.yaml config/training2.yaml --recover
```

### Monitoring Training

- **Terminal output**: Real-time logs in your terminal
- **Modal Dashboard**: Visit https://modal.com/apps to see running functions
- **Logs**: `modal logs zimage-turbo-training`

---

## ⚙️ Configuration Tips

### Adjust Training Steps

```yaml
train:
  steps: 2000  # 500-4000 is typical range
```

### Adjust Batch Size (if OOM)

```yaml
train:
  batch_size: 1
  gradient_accumulation_steps: 4  # Increase this to simulate larger batch
```

### Enable Low VRAM Mode (if needed)

```yaml
model:
  low_vram: true  # Slower but uses less VRAM
```

### Change Output Name

```yaml
config:
  name: "my_custom_lora_v1"  # This becomes the folder name
```

---

## 💰 Cost Estimates

- **A100 GPU**: ~$1.10/hour
- **2000 steps training**: ~30-60 minutes = **~$0.50-$1.00**
- **First run (with downloads)**: Add ~10 minutes = **~$0.20**
- **Volume storage**: ~$0.10/GB/month

**Total per training run**: ~$0.50-$1.20

---

## 🐛 Troubleshooting

### "Config file not found"

**Solution**: Make sure config path is relative to `ai-toolkit-z_image_turbo/config/` or use absolute path.

### "Dataset not found"

**Solution**: 
- Check dataset path in config matches actual location
- Ensure images and captions exist
- Verify dataset is mounted or in volume

### "Out of memory"

**Solution**:
- Ensure `quantize: true` in config
- Reduce `batch_size` to 1
- Increase `gradient_accumulation_steps`
- Enable `low_vram: true`

### "Models not downloading"

**Solution**:
- Check HF token: `modal secret list`
- Verify token has access to models
- Accept model license on Hugging Face

---

## 📚 Next Steps

- Read [MODAL_DEPLOYMENT_PLAN.md](MODAL_DEPLOYMENT_PLAN.md) for detailed information
- Check [README.md](README.md) for project overview
- See example config: `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml`

---

**Happy Training! 🎨**

