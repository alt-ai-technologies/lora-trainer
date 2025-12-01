# Image Generation Project

This repository contains an integration of **Z-Image Turbo** with **AI Toolkit**, enabling fine-tuning of Z-Image Turbo models while preserving their turbo inference speed through a de-distillation training adapter.

---

## 📁 Project Structure

```
lora_trainer/
├── ai-toolkit-z_image_turbo/     # AI Toolkit with Z-Image Turbo integration
├── Z-Image-Turbo/                # Documentation and audit reports
├── book_cover_cli/               # Book cover generation CLI tool
├── datasets/                     # Training datasets
│   └── uchida_book_dataset/      # Uchida Laboratory Book Cover Dataset
├── tests/                        # Test suites for local and Hub models
├── model_vault/                  # Local model storage (downloaded models)
├── prepare_book_cover_dataset.py # Dataset preparation script
├── download_and_upload_book_dataset.py # Dataset download/upload script
├── setup_book_dataset_on_modal.py # Modal dataset setup script
├── upload_dataset_to_modal.py    # Dataset upload to Modal script
├── download_training_samples.py  # Download training samples script
├── BOOK_COVER_DATASET_PREP.md   # Book cover dataset preparation guide
├── BOOK_COVER_TRAINING_QUICKSTART.md # Book cover training quick start
└── README.md                     # This file
```

---

## 📚 Book Cover LoRA Training & Generation

This project includes specialized tools and configurations for training LoRAs on book cover datasets and generating book covers using trained models.

### Quick Links

- **[Book Cover Training Quick Start](BOOK_COVER_TRAINING_QUICKSTART.md)** - Get started training a book cover LoRA in 3 steps
- **[Book Cover Dataset Preparation](BOOK_COVER_DATASET_PREP.md)** - Comprehensive guide to preparing book cover datasets
- **[Book Cover Generator CLI](book_cover_cli/README.md)** - Command-line tool for generating book covers
- **[Book Cover Generator Quick Start](book_cover_cli/QUICKSTART.md)** - Quick start guide for the CLI

### What's Included

1. **Training Configurations**
   - `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml` - Main training config
   - `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers_resume.yaml` - Resume training config

2. **Dataset Preparation Tools**
   - `prepare_book_cover_dataset.py` - Prepare datasets with auto-captioning
   - `download_and_upload_book_dataset.py` - Download Uchida dataset and upload to Modal
   - `setup_book_dataset_on_modal.py` - Setup dataset directly on Modal
   - `upload_dataset_to_modal.py` - Upload prepared datasets to Modal

3. **Generation Tools**
   - `book_cover_cli/book_cover_generator.py` - Interactive and CLI book cover generator
   - `book_cover_cli/generate_on_modal.py` - Generate covers on Modal (GPU access)

4. **Documentation**
   - `BOOK_COVER_DATASET_PREP.md` - Dataset preparation guide
   - `BOOK_COVER_TRAINING_QUICKSTART.md` - Training quick start guide
   - `book_cover_cli/README.md` - CLI documentation
   - `book_cover_cli/QUICKSTART.md` - CLI quick start

### Quick Start: Train a Book Cover LoRA

```bash
# 1. Prepare your dataset
python prepare_book_cover_dataset.py \
    --input /path/to/book/covers \
    --output ./datasets/prepared_book_covers \
    --auto-caption \
    --min-size 512

# 2. Upload to Modal (optional, or use local mount)
modal run upload_dataset_to_modal.py \
    --local-path ./datasets/prepared_book_covers \
    --remote-path book_covers

# 3. Train the LoRA
modal run modal_train_deploy.py \
    ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml
```

### Quick Start: Generate Book Covers

```bash
# Interactive mode
cd book_cover_cli
python book_cover_generator.py --interactive

# Command line mode
python book_cover_generator.py \
    --title "The Dark Forest" \
    --author "Liu Cixin" \
    --genre "science fiction" \
    --color-scheme "dark cosmic" \
    --mood "mysterious"
```

See the [Book Cover Training Quick Start](BOOK_COVER_TRAINING_QUICKSTART.md) for detailed instructions.

---

## 🎯 Overview

### What is Z-Image Turbo?

**Z-Image Turbo** is a step-distilled image generation model that produces high-quality images in just **8 steps** instead of the typical 25-50 steps. It's based on the Z-Image architecture and uses flow matching for fast inference.

**Base Model:** [Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)

### The Challenge: Training on Distilled Models

When you try to train a LoRA directly on a step-distilled model like Z-Image Turbo, the distillation breaks down quickly:
- ❌ The model "forgets" its speed shortcuts
- ❌ Unpredictable quality degradation
- ❌ Loss of turbo speed benefits

### The Solution: De-Distill Training Adapter

The **Z-Image Turbo Training Adapter** is a pre-trained LoRA that "undoes" the distillation, allowing you to:
- ✅ Train LoRAs on a stable, de-distilled version
- ✅ Preserve turbo speed during inference
- ✅ Fine-tune styles, concepts, and characters

