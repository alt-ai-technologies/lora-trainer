import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  try {
    if (id) {
      const job = await prisma.job.findUnique({
        where: { id },
      });
      return NextResponse.json(job);
    }

    const jobs = await prisma.job.findMany({
      orderBy: { created_at: 'desc' },
    });
    return NextResponse.json({ jobs: jobs });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: 'Failed to fetch training data' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { id, name, job_config, gpu_ids } = body;

    // Validate required fields
    if (!name) {
      return NextResponse.json(
        { error: 'Job name is required' },
        { status: 400 }
      );
    }

    if (!job_config) {
      return NextResponse.json(
        { error: 'Job config is required' },
        { status: 400 }
      );
    }

    // Validate dataset paths before saving
    const datasets = job_config?.config?.process?.[0]?.datasets || [];
    
    // Check if datasets array is empty
    if (datasets.length === 0) {
      return NextResponse.json(
        { 
          error: 'No datasets configured',
          details: 'At least one dataset is required to create a training job.',
          suggestion: 'Please add a dataset using the dataset selector in the job form.'
        },
        { status: 400 }
      );
    }
    
    // Check for invalid dataset paths
    const invalidPaths = ['/path/to/images/folder', '/path/to/images', ''];
    const invalidDatasets = datasets.filter((ds: any) => 
      !ds.folder_path || invalidPaths.includes(ds.folder_path) || (typeof ds.folder_path === 'string' && ds.folder_path.includes('/path/to'))
    );
    
    if (invalidDatasets.length > 0) {
      console.error('Invalid dataset paths:', invalidDatasets);
      const invalidPath = invalidDatasets[0].folder_path || '(empty)';
      return NextResponse.json(
        { 
          error: 'Invalid dataset path',
          details: `Please select a valid dataset. The placeholder path "${invalidPath}" is not valid.`,
          suggestion: 'Select a dataset from the dropdown menu in the job form. Make sure the dataset path is a real folder on your system.'
        },
        { status: 400 }
      );
    }

    // Log the request for debugging (remove sensitive data)
    console.log('Creating/updating job:', { id, name, gpu_ids, datasetsCount: datasets.length });

    if (id) {
      // Update existing training
      const training = await prisma.job.update({
        where: { id },
        data: {
          name,
          gpu_ids,
          job_config: JSON.stringify(job_config),
        },
      });
      return NextResponse.json(training);
    } else {
      // find the highest queue position and add 1000
      const highestQueuePosition = await prisma.job.aggregate({
        _max: {
          queue_position: true,
        },
      });
      const newQueuePosition = (highestQueuePosition._max.queue_position || 0) + 1000;

      // Create new training
      const training = await prisma.job.create({
        data: {
          name,
          gpu_ids,
          job_config: JSON.stringify(job_config),
          queue_position: newQueuePosition,
        },
      });
      return NextResponse.json(training);
    }
  } catch (error: any) {
    if (error.code === 'P2002') {
      // Handle unique constraint violation, 409=Conflict
      return NextResponse.json({ error: 'Job name already exists' }, { status: 409 });
    }
    console.error('Error in POST /api/jobs:', error);
    // Handle other errors with more detail
    const errorMessage = error.message || 'Failed to save training data';
    return NextResponse.json(
      { 
        error: 'Failed to save training data',
        details: errorMessage,
        ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
      },
      { status: 500 }
    );
  }
}
