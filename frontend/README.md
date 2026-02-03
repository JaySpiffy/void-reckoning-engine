# Campaign Dashboard v2

Modern React + TypeScript frontend for the Campaign Dashboard.

## Prerequisites

- Node.js 18+
- npm 9+

## Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Run in development mode:**
   ```bash
   npm run dev
   ```
   The dashboard will be available at `http://localhost:5173`.

3. **Build for production:**
   ```bash
   npm run build
   ```
   The build output will be in the `dist/` directory.

## Project Structure

- `src/api`: API client and HTTP utilities
- `src/components`: React components (organized by feature)
- `src/hooks`: Custom React hooks
- `src/stores`: Zustand state stores (centralized state)
- `src/types`: TypeScript type definitions
- `src/utils`: Utility functions
- `src/styles`: Global styles and theme

## Backend Connection

This frontend is configured to proxy API requests to the FastAPI backend running on port 8000.
See `vite.config.ts` for proxy settings.

## State Management

We use **Zustand** for lightweight and efficient state management. Stores are located in `src/stores/`.
