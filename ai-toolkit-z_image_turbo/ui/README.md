# AI Toolkit UI

A modern web interface for the AI Toolkit that allows you to easily create, manage, and deploy LoRA training jobs. Built with Next.js, React, and TypeScript.

## 🎨 Features

- **Job Management**: Create, start, stop, and monitor training jobs
- **Dataset Management**: Upload, organize, and manage training datasets
- **Visual Config Editor**: Create and edit training configurations with a visual interface
- **Modal Integration**: Deploy training jobs directly to Modal cloud infrastructure
- **Real-time Monitoring**: Monitor job progress, logs, and outputs in real-time
- **Sample Generation**: View generated samples during training
- **Secure Access**: Optional authentication token for secure access

## 📋 Prerequisites

- **Node.js** >= 18
- **npm** or **yarn** package manager
- **Python** (for AI Toolkit backend)
- **Modal CLI** (for cloud deployment - optional)

## 🚀 Quick Start

### Installation and Setup

1. **Navigate to the UI directory:**
   ```bash
   cd ai-toolkit-z_image_turbo/ui
   ```

2. **Install dependencies and start the UI:**
   ```bash
   npm run build_and_start
   ```

   This command will:
   - Install all npm dependencies
   - Generate Prisma database schema
   - Build the Next.js application
   - Start the UI server and background worker

3. **Access the UI:**
   - Open your browser to: `http://localhost:8675`
   - Or if running on a server: `http://<your-ip>:8675`

### Development Mode

For development with hot-reloading:

```bash
npm run dev
```

This starts:
- Next.js development server with Turbopack
- Background worker for job processing
- Hot-reload on file changes

## 🔐 Security

### Authentication Token

If hosting on an exposed network, secure the UI with an authentication token:

**Linux/macOS:**
```bash
AI_TOOLKIT_AUTH=your_secure_password npm run build_and_start
```

**Windows (CMD):**
```cmd
set AI_TOOLKIT_AUTH=your_secure_password && npm run build_and_start
```

**Windows (PowerShell):**
```powershell
$env:AI_TOOLKIT_AUTH="your_secure_password"; npm run build_and_start
```

Once set, users will be prompted for this token when accessing the UI.

## 📖 Usage Guide

### Creating a Training Job

1. Click **"New Training Job"** in the sidebar
2. Fill in the training parameters:
   - **Job Name**: Unique identifier for your training job
   - **Model**: Select the model to train (Z-Image Turbo, FLUX, etc.)
   - **Dataset**: Choose or create a dataset
   - **Training Parameters**: Steps, learning rate, batch size, etc.
   - **Sample Prompts**: Test prompts for generating samples during training
3. Click **"Create Job"** to save

### Managing Datasets

1. Navigate to **"Datasets"** in the sidebar
2. **Create Dataset**: Click "New Dataset" and upload images
3. **Add Captions**: Each image needs a corresponding `.txt` caption file
4. **Organize**: Group related images into datasets

### Deploying to Modal

The UI includes integrated Modal deployment:

1. **Create or select a training job**
2. Click the **⚙️ Settings** icon on the job detail page
3. Select **"Deploy to Modal"**
4. Choose deployment option:
   - **"Deploy with Upload"**: Automatically uploads dataset to Modal volume
   - **"Deploy without Upload"**: Deploys using existing Modal volume dataset

For detailed Modal integration instructions, see [`MODAL_UI_INTEGRATION.md`](../../MODAL_UI_INTEGRATION.md)

### Monitoring Jobs

- **Dashboard**: View all jobs and their status
- **Job Detail Page**: View logs, samples, and configuration
- **Real-time Updates**: Job status updates automatically
- **Logs**: View training logs in real-time
- **Samples**: View generated sample images during training

## 🛠️ Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot-reload |
| `npm run build` | Build the production application |
| `npm run start` | Start production server |
| `npm run build_and_start` | Install, build, and start (recommended for first run) |
| `npm run update_db` | Update Prisma database schema |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |
| `npm run test:e2e` | Run end-to-end tests |
| `npm run test:e2e:ui` | Run e2e tests with UI |

