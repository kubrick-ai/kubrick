# Kubrick CLI

A command-line interface tool for deploying and managing Kubrick infrastructure
with Lambda packages and Terraform.

## Installation

```bash
npm install
npm run build
```

## Commands

- `kubrick deploy` - Deploy new or existing Kubrick infrastructure
- `kubrick destroy` - Destroy existing Kubrick infrastructure
- `kubrick --help` - Show help message

## Development

```bash
npm run dev
npm run lint  # Type checking
```

## Usage

After building, the CLI provides interactive prompts for infrastructure
management:

```bash
kubrick deploy    # Deploy with prompts
kubrick destroy   # Destroy with prompts
```

