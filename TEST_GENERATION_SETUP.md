# Image Generation Setup Test Results

## ✅ Tests Completed

### 1. Config File Validation
- ✅ **generate_zimage_simple.yaml**: Valid YAML syntax
- ✅ **generate_zimage.yaml**: Valid YAML syntax (fixed formatting issue)
- ✅ Both configs have correct structure for image generation

### 2. System Environment
- ✅ **PyTorch**: 2.8.0+cu128 installed
- ✅ **CUDA**: Available
- ✅ **GPU**: NVIDIA GeForce RTX 4090 Laptop GPU detected
- ✅ **Model Vault**: Exists at `/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo`
- ✅ **Output Directory**: Created at `ai-toolkit-z_image_turbo/output/gen/`

### 3. AI Toolkit Setup
- ✅ **run.py**: Exists and accessible
- ✅ **Config Loading**: Can import `get_job` function
- ⚠️ **Dependencies**: Need to install AI Toolkit dependencies

### 4. Hugging Face Setup
- ⚠️ **CLI**: Not found or not logged in (needed if using Hub model path)

## 📋 Next Steps to Run Generation

### Step 1: Set Up Python Environment

You have a `.venv` in the project root. Activate it and install dependencies:

```bash
# Activate virtual environment
cd /home/nfmil/projects/image_gen
source .venv/bin/activate

# Or if using the ai-toolkit venv
cd ai-toolkit-z_image_turbo
source venv/bin/activate  # if it exists
```

### Step 2: Install Dependencies

**Option A: Using uv (Recommended - Faster)**
```bash
cd ai-toolkit-z_image_turbo
chmod +x install_with_uv.sh
./install_with_uv.sh
```

**Option B: Using pip**
```bash
cd ai-toolkit-z_image_turbo
pip install -r requirements.txt
```

### Step 3: Login to Hugging Face (if using Hub model)

If you want to use the Hub model path (downloads automatically):
```bash
huggingface-cli login
```

Or use the local model path by uncommenting this line in the config:
```yaml
name_or_path: "/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo"
```

### Step 4: Run Image Generation

**Simple Config:**
```bash
cd ai-toolkit-z_image_turbo
python run.py config/generate_zimage_simple.yaml
```

**Full-Featured Config:**
```bash
cd ai-toolkit-z_image_turbo
python run.py config/generate_zimage.yaml
```

## 📁 Config Files Created

1. **config/generate_zimage_simple.yaml** - Minimal setup, single prompt
2. **config/generate_zimage.yaml** - Full-featured with multiple prompts and options

## 🎯 Expected Output

Images will be saved to:
```
ai-toolkit-z_image_turbo/output/gen/
```

Each image will be named with a timestamp and the prompt (sanitized).

## ⚙️ Configuration Options

### Model Path Options:
- **Hub Path** (default): `"Tongyi-MAI/Z-Image-Turbo"` - Downloads automatically
- **Local Path**: `"/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo"` - Faster, no download

### Generation Settings:
- **Steps**: 8 (optimal for turbo models)
- **Guidance Scale**: 1 (required for flow matching)
- **Size**: 1024x1024 (default, can be changed)
- **Device**: cuda:0 (change to 'cpu' if no GPU)

## 🔧 Troubleshooting

### If you get "ModuleNotFoundError":
- Make sure virtual environment is activated
- Install dependencies: `pip install -r requirements.txt` or use `install_with_uv.sh`

### If you get "Model not found":
- Check model path in config
- If using Hub path, login: `huggingface-cli login`
- If using local path, verify it exists: `ls -la /home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo`

### If you get "Out of memory":
- Enable quantization (already enabled in configs)
- Reduce image size: `width: 512, height: 512`
- Reduce steps: `sample_steps: 4`

### If generation is slow:
- Make sure you're using GPU: `device: cuda:0`
- Check that CUDA is available: `python -c "import torch; print(torch.cuda.is_available())"`

## ✅ Test Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Config Files | ✅ Valid | Both configs are properly formatted |
| YAML Syntax | ✅ Valid | No syntax errors |
| GPU Available | ✅ Yes | RTX 4090 Laptop GPU |
| PyTorch | ✅ Installed | Version 2.8.0+cu128 |
| Model Vault | ✅ Exists | Local model available |
| Output Dir | ✅ Created | Ready for images |
| Dependencies | ⚠️ Need Install | Run install script |
| HF Login | ⚠️ Not Set | Only needed for Hub path |

## 🚀 Ready to Generate!

Once dependencies are installed, you can run:
```bash
cd ai-toolkit-z_image_turbo
python run.py config/generate_zimage_simple.yaml
```

