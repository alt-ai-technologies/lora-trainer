import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { defaultTrainFolder, defaultDatasetsFolder } from '@/paths';
import { flushCache } from '@/server/settings';

const prisma = new PrismaClient();

export async function GET() {
  try {
    const settings = await prisma.settings.findMany();
    const settingsObject = settings.reduce((acc: any, setting) => {
      acc[setting.key] = setting.value;
      return acc;
    }, {});
    // if TRAINING_FOLDER is not set, use default
    if (!settingsObject.TRAINING_FOLDER || settingsObject.TRAINING_FOLDER === '') {
      settingsObject.TRAINING_FOLDER = defaultTrainFolder;
    }
    // if DATASETS_FOLDER is not set, use default
    if (!settingsObject.DATASETS_FOLDER || settingsObject.DATASETS_FOLDER === '') {
      settingsObject.DATASETS_FOLDER = defaultDatasetsFolder;
    }
    return NextResponse.json(settingsObject);
  } catch (error) {
    console.error('Error fetching settings:', error);
    return NextResponse.json({ error: 'Failed to fetch settings' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { HF_TOKEN, TRAINING_FOLDER, DATASETS_FOLDER } = body;

    // Ensure values are strings (handle undefined/null)
    const hfToken = String(HF_TOKEN ?? '');
    const trainingFolder = String(TRAINING_FOLDER ?? '');
    const datasetsFolder = String(DATASETS_FOLDER ?? '');

    // Upsert both settings
    await Promise.all([
      prisma.settings.upsert({
        where: { key: 'HF_TOKEN' },
        update: { value: hfToken },
        create: { key: 'HF_TOKEN', value: hfToken },
      }),
      prisma.settings.upsert({
        where: { key: 'TRAINING_FOLDER' },
        update: { value: trainingFolder },
        create: { key: 'TRAINING_FOLDER', value: trainingFolder },
      }),
      prisma.settings.upsert({
        where: { key: 'DATASETS_FOLDER' },
        update: { value: datasetsFolder },
        create: { key: 'DATASETS_FOLDER', value: datasetsFolder },
      }),
    ]);

    flushCache();

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error('Error updating settings:', error);
    console.error('Error stack:', error?.stack);
    console.error('Error name:', error?.name);
    console.error('Error code:', error?.code);
    const errorMessage = error?.message || String(error) || 'Unknown error';
    return NextResponse.json(
      { 
        error: 'Failed to update settings', 
        details: errorMessage,
        code: error?.code,
        name: error?.name
      },
      { status: 500 }
    );
  }
}
