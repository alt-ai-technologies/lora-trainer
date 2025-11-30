Modal Deployment summary
Main files
MODAL_DEPLOYMENT_PLAN.md — Deployment plan covering:
Architecture and components
Implementation phases
Volume management
Troubleshooting
Cost estimates
modal_train_deploy.py — Main Modal deployment script with:
Z-Image Turbo dependencies
Model caching (HF cache volume)
Training output persistence
Dataset volume support
Error handling and recovery
modal_train_lora_zimage_turbo_24gb.yaml — Modal-specific training config:
Pre-configured for Modal paths
Z-Image Turbo settings
Training adapter configuration
Optimized for 24GB VRAM
MODAL_QUICK_START.md — Quick start guide:
5-minute setup
Common tasks
Troubleshooting tips
Features
Model caching: HF models cached in a persistent volume (first run downloads, subsequent runs use cache)
Training outputs: LoRAs, samples, and checkpoints saved to a persistent volume
Dataset support: Local mount or volume upload
Cost: ~$0.50–$1.20 per training run
Error recovery: Continue on failure with --recover flag
Next steps
Test deployment: Run with a small dataset to verify everything works
Verify caching: Confirm models are cached between runs
Helper scripts: Create utilities for dataset upload and result download
Usage
# 1. Setup (one-time)modal secret create huggingface HF_TOKEN=your_token# 2. Prepare datasetmkdir -p dataset/my_style# Add images and captions...# 3. Create configcp ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml \   ai-toolkit-z_image_turbo/config/my_training.yaml# Edit config: update name and dataset path# 4. Run trainingmodal run modal_train_deploy.py config/my_training.yaml
The deployment is ready. The plan covers architecture, implementation, and usage. Should I test the deployment or create helper scripts next?