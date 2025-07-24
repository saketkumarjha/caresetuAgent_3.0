# Frontend Deployment Guide

This guide covers how to build and deploy the CareSetu Voice Assistant frontend to various hosting platforms.

## Quick Start

### Development Build

```bash
npm run build:dev
```

### Production Build

```bash
npm run build:production
```

### Preview Production Build

```bash
npm run preview:production
```

## Environment Configuration

The application supports three environments:

### Development

- **Environment file**: `.env.development`
- **Build command**: `npm run build:dev`
- **Features**: Debug mode enabled, detailed logging, dev tools
- **Backend**: Local development server

### Staging

- **Environment file**: `.env.staging`
- **Build command**: `npm run build:staging`
- **Features**: Debug mode enabled, info logging, dev tools
- **Backend**: Staging server on Render.com

### Production

- **Environment file**: `.env.production`
- **Build command**: `npm run build:production`
- **Features**: Optimized build, minimal logging, analytics enabled
- **Backend**: Production server on Render.com

## Environment Variables

### Required Variables

```env
VITE_LIVEKIT_URL=wss://your-livekit-url
VITE_LIVEKIT_API_KEY=your-api-key
VITE_LIVEKIT_API_SECRET=your-api-secret
```

### Optional Variables

```env
VITE_APP_NAME=CareSetu Voice Assistant
VITE_TOKEN_ENDPOINT=https://your-backend.com/api/token
VITE_DEBUG_MODE=false
VITE_LOG_LEVEL=warn
VITE_ENABLE_DEVTOOLS=false
VITE_ENABLE_ANALYTICS=true
```

## Deployment Platforms

### 1. Netlify

#### Automatic Deployment (Recommended)

1. Connect your GitHub repository to Netlify
2. Set build command: `npm run build:production`
3. Set publish directory: `dist`
4. Configure environment variables in Netlify dashboard

#### Manual Deployment

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy using script
./deploy.sh production netlify

# Or deploy manually
npm run build:production
netlify deploy --prod --dir=dist
```

#### Configuration

The `netlify.toml` file is already configured with:

- Build settings
- Redirect rules for SPA
- Security headers
- Caching rules

### 2. Vercel

#### Automatic Deployment (Recommended)

1. Connect your GitHub repository to Vercel
2. Vercel will automatically detect Vite configuration
3. Configure environment variables in Vercel dashboard

#### Manual Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy using script
./deploy.sh production vercel

# Or deploy manually
npm run build:production
vercel --prod
```

#### Configuration

The `vercel.json` file is already configured with:

- Build settings
- SPA routing
- Security headers
- Caching rules

### 3. GitHub Pages

#### Automatic Deployment

1. Enable GitHub Actions in your repository
2. The `.github/workflows/deploy.yml` workflow will automatically deploy on push to main
3. Enable GitHub Pages in repository settings

#### Manual Deployment

```bash
# Build for production
npm run build:production

# Deploy to gh-pages branch (requires gh-pages package)
npm install -g gh-pages
gh-pages -d dist
```

### 4. Other Static Hosting

For other platforms (AWS S3, Firebase Hosting, etc.):

```bash
# Build for production
npm run build:production

# Upload contents of ./dist directory to your hosting provider
```

## Build Optimization

### Bundle Analysis

```bash
npm run analyze
```

### Performance Optimization

The build is optimized with:

- Code splitting for vendor libraries
- Asset optimization
- Tree shaking
- Minification
- Source maps for debugging

### Bundle Size

- **Vendor chunk**: React, React DOM (~45KB gzipped)
- **LiveKit chunk**: LiveKit client libraries (~120KB gzipped)
- **App chunk**: Application code (~30KB gzipped)

## Security Configuration

### Content Security Policy

Configured in deployment files with appropriate directives for:

- WebRTC connections
- Audio/video access
- External API calls

### Environment Security

- API secrets are only used server-side
- Client only receives public configuration
- Tokens are stored in memory only

## Monitoring and Analytics

### Build Information

Each build includes:

- Version number
- Build timestamp
- Environment information

### Performance Monitoring

- Connection time tracking
- Audio latency monitoring
- Error rate tracking
- User session analytics (production only)

## Troubleshooting

### Common Issues

#### Build Fails

```bash
# Clear cache and reinstall
npm run clean
rm -rf node_modules package-lock.json
npm install
npm run build:production
```

#### Environment Variables Not Loading

- Ensure variables start with `VITE_`
- Check correct `.env.*` file is being used
- Verify no typos in variable names

#### LiveKit Connection Issues

- Verify `VITE_LIVEKIT_URL` is correct
- Check API key and secret are valid
- Ensure backend token endpoint is accessible

#### Deployment Issues

- Check build output in `dist/` directory
- Verify all assets are included
- Test with `npm run preview` before deploying

### Debug Mode

Enable debug mode in development:

```env
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug
```

### Performance Issues

- Use `npm run analyze` to check bundle size
- Enable performance monitoring in staging
- Check network tab for slow resources

## CI/CD Pipeline

### GitHub Actions

The included workflow:

1. Runs on push to main/staging/development branches
2. Tests multiple Node.js versions
3. Runs linting and builds
4. Deploys to GitHub Pages and Netlify
5. Uploads build artifacts

### Custom CI/CD

For other CI/CD systems, use these commands:

```bash
# Install dependencies
npm ci

# Run linting
npm run lint

# Build for production
npm run build:production

# Test build
npm run preview &
# Run your tests here
```

## Maintenance

### Updates

```bash
# Update dependencies
npm update

# Check for security vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix
```

### Monitoring

- Monitor build times and sizes
- Track deployment success rates
- Monitor application performance metrics
- Review error logs regularly

## Support

For deployment issues:

1. Check this documentation
2. Review build logs
3. Test locally with `npm run preview:production`
4. Check platform-specific documentation
5. Contact development team
