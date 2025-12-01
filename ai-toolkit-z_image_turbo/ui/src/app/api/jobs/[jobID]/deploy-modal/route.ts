import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as yaml from 'yaml';

const execAsync = promisify(exec);
const prisma = new PrismaClient();

// Convert UI job config to Modal-compatible YAML format
function convertToModalConfig(jobConfig: any, datasetName: string): any {
  const config = {
    job: 'extension',
    config: {
      name: jobConfig.config.name,
      process: [
        {
          type: 'sd_trainer',
          training_folder: '/root/modal_output', // Modal mount directory
          device: 'cuda:0',
          ...(jobConfig.config.process[0].trigger_word && {
            trigger_word: jobConfig.config.process[0].trigger_word,
          }),
          network: {
            type: jobConfig.config.process[0].network?.type || 'lora',
            linear: jobConfig.config.process[0].network?.linear || 128,
            linear_alpha: jobConfig.config.process[0].network?.linear_alpha || 128,
            ...(jobConfig.config.process[0].network?.transformer_only !== undefined && {
              transformer_only: jobConfig.config.process[0].network.transformer_only,
            }),
          },
          save: {
            dtype: jobConfig.config.process[0].save?.dtype || 'float16',
            save_every: jobConfig.config.process[0].save?.save_every || 250,
            max_step_saves_to_keep: jobConfig.config.process[0].save?.max_step_saves_to_keep || 4,
            push_to_hub: jobConfig.config.process[0].save?.push_to_hub || false,
            ...(jobConfig.config.process[0].save?.hf_repo_id && {
              hf_repo_id: jobConfig.config.process[0].save.hf_repo_id,
            }),
            ...(jobConfig.config.process[0].save?.hf_private !== undefined && {
              hf_private: jobConfig.config.process[0].save.hf_private,
            }),
          },
          datasets: jobConfig.config.process[0].datasets.map((ds: any) => ({
            folder_path: `/root/datasets/${datasetName}`, // Convert to Modal path
            caption_ext: ds.caption_ext || 'txt',
            caption_dropout_rate: ds.caption_dropout_rate || 0.05,
            shuffle_tokens: ds.shuffle_tokens || false,
            cache_latents_to_disk: ds.cache_latents_to_disk !== undefined ? ds.cache_latents_to_disk : true,
            resolution: ds.resolution || [512, 768, 1024],
            ...(ds.mask_path && { mask_path: ds.mask_path }),
            ...(ds.mask_min_value !== undefined && { mask_min_value: ds.mask_min_value }),
            ...(ds.default_caption && { default_caption: ds.default_caption }),
            ...(ds.network_weight !== undefined && { network_weight: ds.network_weight }),
            ...(ds.is_reg !== undefined && { is_reg: ds.is_reg }),
          })),
          train: {
            batch_size: jobConfig.config.process[0].train?.batch_size || 1,
            steps: jobConfig.config.process[0].train?.steps || 2000,
            gradient_accumulation_steps: jobConfig.config.process[0].train?.gradient_accumulation_steps || 4,
            train_unet: jobConfig.config.process[0].train?.train_unet !== undefined 
              ? jobConfig.config.process[0].train.train_unet 
              : true,
            train_text_encoder: jobConfig.config.process[0].train?.train_text_encoder || false,
            gradient_checkpointing: jobConfig.config.process[0].train?.gradient_checkpointing !== undefined
              ? jobConfig.config.process[0].train.gradient_checkpointing
              : true,
            noise_scheduler: jobConfig.config.process[0].train?.noise_scheduler || 'flowmatch',
            optimizer: jobConfig.config.process[0].train?.optimizer || 'adamw8bit',
            lr: jobConfig.config.process[0].train?.lr || 1e-4,
            dtype: jobConfig.config.process[0].train?.dtype || 'bf16',
            ...(jobConfig.config.process[0].train?.skip_first_sample !== undefined && {
              skip_first_sample: jobConfig.config.process[0].train.skip_first_sample,
            }),
            ...(jobConfig.config.process[0].train?.disable_sampling !== undefined && {
              disable_sampling: jobConfig.config.process[0].train.disable_sampling,
            }),
            ...(jobConfig.config.process[0].train?.linear_timesteps !== undefined && {
              linear_timesteps: jobConfig.config.process[0].train.linear_timesteps,
            }),
            ...(jobConfig.config.process[0].train?.ema_config && {
              ema_config: jobConfig.config.process[0].train.ema_config,
            }),
          },
          model: {
            name_or_path: jobConfig.config.process[0].model?.name_or_path || 'Tongyi-MAI/Z-Image-Turbo',
            arch: jobConfig.config.process[0].model?.arch || 'zimage',
            ...(jobConfig.config.process[0].model?.assistant_lora_path && {
              assistant_lora_path: jobConfig.config.process[0].model.assistant_lora_path,
            }),
            quantize: jobConfig.config.process[0].model?.quantize !== undefined
              ? jobConfig.config.process[0].model.quantize
              : true,
            ...(jobConfig.config.process[0].model?.quantize_te !== undefined && {
              quantize_te: jobConfig.config.process[0].model.quantize_te,
            }),
            ...(jobConfig.config.process[0].model?.low_vram !== undefined && {
              low_vram: jobConfig.config.process[0].model.low_vram,
            }),
            ...(jobConfig.config.process[0].model?.qtype && {
              qtype: jobConfig.config.process[0].model.qtype,
            }),
          },
          sample: {
            sampler: jobConfig.config.process[0].sample?.sampler || 'flowmatch',
            sample_every: jobConfig.config.process[0].sample?.sample_every || 250,
            width: jobConfig.config.process[0].sample?.width || 1024,
            height: jobConfig.config.process[0].sample?.height || 1024,
            seed: jobConfig.config.process[0].sample?.seed || 42,
            walk_seed: jobConfig.config.process[0].sample?.walk_seed !== undefined
              ? jobConfig.config.process[0].sample.walk_seed
              : true,
            guidance_scale: jobConfig.config.process[0].sample?.guidance_scale || 1,
            sample_steps: jobConfig.config.process[0].sample?.sample_steps || 8,
            ...(jobConfig.config.process[0].sample?.prompts && {
              prompts: jobConfig.config.process[0].sample.prompts,
            }),
            ...(jobConfig.config.process[0].sample?.neg && {
              neg: jobConfig.config.process[0].sample.neg,
            }),
          },
        },
      ],
    },
    meta: {
      name: '[name]',
      version: '1.0',
    },
  };

  return config;
}

