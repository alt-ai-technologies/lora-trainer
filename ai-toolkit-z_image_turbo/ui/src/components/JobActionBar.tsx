import Link from 'next/link';
import { Eye, Trash2, Pen, Play, Pause, Cog, X, Cloud } from 'lucide-react';
import { Button } from '@headlessui/react';
import { openConfirm } from '@/components/ConfirmModal';
import { Job } from '@prisma/client';
import { startJob, stopJob, deleteJob, getAvaliableJobActions, markJobAsStopped, deployToModal } from '@/utils/jobs';
import { startQueue } from '@/utils/queue';
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';
import { redirect } from 'next/navigation';

interface JobActionBarProps {
  job: Job;
  onRefresh?: () => void;
  afterDelete?: () => void;
  hideView?: boolean;
  className?: string;
  autoStartQueue?: boolean;
}

export default function JobActionBar({
  job,
  onRefresh,
  afterDelete,
  className,
  hideView,
  autoStartQueue = false,
}: JobActionBarProps) {
  const { canStart, canStop, canDelete, canEdit, canRemoveFromQueue } = getAvaliableJobActions(job);

  if (!afterDelete) afterDelete = onRefresh;

  return (
    <div className={`${className}`}>
      {canStart && (
        <Button
          onClick={async () => {
            if (!canStart) return;
            await startJob(job.id);
            // start the queue as well
            if (autoStartQueue) {
              await startQueue(job.gpu_ids);
            }
            if (onRefresh) onRefresh();
          }}
          className={`ml-2 opacity-100`}
        >
          <Play />
        </Button>
      )}
      {canRemoveFromQueue && (
        <Button
          onClick={async () => {
            if (!canRemoveFromQueue) return;
            await markJobAsStopped(job.id);
            if (onRefresh) onRefresh();
          }}
          className={`ml-2 opacity-100`}
        >
          <X />
        </Button>
      )}
      {canStop && (
        <Button
          onClick={() => {
            if (!canStop) return;
            openConfirm({
              title: 'Stop Job',
              message: `Are you sure you want to stop the job "${job.name}"? You CAN resume later.`,
              type: 'info',
              confirmText: 'Stop',
              onConfirm: async () => {
                await stopJob(job.id);
                if (onRefresh) onRefresh();
              },
            });
          }}
          className={`ml-2 opacity-100`}
        >
          <Pause />
        </Button>
      )}
      {!hideView && (
        <Link href={`/jobs/${job.id}`} className="ml-2 text-gray-200 hover:text-gray-100 inline-block">
          <Eye />
        </Link>
      )}
      {canEdit && (
        <Link href={`/jobs/new?id=${job.id}`} className="ml-2 hover:text-gray-100 inline-block">
          <Pen />
        </Link>
      )}
      <Button
        onClick={() => {
          let message = `Are you sure you want to delete the job "${job.name}"? This will also permanently remove it from your disk.`;
          if (job.status === 'running') {
            message += ' WARNING: The job is currently running. You should stop it first if you can.';
          }
          openConfirm({
            title: 'Delete Job',
            message: message,
            type: 'warning',
            confirmText: 'Delete',
            onConfirm: async () => {
              if (job.status === 'running') {
                try {
                  await stopJob(job.id);
                } catch (e) {
                  console.error('Error stopping job before deleting:', e);
                }
              }
              await deleteJob(job.id);
              if (afterDelete) afterDelete();
            },
          });
        }}
        className={`ml-2 opacity-100`}
      >
        <Trash2 />
      </Button>
      <div className="border-r border-1 border-gray-700 ml-2 inline"></div>
      <Menu>
        <MenuButton className={'ml-2'}>
          <Cog />
        </MenuButton>
        <MenuItems anchor="bottom" className="bg-gray-900 border border-gray-700 rounded shadow-lg w-48 px-2 py-2 mt-4">
          <MenuItem>
            <Link href={`/jobs/new?cloneId=${job.id}`} className="cursor-pointer px-4 py-1 hover:bg-gray-800 rounded block">
              Clone Job
            </Link>
          </MenuItem>
          <MenuItem>
            <div
              className="cursor-pointer px-4 py-1 hover:bg-gray-800 rounded"
              onClick={() => {
                let message = `Are you sure you want to mark this job as stopped? This will set the job status to 'stopped' if the status is hung. Only do this if you are 100% sure the job is stopped. This will NOT stop the job.`;
                openConfirm({
                  title: 'Mark Job as Stopped',
                  message: message,
                  type: 'warning',
                  confirmText: 'Mark as Stopped',
                  onConfirm: async () => {
                    await markJobAsStopped(job.id);
                    onRefresh && onRefresh();
                  },
                });
              }}
            >
              Mark as Stopped
            </div>
          </MenuItem>
          <MenuItem>
            <div
              className="cursor-pointer px-4 py-1 hover:bg-gray-800 rounded flex items-center gap-2"
              onClick={() => {
                openConfirm({
                  title: 'Deploy to Modal',
                  message: `Deploy this job to Modal for cloud training?\n\nThis will:\n1. Convert config to Modal format\n2. Save config file\n3. Upload dataset to Modal volume (recommended)\n4. Start training on Modal\n\nDo you want to upload the dataset? (Click Cancel to deploy without upload)`,
                  type: 'info',
                  confirmText: 'Deploy with Upload',
                  onConfirm: async () => {
                    try {
                      const response = await deployToModal(job.id, true);
                      const modalUrl = response.data.modalUrl;
                      let message = `✅ Modal deployment started!\n\n`;
                      if (modalUrl) {
                        message += `🔗 Modal Dashboard: ${modalUrl}\n\n`;
                      }
                      message += `📄 Config: ${response.data.configRelativePath}\n📁 Dataset: ${response.data.datasetName}\n\n`;
                      if (modalUrl) {
                        message += `Click the link above to monitor your training.`;
                      } else {
                        message += `📋 How to find your Modal URL:\n`;
                        if (response.data.howToFindUrl) {
                          response.data.howToFindUrl.forEach((tip: string, i: number) => {
                            message += `${i + 1}. ${tip}\n`;
                          });
                        } else {
                          message += `1. Check the terminal where the UI is running\n2. Visit https://modal.com/apps\n`;
                        }
                      }
                      alert(message);
                      if (onRefresh) onRefresh();
                    } catch (error: any) {
                      const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
                      const details = error.response?.data?.details || '';
                      const configFile = error.response?.data?.configFile;
                      alert(`❌ Failed to deploy to Modal:\n\n${errorMsg}${details ? `\n\nDetails: ${details}` : ''}${configFile ? `\n\nConfig file saved at:\n${configFile}` : ''}`);
                    }
                  },
                  onCancel: async () => {
                    try {
                      const response = await deployToModal(job.id, false);
                      const modalUrl = response.data.modalUrl;
                      let message = `✅ Modal deployment started!\n\n`;
                      if (modalUrl) {
                        message += `🔗 Modal Dashboard: ${modalUrl}\n\n`;
                      }
                      message += `📄 Config: ${response.data.configRelativePath}\n\n⚠️ Note: Dataset must be uploaded separately using:\nmodal volume upload zimage-datasets <local_path> /root/datasets/<dataset_name>\n\n`;
                      if (modalUrl) {
                        message += `Click the link above to monitor your training.`;
                      } else {
                        message += `📋 How to find your Modal URL:\n`;
                        if (response.data.howToFindUrl) {
                          response.data.howToFindUrl.forEach((tip: string, i: number) => {
                            message += `${i + 1}. ${tip}\n`;
                          });
                        } else {
                          message += `1. Check the terminal where the UI is running\n2. Visit https://modal.com/apps\n`;
                        }
                      }
                      alert(message);
                      if (onRefresh) onRefresh();
                    } catch (error: any) {
                      const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
                      const details = error.response?.data?.details || '';
                      const configFile = error.response?.data?.configFile;
                      alert(`❌ Failed to deploy to Modal:\n\n${errorMsg}${details ? `\n\nDetails: ${details}` : ''}${configFile ? `\n\nConfig file saved at:\n${configFile}` : ''}`);
                    }
                  },
                });
              }}
            >
              <Cloud className="w-4 h-4" />
              Deploy to Modal
            </div>
          </MenuItem>
        </MenuItems>
      </Menu>
    </div>
  );
}