## 📁 Project Structure

```
ui/
├── src/
│   ├── app/              # Next.js app router pages
│   │   ├── dashboard/    # Dashboard page
│   │   ├── jobs/        # Job management pages
│   │   ├── datasets/     # Dataset management pages
│   │   └── api/          # API routes
│   ├── components/       # React components
│   └── types.ts          # TypeScript types
├── cron/                 # Background worker
├── prisma/               # Database schema
├── public/               # Static assets
└── e2e/                  # End-to-end tests
```

## 🔧 Configuration

### Environment Variables

- `AI_TOOLKIT_AUTH`: Authentication token for securing the UI
- `PORT`: Server port (default: 8675)
- `DATABASE_URL`: SQLite database path (auto-configured)

### Database

The UI uses SQLite (via Prisma) to store:
- Job configurations
- Job status and metadata
- Dataset information

Database file location: `prisma/dev.db`

## 🧪 Testing

### End-to-End Tests

Run Playwright tests:

```bash
# Run all tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed
```

## 🐛 Troubleshooting

### Port Already in Use

If port 8675 is already in use:

```bash
# Find and kill the process
lsof -ti:8675 | xargs kill

# Or change the port in package.json start script
```

### Database Errors

If you encounter database errors:

```bash
npm run update_db
```

This regenerates the Prisma client and updates the database schema.

### Build Errors

Clear cache and rebuild:

```bash
rm -rf .next node_modules
npm install
npm run build
```

### Modal Integration Issues

- Ensure Modal CLI is installed: `pip install modal`
- Verify Modal authentication: `modal token show`
- Check HuggingFace secret: `modal secret list`
- See [`MODAL_UI_INTEGRATION.md`](../../MODAL_UI_INTEGRATION.md) for detailed troubleshooting

## 📚 Additional Resources

- **Main README**: [`../README.md`](../README.md) - AI Toolkit overview
- **Setup Guide**: [`../../SETUP_GUIDE.md`](../../SETUP_GUIDE.md) - Complete setup instructions
- **Modal Integration**: [`../../MODAL_UI_INTEGRATION.md`](../../MODAL_UI_INTEGRATION.md) - Modal deployment guide
- **Quick Start**: [`../../MODAL_QUICK_START.md`](../../MODAL_QUICK_START.md) - Quick reference

## 🎯 Key Features Explained

### Job Management

- **Create**: Visual form-based job creation
- **Edit**: Modify job configurations
- **Start/Stop**: Control job execution
- **Monitor**: Real-time status and logs
- **Delete**: Remove jobs and clean up

### Dataset Management

- **Upload**: Drag-and-drop image upload
- **Captioning**: Add/edit captions for images
- **Organization**: Group images into datasets
- **Validation**: Automatic validation of dataset structure

### Modal Deployment

- **One-Click Deploy**: Deploy to Modal with a single click
- **Automatic Upload**: Optionally upload datasets automatically
- **Config Conversion**: Automatic conversion to Modal-compatible format
- **URL Capture**: Automatic capture of Modal dashboard URLs

## 🔄 Architecture

The UI consists of:

1. **Next.js Frontend**: React-based web interface
2. **API Routes**: Server-side API endpoints
3. **Background Worker**: Processes jobs and updates status
4. **Prisma Database**: Stores job and dataset metadata
5. **Modal Integration**: Deploys jobs to Modal cloud

## 📝 Notes

- The UI does **not** need to stay running for jobs to execute
- Jobs run independently once started
- The UI is only needed to start, stop, and monitor jobs
- Training happens on your local machine or Modal cloud (depending on deployment)

## 🤝 Contributing

When contributing to the UI:

1. Follow the existing code style
2. Run `npm run format` before committing
3. Add tests for new features
4. Update this README if adding new features

## 📄 License

See the main project LICENSE file.

---

**Last Updated:** 2025-11-30
