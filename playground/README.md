## Kubrick Playground

Kubrick Playground is a UI that allows you to interact with the Kubrick API. It serves as a test bed to validate your deployment or as an example for API integration. 

The Kubrick Playground provides an intuitive interface for:

- **Semantic Video Search**: Find videos using natural language queries or media-based searches
- **Video Library Management**: Browse your video collection
- **Video Embedding**: Upload and index new videos to make them searchable
- **Multimodal Queries**: Search across visual, textual, and audio content within videos

### Features

### Search

- **Text-based search**: Find videos using natural language descriptions
- **Media-based search**: Upload images, videos, or audio files to find similar content
- **Similarity thresholds**: Fine-tune search precision with configurable similarity scores
- **Multi-modal filtering**: Search across visual-text and audio modalities
- **Scope control**: Search at clip-level or full video level

### Video Library

- Browse video collection
- View video metadata (duration, creation date)
- Thumbnail previews with video player integration

### Video Embedding

- Upload videos for indexing
- Progress tracking via the Tasks page

## Installation

A Playground is automatically generated and accessible via CloudFront URL when deploying Kubrick with the CLI tool. However if you would like to install and run the Playground locally, follow the guidance below. 

### Prerequisites

- Node.js 18+
- npm, yarn, pnpm, or bun
- Access to a deployed Kubrick API

### Setup

1. **Clone the repository**
    
    ```bash
    git clone https://github.com/kubrick-ai/playground.git
    cd playground
    
    ```
    
2. **Install dependencies**
    
    ```bash
    npm install
    # or
    yarn install
    # or
    pnpm install
    
    ```
    
3. **Configure environment**
    - Create a `.env` in the playground root directory
    - Add the following to the `.env` file
    
    ```bash
    NEXT_PUBLIC_API_BASE=<your deployed Kubrick API>
    ```
    
4. **Start development server**
    
    ```bash
    next dev
    ```
    
5. **Open the application** Navigate to [http://localhost:3000](http://localhost:3000/)

##