// Extract dataset name from local path
function extractDatasetName(localPath: string, datasetsFolder: string): string {
  // Remove datasets folder prefix and get the dataset name
  if (localPath.startsWith(datasetsFolder)) {
    const relativePath = localPath.substring(datasetsFolder.length);
    // Get first part of path (dataset name)
    return relativePath.split(path.sep).filter(Boolean)[0] || 'default_dataset';
  }
  // If path doesn't match, try to extract from path
  return path.basename(localPath) || 'default_dataset';
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ jobID: string }> }
) {
  try {
    const { jobID } = await params;
    const body = await request.json();
    const { uploadDataset = false } = body;

    // Get job from database
    const job = await prisma.job.findUnique({
      where: { id: jobID },
    });

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 });
    }

    const jobConfig = JSON.parse(job.job_config);
    
    // Get settings to find datasets folder
    let datasetsFolder = './datasets';
    try {
      // Settings are stored as key-value pairs in settings table
      const settings = await prisma.settings.findMany();
      const settingsObject = settings.reduce((acc: any, setting) => {
        acc[setting.key] = setting.value;
        return acc;
      }, {});
      datasetsFolder = settingsObject.DATASETS_FOLDER || './datasets';
    } catch (error) {
      console.warn('Could not fetch settings, using default:', error);
    }

    // Extract dataset name from first dataset path
    const firstDataset = jobConfig.config.process[0].datasets[0];
    const datasetName = extractDatasetName(firstDataset.folder_path, datasetsFolder);

    // Convert config to Modal format
    const modalConfig = convertToModalConfig(jobConfig, datasetName);

    // Get project root (go up from ui directory)
    // process.cwd() in Next.js API routes is the project root (ui directory)
    const projectRoot = path.resolve(process.cwd(), '..');
    const configDir = path.join(projectRoot, 'config');
    const configFileName = `${jobConfig.config.name.replace(/[^a-zA-Z0-9_-]/g, '_')}_modal.yaml`;
    const configFilePath = path.join(configDir, configFileName);

    // Ensure config directory exists
    await fs.mkdir(configDir, { recursive: true });

    // Write config file
    const yamlContent = yaml.stringify(modalConfig, {
      indent: 2,
      lineWidth: -1,
    });
    await fs.writeFile(configFilePath, yamlContent, 'utf-8');

    // Upload dataset to Modal volume if requested
    if (uploadDataset) {
      const localDatasetPath = firstDataset.folder_path;
      const modalDatasetPath = `/root/datasets/${datasetName}`;
      
      try {
        // Upload dataset to Modal volume
        const uploadCmd = `modal volume upload zimage-datasets "${localDatasetPath}" "${modalDatasetPath}"`;
        await execAsync(uploadCmd, { cwd: projectRoot });
      } catch (error: any) {
        console.error('Dataset upload error:', error);
        // Continue even if upload fails - user can upload manually
      }
    }

    // Trigger Modal deployment
    // modal_train_deploy.py is in the parent directory of ai-toolkit-z_image_turbo
    const modalDeployPath = path.join(projectRoot, '..', 'modal_train_deploy.py');
    const configRelativePath = `config/${path.basename(configFilePath)}`;
    
    // Run modal deployment (use absolute path for config)
    const deployCmd = `cd "${projectRoot}" && modal run "${modalDeployPath}" "${configRelativePath}"`;
    
    try {
      // Execute Modal deployment and try to capture URL
      // Note: Modal prints the URL early in the output, but exec() buffers output
      // We'll start the process and return immediately, but also try to capture URL
      let modalUrl: string | null = null;
      
      // Start the process
      const childProcess = exec(deployCmd, { cwd: projectRoot }, (error, stdout, stderr) => {
        if (error) {
          console.error('Modal deployment error:', error);
        }
        if (stdout) {
          console.log('Modal deployment output:', stdout);
          
          // Extract Modal URL from output
          // Modal URLs can be in various formats:
          // - https://modal.com/apps/...
          // - https://modal.com/app/...
          // - View logs at: https://modal.com/...
          const urlPatterns = [
            /https?:\/\/[^\s]*modal\.com\/apps\/[^\s]*/i,
            /https?:\/\/[^\s]*modal\.com\/app\/[^\s]*/i,
            /https?:\/\/[^\s]*modal\.com[^\s]*/i,
          ];
          
          for (const pattern of urlPatterns) {
            const match = stdout.match(pattern);
            if (match) {
              modalUrl = match[0].replace(/[.,;!?]+$/, ''); // Remove trailing punctuation
              break;
            }
          }
        }
        if (stderr) {
          console.error('Modal deployment stderr:', stderr);
          
          // Also check stderr for URLs
          if (!modalUrl) {
            const urlPatterns = [
              /https?:\/\/[^\s]*modal\.com\/apps\/[^\s]*/i,
              /https?:\/\/[^\s]*modal\.com\/app\/[^\s]*/i,
              /https?:\/\/[^\s]*modal\.com[^\s]*/i,
            ];
            
            for (const pattern of urlPatterns) {
              const match = stderr.match(pattern);
              if (match) {
                modalUrl = match[0].replace(/[.,;!?]+$/, '');
                break;
              }
            }
          }
        }
      });

      // Give Modal a moment to print the URL (it usually appears early)
      // We'll return immediately but the URL might be captured in the callback
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Note: Modal URL is printed in the terminal output
      // Users can find it by:
      // 1. Checking the terminal where the UI is running
      // 2. Running: modal app list (to see running apps)
      // 3. Visiting https://modal.com/apps
      
      return NextResponse.json({
        success: true,
        message: 'Modal deployment started',
        configFile: configFilePath,
        configRelativePath: `config/${path.basename(configFilePath)}`,
        datasetName,
        modalCommand: deployCmd,
        modalUrl: modalUrl || null,
        note: modalUrl 
          ? 'Check the Modal dashboard link above to monitor your training.'
          : 'The Modal deployment URL will appear in your terminal output. You can also visit https://modal.com/apps to see all running deployments.',
        howToFindUrl: [
          'Check the terminal where the UI is running - Modal prints the URL there',
          'Visit https://modal.com/apps to see all your running deployments',
          'Run: modal app list (in a terminal) to see active apps',
        ],
      });
    } catch (error: any) {
      console.error('Failed to start Modal deployment:', error);
      return NextResponse.json(
        { 
          error: 'Failed to start Modal deployment',
          details: error.message,
          configFile: configFilePath, // Still return config file path
        },
        { status: 500 }
      );
    }
  } catch (error: any) {
    console.error('Modal deployment API error:', error);
    return NextResponse.json(
      { error: 'Failed to deploy to Modal', details: error.message },
      { status: 500 }
    );
  }
}

