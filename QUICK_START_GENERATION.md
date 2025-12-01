# Quick Start: Generate Images

## ✅ Setup Verified!

All tests passed! Your system is ready to generate images.

## 🚀 Generate Images Now

### Option 1: Simple Config (Recommended for first test)
```bash
cd ai-toolkit-z_image_turbo
python run.py config/generate_zimage_simple.yaml
```

### Option 2: Full-Featured Config
```bash
cd ai-toolkit-z_image_turbo
python run.py config/generate_zimage.yaml
```

## 📁 Output Location

Images will be saved to:
```
ai-toolkit-z_image_turbo/output/gen/
```

## ⚙️ Configuration

### Use Local Model (Faster)
Edit the config file and uncomment:
```yaml
name_or_path: "/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo"
```

### Customize Prompts
Edit the `prompts:` section in your config file:
```yaml
prompts:
  - "your prompt here"
  - "another prompt"
```

## 🔍 Test Your Setup

Run the test script anytime:
```bash
python test_generation_setup.py
```

## 📚 More Information

- Full guide: `HOW_TO_GENERATE_IMAGES.md`
- Test results: `TEST_GENERATION_SETUP.md`
