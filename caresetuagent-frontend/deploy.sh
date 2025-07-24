#!/bin/bash

# Frontend Deployment Script
# Usage: ./deploy.sh [environment] [platform]
# Example: ./deploy.sh production netlify

set -e

# Default values
ENVIRONMENT=${1:-production}
PLATFORM=${2:-netlify}

echo "🚀 Starting deployment for $ENVIRONMENT environment to $PLATFORM..."

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "❌ Invalid environment. Use: development, staging, or production"
    exit 1
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
npm run clean

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Run linting
echo "🔍 Running linting..."
npm run lint

# Build for specified environment
echo "🔨 Building for $ENVIRONMENT..."
case $ENVIRONMENT in
    development)
        npm run build:dev
        ;;
    staging)
        npm run build:staging
        ;;
    production)
        npm run build:production
        ;;
esac

# Deploy to specified platform
echo "🚀 Deploying to $PLATFORM..."
case $PLATFORM in
    netlify)
        if command -v netlify &> /dev/null; then
            netlify deploy --prod --dir=dist
        else
            echo "❌ Netlify CLI not found. Install with: npm install -g netlify-cli"
            exit 1
        fi
        ;;
    vercel)
        if command -v vercel &> /dev/null; then
            vercel --prod
        else
            echo "❌ Vercel CLI not found. Install with: npm install -g vercel"
            exit 1
        fi
        ;;
    github-pages)
        echo "📄 For GitHub Pages, push to main branch or use GitHub Actions"
        echo "📁 Build files are ready in ./dist directory"
        ;;
    manual)
        echo "📁 Build completed! Files are ready in ./dist directory"
        echo "📋 Upload the contents of ./dist to your hosting provider"
        ;;
    *)
        echo "❌ Unsupported platform. Use: netlify, vercel, github-pages, or manual"
        exit 1
        ;;
esac

echo "✅ Deployment completed successfully!"

# Show build info
echo ""
echo "📊 Build Information:"
echo "Environment: $ENVIRONMENT"
echo "Platform: $PLATFORM"
echo "Build size:"
du -sh dist/
echo ""
echo "📁 Build contents:"
ls -la dist/