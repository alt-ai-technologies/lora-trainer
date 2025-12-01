import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(request: NextRequest, { params }: { params: { jobID: string } }) {
  const { jobID } = await params;

  const job = await prisma.job.findUnique({
    where: { id: jobID },
  });

  if (!job) {
    return NextResponse.json({ error: 'Job not found' }, { status: 404 });
  }

  // Validate job config before starting
  try {
    const jobConfig = JSON.parse(job.job_config);
    const datasets = jobConfig.config?.process?.[0]?.datasets || [];
    
    // Check for placeholder or invalid dataset paths
    const invalidPaths = ['/path/to/images/folder', '/path/to/images', ''];
    const invalidDatasets = datasets.filter((ds: any) => 
      !ds.folder_path || invalidPaths.includes(ds.folder_path) || ds.folder_path.includes('/path/to')
    );
    
    if (invalidDatasets.length > 0) {
      return NextResponse.json(
        { 
          error: 'Invalid dataset path',
          details: `One or more datasets have invalid paths. Please edit the job and select a valid dataset. Invalid paths: ${invalidDatasets.map((d: any) => d.folder_path).join(', ')}`,
          suggestion: 'Go to the job edit page and select a valid dataset from the dropdown.'
        },
        { status: 400 }
      );
    }
  } catch (error) {
    // If config parsing fails, still allow the job to start (let the backend handle it)
    console.warn('Could not validate job config:', error);
  }

  // get highest queue position
  const highestQueuePosition = await prisma.job.aggregate({
    _max: {
      queue_position: true,
    },
  });
  const newQueuePosition = (highestQueuePosition._max.queue_position || 0) + 1000;

  await prisma.job.update({
    where: { id: jobID },
    data: { queue_position: newQueuePosition },
  });

  // make sure the queue is running
  const queue = await prisma.queue.findFirst({
    where: {
      gpu_ids: job.gpu_ids,
    },
  });

  // if queue doesn't exist, create it
  if (!queue) {
    await prisma.queue.create({
      data: {
        gpu_ids: job.gpu_ids,
        is_running: false,
      },
    });
  }

  await prisma.job.update({
    where: { id: jobID },
    data: {
      status: 'queued',
      stop: false,
      return_to_queue: false,
      info: 'Job queued',
    },
  });

  // Return the response immediately
  return NextResponse.json(job);
}