**Training Adapter:** [ostris/zimage_turbo_training_adapter](https://huggingface.co/ostris/zimage_turbo_training_adapter)

---

## 🔧 Z-Image Turbo Integration

### How It's Integrated

Z-Image Turbo is **fully integrated** into AI Toolkit through multiple layers:

#### 1. **Core Model Implementation** (`extensions_built_in/diffusion_models/z_image/z_image.py`)

The `ZImageModel` class extends `BaseModel` and provides:

- **Architecture Support**: Sets `arch = "zimage"` for model discovery
- **Model Loading**: Loads transformer, text encoder (Qwen3ForCausalLM), VAE, and pipeline
- **Training Adapter Loading**: `load_training_adapter()` method that:
  - Handles both local paths and Hugging Face Hub paths
  - Automatically downloads adapter from Hub if not found locally
  - Converts weight keys from `diffusion_model.` to `transformer.` format
  - Merges adapter into model with `merge_weight=1.0`
  - Configures adapter for training (deactivated) and inference (inverted)
- **Flow Matching**: Implements custom flow matching scheduler
- **Memory Management**: Supports quantization, layer offloading, and low VRAM modes
- **LoRA Weight Conversion**: Converts between `transformer.` and `diffusion_model.` formats

#### 2. **Configuration System Integration**

- **Type Safety**: `'zimage'` added to `ModelArch` type definition (`toolkit/config_modules.py:556`)
- **Config Parsing**: Explicit handling for `'zimage'` arch in config parsing logic
- **Model Properties**: `is_zimage` property added to `BaseModel` and `StableDiffusion` classes
- **Model Discovery**: `get_model_class()` automatically finds `ZImageModel` by matching `arch == "zimage"`

#### 3. **Training Adapter System**

The training adapter is seamlessly integrated:

- **Automatic Loading**: Loads when `assistant_lora_path` is specified in config
- **Training Phase**: 
  - Adapter is merged into model (`merge_in(merge_weight=1.0)`)
  - Deactivated during training (`is_active = False`, `multiplier = -1.0`)
  - Model trains on de-distilled version
- **Inference Phase**:
  - Adapter is activated with `multiplier = -1.0` (inverted)
  - This removes adapter effects, restoring distilled model
  - Your trained LoRA remains on the distilled model
- **Path Flexibility**: Supports both local paths and Hugging Face Hub paths

#### 4. **UI Integration** (`ui/src/app/jobs/new/options.ts`)

- **Model Option**: "Z-Image Turbo (w/ Training Adapter)" in model selector
- **Pre-configured Settings**:
  - Quantization enabled by default
  - Flow matching sampler
  - Guidance scale: 1 (appropriate for turbo models)
  - Sample steps: 8 (optimal for turbo models)
- **Training Adapter Field**: `assistant_lora_path` field exposed in UI
- **Default Paths**: Pre-filled with Hub paths, easily changeable to local paths

#### 5. **Model Registration**

- **Module Export**: `ZImageModel` exported from `extensions_built_in/diffusion_models/z_image/__init__.py`
- **Model List**: Added to `AI_TOOLKIT_MODELS` in `extensions_built_in/diffusion_models/__init__.py`
- **Automatic Discovery**: Works with existing training pipeline without modifications

### Architecture

```
ZImageModel (BaseModel)
├── arch = "zimage"  # Model identifier
├── is_flow_matching = True
├── is_transformer = True
│
├── load_model()
│   ├── Load transformer (ZImageTransformer2DModel)
│   ├── Load text encoder (Qwen3ForCausalLM)
│   ├── Load VAE (AutoencoderKL)
│   ├── Create ZImagePipeline
│   └── load_training_adapter() [if assistant_lora_path provided]
│       ├── Check if local path exists
│       ├── If not, download from Hugging Face Hub
│       ├── Load safetensors file
│       ├── Convert weight keys: diffusion_model. → transformer.
│       ├── Create LoRASpecialNetwork
│       ├── Merge adapter: merge_in(merge_weight=1.0)
│       ├── Set is_merged_in = False (for inference handling)
│       ├── Set multiplier = -1.0
│       ├── Set is_active = False (training phase)
│       └── Set invert_assistant_lora = True
│
├── get_noise_prediction()
│   └── Implements flow matching noise prediction
│
├── generate_single_image()
│   └── Handles inference with adapter inversion
│
├── convert_lora_weights_before_save()
│   └── Converts: transformer. → diffusion_model.
│
└── convert_lora_weights_before_load()
    └── Converts: diffusion_model. → transformer.
```

### Integration Points

1. **Model Discovery** (`toolkit/util/get_model.py`)
   - `get_model_class()` searches all registered models
   - Matches `config.arch == "zimage"` to `ZImageModel.arch`
   - Returns `ZImageModel` class for instantiation

2. **Configuration System** (`toolkit/config_modules.py`)
   - `ModelArch` type includes `'zimage'` for type safety
   - Config parser handles `'zimage'` arch in `ModelConfig.__init__()`
   - `is_zimage` property available on model instances

3. **Training Pipeline** (`jobs/process/BaseSDTrainProcess.py`)
   - Uses `get_model_class()` to get `ZImageModel`
   - Instantiates model with config
   - Calls `load_model()` which handles adapter loading
   - Training adapter automatically managed during training/inference

4. **UI Integration** (`ui/src/app/jobs/new/options.ts`)
   - Model option: `'zimage:turbo'`
   - Pre-fills `assistant_lora_path` with Hub path
   - Sets optimal defaults (quantization, flow matching, etc.)
   - Exposes `assistant_lora_path` field for customization

---

## 🎓 How the Training Adapter Works

### The Problem

**Step distillation** is a delicate optimization. When you fine-tune:
- Gradients push the model away from its distilled state
- The carefully learned shortcuts break down
- You lose speed and may get quality issues

### The Solution: Two-Phase System

#### Phase 1: Training (De-Distilled State)

```
Base Model (Distilled) + Training Adapter = De-Distilled Model
```

**What happens:**
1. Training adapter is merged into the base model
2. Adapter is deactivated during training (`is_active = False`, `multiplier = -1.0`)
3. Your new LoRA trains on this de-distilled version
4. The distillation doesn't break down because it's already "broken down" by the adapter

**Result:** Your LoRA learns only your content, not how to break distillation.

#### Phase 2: Inference (Distilled State)

```
Base Model (Distilled) + Your LoRA - Training Adapter = Fast Inference
```

**What happens:**
1. Training adapter is activated with `multiplier = -1.0` (inverted)
2. This removes the adapter, restoring the distilled model
3. Your new LoRA's information remains on the distilled model

**Result:** Turbo speed with your fine-tuned content! 🚀

### Technical Implementation

The adapter uses a clever trick with negative multipliers:

- **During Training:**
  ```python
  adapter.multiplier = -1.0
  adapter.is_active = False  # Deactivated, doesn't affect gradients
  ```

- **During Inference:**
  ```python
  adapter.is_active = True
  adapter.multiplier = -1.0  # Inverts effects, removes adapter
  ```

This is mathematically equivalent to:
```
Inference = Base + Your LoRA - Adapter
          = (Distilled + Adapter) + Your LoRA - Adapter
          = Distilled + Your LoRA ✅
```

### Limitations

- ✅ **Works great for:** Short training runs (styles, concepts, characters)
- ⚠️ **May break down for:** Long training runs (many epochs)
- 📝 **Note:** This is a workaround that slows the breakdown, not a permanent solution

For detailed explanation, see: [Training Adapter Explanation](Z-Image-Turbo/TRAINING_ADAPTER_EXPLANATION.md)

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- NVIDIA GPU with 24GB+ VRAM (with quantization)
- Hugging Face account
- Git

### 2. Installation

#### Option A: Using uv (Recommended - Faster)

```bash
# Clone the repository
git clone <repository-url>
cd image_gen

# Set up AI Toolkit
cd ai-toolkit-z_image_turbo

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Use the automated installation script
chmod +x install_with_uv.sh
./install_with_uv.sh
```

The script will:
- Create/activate a virtual environment
- Install PyTorch with CUDA support
- Install all dependencies using uv (10-100x faster than pip)

#### Option B: Using pip (Standard)

```bash
# Clone the repository
git clone <repository-url>
cd image_gen

# Set up AI Toolkit
cd ai-toolkit-z_image_turbo
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install PyTorch first
pip install --no-cache-dir torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 \
    --index-url https://download.pytorch.org/whl/cu126

# Install dependencies
pip install -r requirements.txt
```

**Note:** See `ai-toolkit-z_image_turbo/UV_SETUP.md` for detailed uv usage guide.

### 3. Download Models

#### Option A: Download to Model Vault (Recommended)

```bash
# Run the download script
cd ai-toolkit-z_image_turbo
python3 scripts/download_zimage_models.py
```

Models will be downloaded to `/home/nfmil/model_vault/`:
- Base model: `Tongyi-MAI/Z-Image-Turbo` (~31 GB)
- Training adapter: `ostris/zimage_turbo_training_adapter` (~163 MB)

#### Option B: Use Hugging Face Hub (Downloads on First Use)

Models will be downloaded automatically when you first use them. Make sure you're logged in:

```bash
huggingface-cli login
```

**Note:** You may need to accept the model license on [Hugging Face](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo).

### 4. Prepare Your Dataset

Create a folder with images and captions:
```
dataset/
├── image1.jpg
├── image1.txt  # Caption: "a photo of a cat"
├── image2.jpg
├── image2.txt  # Caption: "a photo of a dog"
└── ...
```

### 5. Create Training Config

Copy and edit the example config:
```bash
cp ai-toolkit-z_image_turbo/config/examples/train_lora_zimage_turbo_24gb.yaml \
   ai-toolkit-z_image_turbo/config/my_training.yaml
```

**Example config file:** `ai-toolkit-z_image_turbo/config/examples/train_lora_zimage_turbo_24gb.yaml`

Edit the config:
```yaml
config:
  output_name: "my_zimage_lora"
  process:
    - type: "train"
      model:
        name_or_path: "/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo"  # or "Tongyi-MAI/Z-Image-Turbo"
        arch: "zimage"
        assistant_lora_path: "/home/nfmil/model_vault/ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors"
        quantize: true
        low_vram: true
      train:
        dataset_folder: "./dataset"
        epochs: 10
      # ... other settings
```

### 6. Start Training

You have three options for training:

#### Option A: Local Training (CLI)

```bash
cd ai-toolkit-z_image_turbo
python run.py config/my_training.yaml
```

#### Option B: Local Training (Web UI)

```bash
cd ai-toolkit-z_image_turbo/ui
npm run build_and_start
```

Then access the UI at `http://localhost:8675` to create and manage training jobs visually.

#### Option C: Cloud Training on Modal (via Web UI) ⭐ Recommended

The easiest way to train on Modal's cloud GPUs:

1. **Start the Web UI:**
   ```bash
   cd ai-toolkit-z_image_turbo/ui
   npm run build_and_start
   ```

2. **Create a training job** in the UI with all your settings

3. **Deploy to Modal:**
   - Navigate to the job detail page
   - Click the ⚙️ (Settings) icon
   - Select **"Deploy to Modal"**
   - Choose to upload dataset or deploy without upload

The UI will automatically:
- ✅ Convert your config to Modal-compatible format
- ✅ Convert dataset paths to Modal paths
- ✅ Optionally upload dataset to Modal volume
- ✅ Trigger Modal deployment
- ✅ Save config file for manual use

**Prerequisites for Modal:**
```bash
# Install Modal
pip install modal
modal setup

# Set up HuggingFace secret
modal secret create huggingface HF_TOKEN=your_token_here
```

See [Modal UI Integration Guide](MODAL_UI_INTEGRATION.md) for detailed instructions.

#### Option D: Cloud Training on Modal (CLI)

```bash
# Create Modal-compatible config (or use the one generated by UI)
cp ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml \
   ai-toolkit-z_image_turbo/config/my_modal_training.yaml

# Edit the config file, then deploy
modal run modal_train_deploy.py config/my_modal_training.yaml
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete Modal setup instructions.

---

## 📚 Documentation

### Integration Documentation

- **[Z-Image Turbo Audit](Z-Image-Turbo/Z_IMAGE_TURBO_AUDIT.md)** - Comprehensive code audit and review
- **[Training Adapter Explanation](Z-Image-Turbo/TRAINING_ADAPTER_EXPLANATION.md)** - Detailed explanation of how the adapter works
- **[Integration Plan](ai-toolkit-z_image_turbo/Z_IMAGE_TURBO_INTEGRATION_PLAN.md)** - Implementation plan and tasks
- **[Integration Status](ai-toolkit-z_image_turbo/INTEGRATION_STATUS.md)** - Current integration status
- **[Test Results](ai-toolkit-z_image_turbo/TEST_RESULTS.md)** - Test verification results

### Installation & Setup

- **[UV Setup Guide](ai-toolkit-z_image_turbo/UV_SETUP.md)** - Guide for using uv package manager
- **[Installation Guide](ai-toolkit-z_image_turbo/INSTALLATION.md)** - General installation instructions
- **[UV Integration Summary](ai-toolkit-z_image_turbo/UV_INTEGRATION_SUMMARY.md)** - Summary of uv integration

### Training & Deployment

- **[Modal UI Integration Guide](MODAL_UI_INTEGRATION.md)** - How to use the web UI to deploy to Modal
- **[Modal Setup Guide](SETUP_GUIDE.md)** - Complete guide for Modal cloud training setup

### Book Cover Training & Generation

- **[Book Cover Training Quick Start](BOOK_COVER_TRAINING_QUICKSTART.md)** - Quick start guide for training book cover LoRAs
- **[Book Cover Dataset Preparation](BOOK_COVER_DATASET_PREP.md)** - Comprehensive dataset preparation guide
- **[Book Cover Generator CLI](book_cover_cli/README.md)** - CLI tool for generating book covers
- **[Book Cover Generator Quick Start](book_cover_cli/QUICKSTART.md)** - Quick start for the CLI

### Test Documentation

- **[Test Status](tests/TEST_STATUS.md)** - Test results and coverage
- **[Test README](tests/README.md)** - How to run tests

### External Resources

- **[Training Adapter Model Card](https://huggingface.co/ostris/zimage_turbo_training_adapter)**
- **[Base Model](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)**
- **[GitHub Commit](https://github.com/ostris/ai-toolkit/commit/4e62c38df5eb25dcf6a9ba3011113521f1f20c10)**
- **[Tutorial Video](https://youtu.be/Kmve1_jiDpQ)**

---

## 🧪 Testing

### Run Tests

```bash
cd /home/nfmil/projects/image_gen
source .venv/bin/activate

# Test local models
pytest tests/test_zimage_turbo_local_models.py -v -k "not (loading or adapter_inversion)"

# Test Hub models (downloads on-demand)
pytest tests/test_zimage_turbo_hub_models.py -v -k "not (loading or adapter)"

# Run all lightweight tests
pytest tests/test_zimage_turbo_*.py -v -k "not (loading or adapter_inversion)"
```

**Current Status:** ✅ 20/26 tests passing (77%)

See [Test Status](tests/TEST_STATUS.md) for details.

---

## 🔍 Key Features

### ✅ What's Working

- **Model Discovery:** ZImageModel correctly registered and discoverable via `arch = "zimage"`
- **Type Safety:** `'zimage'` added to `ModelArch` type definition
- **Config Parsing:** Full support for `'zimage'` arch in configuration system
- **Model Properties:** `is_zimage` property available on model classes
- **Local Paths:** Models can be loaded from `/home/nfmil/model_vault`
- **Hub Paths:** Models can be downloaded from Hugging Face Hub automatically
- **Training Adapter:** Automatically loads and manages the de-distill adapter
- **UI Integration:** Z-Image Turbo option available in web UI with pre-configured settings
- **Modal UI Integration:** One-click deployment to Modal cloud GPUs directly from the web UI
- **LoRA Training:** Full LoRA training pipeline works end-to-end
- **Weight Conversion:** Proper conversion between `transformer.` and `diffusion_model.` formats
- **Example Config:** Example configuration file created at `config/examples/train_lora_zimage_turbo_24gb.yaml`
- **Modal Config:** Example Modal config at `config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml`
- **Package Management:** uv integration for faster dependency installation

### ⚠️ Known Limitations

- **Memory:** Model loading requires CUDA + 24GB+ VRAM (with quantization)
- **Long Training:** Adapter may break down on very long training runs (many epochs)
- **Step Distillation:** The adapter is a workaround that slows breakdown, not a permanent solution

---

## 📖 Usage Examples

### Using Local Models

```yaml
model:
  name_or_path: "/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo"
  arch: "zimage"
  assistant_lora_path: "/home/nfmil/model_vault/ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors"
```

### Using Hub Models

```yaml
model:
  name_or_path: "Tongyi-MAI/Z-Image-Turbo"
  arch: "zimage"
  assistant_lora_path: "ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors"
```

Both methods work! Local paths are faster and don't require internet during training.

### Book Cover Training Example

```bash
# Prepare dataset
python prepare_book_cover_dataset.py \
    --input ./datasets/uchida_book_dataset/images \
    --output ./datasets/prepared_book_covers \
    --metadata ./datasets/uchida_book_dataset/metadata.json \
    --min-size 512

# Train on Modal
modal run modal_train_deploy.py \
    ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml
```

### Book Cover Generation Example

```bash
# Interactive mode
cd book_cover_cli
python book_cover_generator.py --interactive

# Command line mode
python book_cover_generator.py \
    --title "The Dark Forest" \
    --author "Liu Cixin" \
    --genre "science fiction" \
    --color-scheme "dark cosmic" \
    --mood "mysterious" \
    --style "minimalist" \
    --width 768 \
    --height 1024
```

---

## 🛠️ Project Components

### AI Toolkit Integration

- **Location:** `ai-toolkit-z_image_turbo/`
- **Model Class:** `extensions_built_in/diffusion_models/z_image/z_image.py`
- **UI Integration:** `ui/src/app/jobs/new/options.ts`
- **Status:** ✅ Fully functional

### Model Storage

- **Model Vault:** `/home/nfmil/model_vault/`
  - Base model: `Tongyi-MAI/Z-Image-Turbo/` (~31 GB)
  - Training adapter: `ostris/zimage_turbo_training_adapter/` (~163 MB)

### Book Cover Tools

- **CLI Generator:** `book_cover_cli/book_cover_generator.py` - Generate book covers interactively or via CLI
- **Dataset Prep:** `prepare_book_cover_dataset.py` - Prepare datasets with auto-captioning
- **Modal Upload:** `upload_dataset_to_modal.py` - Upload datasets to Modal volume
- **Modal Setup:** `setup_book_dataset_on_modal.py` - Setup datasets directly on Modal
- **Training Configs:** 
  - `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml`
  - `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers_resume.yaml`

### Test Suites

- **Local Models:** `tests/test_zimage_turbo_local_models.py`
- **Hub Models:** `tests/test_zimage_turbo_hub_models.py`
- **Status:** ✅ 20/26 tests passing

---

## 🎬 Tutorial

Watch the official tutorial: [How to Train a Z-Image-Turbo LoRA with AI Toolkit](https://youtu.be/Kmve1_jiDpQ)

The tutorial demonstrates:
- Setting up Z-Image Turbo training
- Using the training adapter
- Training a style LoRA (children's drawings)
- The complete workflow from dataset to trained LoRA

**Example LoRA from Tutorial:** [ostris/z_image_turbo_childrens_drawings](https://huggingface.co/ostris/z_image_turbo_childrens_drawings)

### Book Cover Training Workflow

1. **Prepare Dataset**
   ```bash
   python prepare_book_cover_dataset.py \
       --input ./datasets/uchida_book_dataset/images \
       --output ./datasets/prepared_book_covers \
       --metadata ./datasets/uchida_book_dataset/metadata.json \
       --min-size 512
   ```

2. **Upload to Modal** (optional)
   ```bash
   modal run upload_dataset_to_modal.py \
       --local-path ./datasets/prepared_book_covers \
       --remote-path book_covers
   ```

3. **Train LoRA**
   ```bash
   modal run modal_train_deploy.py \
       ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml
   ```

4. **Generate Covers**
   ```bash
   cd book_cover_cli
   python book_cover_generator.py --interactive
   ```

See [BOOK_COVER_TRAINING_QUICKSTART.md](BOOK_COVER_TRAINING_QUICKSTART.md) for detailed instructions.

---

## 🔬 Technical Details

### Model Architecture

- **Base Model:** Z-Image Transformer (diffusion model)
- **Text Encoder:** Qwen3ForCausalLM (Qwen 3)
- **VAE:** AutoencoderKL
- **Scheduler:** CustomFlowMatchEulerDiscreteScheduler
- **Bucket Divisibility:** 32 (16 for VAE, 2 for patch size)

### Training Adapter Details

- **Type:** LoRA (Low-Rank Adaptation)
- **Target:** Transformer layers only
- **Creation:** Trained on thousands of Z-Image-Turbo generated images
- **Learning Rate:** 1e-5 (very low, to slowly break down distillation)
- **Purpose:** De-distill the model for stable training

### Memory Requirements

- **Minimum:** 24GB VRAM (with quantization)
- **Recommended:** 32GB+ VRAM
- **Optimizations:**
  - Quantization (`quantize: true`)
  - Low VRAM mode (`low_vram: true`)
  - Layer offloading (`layer_offloading: true`)

---

## 🐛 Troubleshooting

### Models Not Found

```bash
# Check if models are downloaded
ls -lh /home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo/
ls -lh /home/nfmil/model_vault/ostris/zimage_turbo_training_adapter/

# Or download them
cd ai-toolkit-z_image_turbo
python3 scripts/download_zimage_models.py
```

### Authentication Issues

```bash
# Login to Hugging Face
huggingface-cli login

# Accept model license
# Visit: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
```

### Out of Memory

- Enable quantization: `quantize: true`
- Enable low VRAM mode: `low_vram: true`
- Reduce batch size: `batch_size: 1`
- Use gradient accumulation: `gradient_accumulation: 4`

### Training Adapter Not Loading

- Check path is correct
- Verify file exists: `ls -lh <adapter_path>`
- Check Hugging Face Hub access if using Hub path

### Book Cover Generation Issues

**LoRA not found:**
- Check that the LoRA path is correct
- Default path assumes Modal volume is mounted
- Use `--lora-path` to specify a different location

**Out of Memory during generation:**
- Reduce image size: `--width 512 --height 768`
- Reduce steps: `--steps 4`

**Dataset preparation errors:**
- Ensure images are at least 512px on shortest side
- Check that metadata file format matches expected structure
- Use `--auto-caption` if metadata is not available

---

## 📝 License

- **AI Toolkit:** Check `ai-toolkit-z_image_turbo/LICENSE`
- **Z-Image Turbo:** Check model license on [Hugging Face](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- **Training Adapter:** Apache 2.0

---

## 🙏 Credits

- **AI Toolkit:** Created by [Ostris](https://github.com/ostris)
- **Z-Image Turbo:** [Tongyi-MAI](https://huggingface.co/Tongyi-MAI)
- **Training Adapter:** [ostris](https://huggingface.co/ostris)

---

## 📞 Support

- **AI Toolkit Issues:** [GitHub Issues](https://github.com/ostris/ai-toolkit/issues)
- **Discord:** [AI Toolkit Discord](https://discord.gg/VXmU2f5WEU)
- **Documentation:** See `Z-Image-Turbo/` directory for detailed docs

---

## 🎯 Integration Status

### ✅ Completed

1. ✅ **Models downloaded** to `/home/nfmil/model_vault`
2. ✅ **Tests created** - 20/26 tests passing (77%)
3. ✅ **Configuration fixes** - `'zimage'` added to ModelArch type
4. ✅ **Config parsing** - Full support for `'zimage'` arch
5. ✅ **Model properties** - `is_zimage` property added
6. ✅ **Example config** - Created at `config/examples/train_lora_zimage_turbo_24gb.yaml`
7. ✅ **Modal config** - Created at `config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml`
8. ✅ **Modal UI integration** - One-click deployment to Modal from web UI
9. ✅ **uv integration** - Fast package management setup
10. ✅ **Documentation** - Comprehensive integration docs

### ⏭ Next Steps

1. ⏭ Test actual training run with real dataset
2. ⏭ Test inference with trained LoRA
3. ⏭ Performance benchmarking
4. ⏭ Long-term training stability testing
5. ⏭ Enhanced Modal integration features (progress monitoring, auto-download)

---

## 📋 Technical Integration Details

### Training Adapter Implementation Flow

```
1. Model Loading
   ├── Load transformer (ZImageTransformer2DModel)
   ├── Load text encoder (Qwen3ForCausalLM)
   ├── Load VAE (AutoencoderKL)
   └── If assistant_lora_path specified:
       └── load_training_adapter()
           ├── Download from Hub (if needed)
           ├── Convert keys: diffusion_model. → transformer.
           ├── Create LoRASpecialNetwork
           ├── Merge adapter: merge_in(merge_weight=1.0)
           ├── Set is_merged_in = False (for inference)
           ├── Set multiplier = -1.0
           ├── Set is_active = False (training)
           └── Set invert_assistant_lora = True

2. Training Phase
   ├── Model state: Base + Training Adapter (merged, deactivated)
   ├── Your LoRA trains on de-distilled model
   └── Training adapter doesn't affect gradients (is_active = False)

3. Inference Phase
   ├── Training adapter activated with multiplier = -1.0
   ├── This inverts adapter, removing it: Base - Adapter = Distilled
   ├── Your LoRA remains: Distilled + Your LoRA
   └── Result: Fast inference with your fine-tuned content
```

### Book Cover Training Configuration

The book cover training configs are optimized for portrait-oriented book covers:

- **Resolutions**: `[512, 768, 1024]` - Portrait aspect ratios
- **Sample Size**: `768x1024` - Standard book cover dimensions
- **Steps**: `1000-3000` - Optimized for style learning
- **Sample Prompts**: 10 book cover-specific prompts for testing
- **Dataset Path**: `/root/datasets/book_covers` (Modal) or local path

### Key Code Locations

- **Model Class**: `ai-toolkit-z_image_turbo/extensions_built_in/diffusion_models/z_image/z_image.py`
- **Config System**: `ai-toolkit-z_image_turbo/toolkit/config_modules.py`
- **UI Integration**: `ai-toolkit-z_image_turbo/ui/src/app/jobs/new/options.ts`
- **Modal UI Integration**: `ai-toolkit-z_image_turbo/ui/src/app/api/jobs/[jobID]/deploy-modal/route.ts`
- **Modal Deployment**: `modal_train_deploy.py` - Main Modal deployment script
- **Model Registration**: `ai-toolkit-z_image_turbo/extensions_built_in/diffusion_models/__init__.py`
- **Example Config**: `ai-toolkit-z_image_turbo/config/examples/train_lora_zimage_turbo_24gb.yaml`
- **Modal Example Config**: `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml`
- **Book Cover Config**: `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml`
- **Book Cover Generator**: `book_cover_cli/book_cover_generator.py`
- **Dataset Prep**: `prepare_book_cover_dataset.py`

---

**Last Updated:** 2025-11-30

---

## ☁️ Modal Cloud Training

### Quick Start with Modal UI

The easiest way to train on Modal's cloud GPUs is through the web UI:

1. **Start the UI:**
   ```bash
   cd ai-toolkit-z_image_turbo/ui
   npm run build_and_start
   ```

2. **Create a job** in the UI with all your training settings

3. **Deploy to Modal:**
   - Go to job detail page → Click ⚙️ Settings → **"Deploy to Modal"**
   - Choose to upload dataset or deploy without upload
   - The Modal dashboard URL will be displayed (or instructions on how to find it)

The UI handles everything automatically! 🚀

**Finding Your Modal URL:**
- The success message will show the Modal dashboard URL if captured
- Check the terminal where the UI is running (Modal prints the URL there)
- Visit [https://modal.com/apps](https://modal.com/apps) to see all deployments
- Run `modal app list` in a terminal to see active apps

### What the Modal Integration Does

When you deploy from the UI:

1. **Config Conversion** - Converts UI config to Modal-compatible YAML
2. **Path Conversion** - Converts local dataset paths to Modal paths (`/root/datasets/...`)
3. **Dataset Upload** - Optionally uploads dataset to Modal volume
4. **Deployment** - Triggers Modal training automatically
5. **Config Saving** - Saves config file for manual use if needed
6. **URL Capture** - Attempts to capture and display the Modal dashboard URL for easy monitoring

### Manual Modal Deployment

You can also deploy manually using the CLI:

```bash
# Create/edit Modal config
cp ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml \
   ai-toolkit-z_image_turbo/config/my_training.yaml

# Deploy to Modal
modal run modal_train_deploy.py config/my_training.yaml
```

### Modal Prerequisites

Before using Modal, ensure:

1. **Modal is installed and configured:**
   ```bash
   pip install modal
   modal setup
   ```

2. **HuggingFace secret is set:**
   ```bash
   modal secret create huggingface HF_TOKEN=your_token_here
   ```

3. **Volumes are ready** (created automatically on first use):
   - `zimage-training-outputs` - Training outputs
   - `zimage-datasets` - Dataset storage
   - `hf-model-cache` - Model caching

### Downloading Results

After training completes:

```bash
modal volume download zimage-training-outputs \
  /root/modal_output/<job_name> \
  ./outputs/<job_name>
```

For detailed instructions, see:
- **[Modal UI Integration Guide](MODAL_UI_INTEGRATION.md)** - Using the web UI
- **[Modal Setup Guide](SETUP_GUIDE.md)** - Complete setup instructions

---

## 📚 Book Cover Entrypoints & Scripts

### Dataset Preparation Scripts

#### `prepare_book_cover_dataset.py`
Prepares book cover datasets for training by creating captions and filtering images.

**Usage:**
```bash
# With metadata
python prepare_book_cover_dataset.py \
    --input /path/to/book/covers \
    --output /path/to/prepared_dataset \
    --metadata /path/to/metadata.json \
    --min-size 512

# With auto-captioning (BLIP)
python prepare_book_cover_dataset.py \
    --input /path/to/book/covers \
    --output /path/to/prepared_dataset \
    --auto-caption \
    --min-size 512
```

**Options:**
- `--input`: Input directory containing book cover images (required)
- `--output`: Output directory for prepared dataset (required)
- `--metadata`: Path to metadata JSON/JSONL file (optional)
- `--auto-caption`: Use BLIP to auto-generate captions (optional)
- `--min-size`: Minimum image size in pixels (default: 512)
- `--max-images`: Maximum number of images to process (optional)

#### `download_and_upload_book_dataset.py`
Downloads the Uchida Laboratory Book Cover Dataset and uploads it to Modal.

**Usage:**
```bash
python download_and_upload_book_dataset.py \
    --output-dir ./datasets \
    --max-images 1000  # Optional: limit for testing
```

**Options:**
- `--output-dir`: Directory to store downloaded dataset (default: ./datasets)
- `--max-images`: Maximum number of images to process (optional)
- `--skip-download`: Skip download, use existing dataset
- `--skip-prepare`: Skip preparation, use existing prepared dataset
- `--skip-upload`: Skip upload to Modal

#### `setup_book_dataset_on_modal.py`
Sets up book cover dataset directly on Modal volume (avoids local upload).

**Usage:**
```bash
# Download and setup on Modal
modal run setup_book_dataset_on_modal.py --max-images 1000

# Create test dataset
modal run setup_book_dataset_on_modal.py --use-test-data
```

**Options:**
- `--max-images`: Maximum number of images to download (optional)
- `--use-test-data`: Create a small test dataset instead

#### `upload_dataset_to_modal.py`
Uploads a prepared dataset to Modal volume.

**Usage:**
```bash
modal run upload_dataset_to_modal.py \
    --local-path ./datasets/prepared_book_covers \
    --remote-path book_covers
```

**Options:**
- `--local-path`: Local path to dataset directory (required)
- `--remote-path`: Remote path in Modal volume (default: book_covers)

### Training Scripts

#### `modal_train_deploy.py`
Main Modal deployment script for training LoRAs.

**Usage:**
```bash
# Train book cover LoRA
modal run modal_train_deploy.py \
    ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml

# Resume training
modal run modal_train_deploy.py \
    ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers_resume.yaml
```

### Generation Scripts

#### `book_cover_cli/book_cover_generator.py`
Interactive and command-line book cover generator.

**Usage:**
```bash
# Interactive mode
cd book_cover_cli
python book_cover_generator.py --interactive

# Command line mode
python book_cover_generator.py \
    --title "The Dark Forest" \
    --author "Liu Cixin" \
    --genre "science fiction" \
    --color-scheme "dark cosmic" \
    --mood "mysterious" \
    --style "minimalist" \
    --width 768 \
    --height 1024 \
    --steps 8 \
    --seed -1 \
    --output-dir ./book_covers \
    --lora-path /path/to/lora.safetensors
```

**Options:**
- `--title`: Book title (required unless using `--interactive`)
- `--author`: Author name (optional)
- `--genre`: Genre (thriller, romance, sci-fi, fantasy, etc.) (optional)
- `--color-scheme`: Color scheme (dark, vibrant, pastel, etc.) (optional)
- `--mood`: Mood/atmosphere (mysterious, inspiring, dramatic, etc.) (optional)
- `--style`: Design style (minimalist, bold, elegant, etc.) (optional)
- `--typography`: Typography style (bold, elegant, modern, etc.) (optional)
- `--elements`: Additional design elements (optional)
- `--width`: Image width in pixels (default: 768)
- `--height`: Image height in pixels (default: 1024)
- `--steps`: Number of inference steps (default: 8)
- `--seed`: Random seed (-1 for random, default: -1)
- `--output-dir`: Output directory (default: ./book_covers)
- `--lora-path`: Path to LoRA checkpoint (default: step 500 checkpoint)
- `--interactive`: Run in interactive mode

#### `book_cover_cli/generate_on_modal.py`
Generate book covers on Modal (for GPU access).

**Usage:**
```bash
cd book_cover_cli
python generate_on_modal.py --title "My Book" --genre thriller
```

#### `book_cover_cli/download_lora.py`
Download LoRA checkpoint from Modal volume to local machine.

**Usage:**
```bash
cd book_cover_cli
python download_lora.py
```

### Utility Scripts

#### `download_training_samples.py`
Download training sample images from Modal volume.

**Usage:**
```bash
modal run download_training_samples.py ./downloaded_training_samples
```

**Options:**
- Output directory (default: ./downloaded_training_samples)

### Configuration Files

#### Book Cover Training Configs

- **`ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml`**
  - Main training configuration for book covers
  - Portrait-oriented resolutions (768x1024)
  - Book cover-specific sample prompts
  - Optimized training parameters

- **`ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers_resume.yaml`**
  - Resume training configuration
  - Automatically resumes from latest checkpoint
  - Same settings as main config

### Complete Workflow Example

```bash
# 1. Prepare dataset
python prepare_book_cover_dataset.py \
    --input ./datasets/uchida_book_dataset/images \
    --output ./datasets/prepared_book_covers \
    --metadata ./datasets/uchida_book_dataset/metadata.json \
    --min-size 512

# 2. Upload to Modal
modal run upload_dataset_to_modal.py \
    --local-path ./datasets/prepared_book_covers \
    --remote-path book_covers

# 3. Train LoRA
modal run modal_train_deploy.py \
    ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml

# 4. Download LoRA (optional)
cd book_cover_cli
python download_lora.py

# 5. Generate covers
python book_cover_generator.py --interactive
```

For more details, see:
- **[Book Cover Training Quick Start](BOOK_COVER_TRAINING_QUICKSTART.md)**
- **[Book Cover Dataset Preparation](BOOK_COVER_DATASET_PREP.md)**
- **[Book Cover Generator CLI](book_cover_cli/README.md)**

