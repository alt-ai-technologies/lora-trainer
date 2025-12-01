# Modal Test Deployment Guide

This guide explains how to deploy and run the Z-Image Turbo Hub Models tests on Modal.

## Prerequisites

1. **Modal Account**: Sign up at [modal.com](https://modal.com) if you don't have an account
2. **Modal CLI**: Install the Modal CLI:
   ```bash
   pip install modal
   ```
3. **Authentication**: Authenticate with Modal:
   ```bash
   modal token new
   ```

## Optional: Hugging Face Token

If you need to access gated models, set up a Hugging Face secret in Modal:

```bash
modal secret create huggingface \
  HF_TOKEN=your_huggingface_token_here
```

Or if you already have a secret named "huggingface", the script will use it automatically.

## Running Tests on Modal

### Basic Usage

Run the default test suite:

```bash
modal run modal_test_deploy.py
```

### Specify a Different Test File

```bash
modal run modal_test_deploy.py --test-file tests/test_zimage_turbo_hub_models.py
```

### Monitor Execution

You can monitor the execution in real-time:

1. **Modal Dashboard**: Visit [modal.com/apps](https://modal.com/apps) to see running functions
2. **Logs**: View logs in the Modal dashboard or use:
   ```bash
   modal logs zimage-turbo-tests
   ```

## Configuration

### GPU Selection

The script is configured to use an A100 GPU by default. You can modify this in `modal_test_deploy.py`:

```python
@app.function(
    gpu="A100",  # Options: "A100", "H100", "A10G", "T4", etc.
    ...
)
```

### Timeout

The default timeout is 1 hour (3600 seconds). Adjust if needed:

```python
timeout=3600,  # Increase for slower connections or larger models
```

## What Gets Deployed

1. **Dependencies**: All required Python packages including PyTorch with CUDA support
2. **Code**: The `ai-toolkit-z_image_turbo` directory and `tests` directory are mounted
3. **Environment**: Hugging Face transfer enabled for faster downloads

## Test Execution Flow

1. Modal spins up a GPU instance (A100)
2. Installs all dependencies
3. Mounts your code
4. Runs the test suite
5. Downloads models from Hugging Face Hub (if not cached)
6. Executes all tests
7. Returns results

## Troubleshooting

### Tests Fail to Start

- Check that Modal CLI is authenticated: `modal token list`
- Verify the test file path is correct
- Check Modal logs for errors

### Model Download Issues

- Ensure you have internet access from Modal (should work by default)
- If using gated models, verify your Hugging Face token is set up correctly
- Check Hugging Face Hub status

### GPU Not Available

- Modal may be out of A100 GPUs, try a different GPU type
- Check Modal's GPU availability: [modal.com/docs/guide/gpu](https://modal.com/docs/guide/gpu)

### Timeout Issues

- Increase the timeout in the function definition
- Check if model downloads are taking too long
- Consider using cached models if available

## Model Caching

The deployment uses **Modal Volumes** to cache Hugging Face models between runs, significantly speeding up subsequent deployments:

- **Volume Name**: `hf-model-cache`
- **Cache Location**: `/root/.cache/huggingface`
- **Automatic**: Models are automatically cached after the first download
- **Persistent**: Cache persists across deployments, so subsequent runs are much faster

On the first run, models will be downloaded (this may take several minutes). On subsequent runs, models will be loaded from the cache, reducing test time from ~3-5 minutes to ~30-60 seconds.

To clear the cache (if needed):
```bash
modal volume delete hf-model-cache
```

## Cost Considerations

- Modal charges per second of GPU usage
- A100 GPUs are more expensive but faster
- Consider using A10G or T4 for lighter workloads
- Tests typically complete in 10-30 minutes on first run (with downloads)
- Subsequent runs with cached models: 30-60 seconds

## Example Output

```
============================================================
Z-Image Turbo Hub Models Test Suite - Modal Deployment
============================================================
Test file: /root/tests/test_zimage_turbo_hub_models.py
AI Toolkit path: /root/ai-toolkit-z_image_turbo
CUDA available: True
CUDA device: NVIDIA A100-SXM4-40GB
============================================================

Running: Hub Model IDs Valid...
✓ Hub Model IDs Valid passed

Running: Model Discovery with Hub Path...
✓ Model Discovery with Hub Path passed

...
```

## Next Steps

After successful deployment, you can:

1. Integrate into CI/CD pipelines
2. Schedule regular test runs
3. Use Modal's webhooks for notifications
4. Set up monitoring and alerts

For more information, see [Modal Documentation](https://modal.com/docs).

