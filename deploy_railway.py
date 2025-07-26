#!/usr/bin/env python3
"""
Railway Deployment Script
Automated deployment to Railway cloud platform
"""

import os
import sys
import subprocess
import json
from typing import Dict, List

class RailwayDeployer:
    """Railway deployment automation."""
    
    def __init__(self):
        self.required_env_vars = [
            'LIVEKIT_URL',
            'LIVEKIT_API_KEY', 
            'LIVEKIT_API_SECRET',
            'ASSEMBLYAI_API_KEY',
            'GOOGLE_API_KEY'
        ]
    
    def check_railway_cli(self) -> bool:
        """Check if Railway CLI is installed."""
        try:
            result = subprocess.run(['railway', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Railway CLI found: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        print("❌ Railway CLI not found")
        print("Install with: npm install -g @railway/cli")
        return False
    
    def check_git_status(self) -> bool:
        """Check if git repo is clean and up to date."""
        try:
            # Check if we're in a git repo
            subprocess.run(['git', 'status'], 
                          capture_output=True, check=True)
            
            # Check for uncommitted changes
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip():
                print("⚠️  Uncommitted changes found:")
                print(result.stdout)
                response = input("Commit changes? (y/n): ")
                if response.lower() == 'y':
                    self.commit_changes()
                else:
                    print("❌ Please commit changes before deploying")
                    return False
            
            print("✅ Git repository is clean")
            return True
            
        except subprocess.CalledProcessError:
            print("❌ Not in a git repository")
            return False
    
    def commit_changes(self):
        """Commit current changes."""
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Railway deployment update'], 
                          check=True)
            print("✅ Changes committed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to commit changes: {e}")
    
    def check_env_vars(self) -> Dict[str, str]:
        """Check for required environment variables."""
        env_vars = {}
        missing = []
        
        for var in self.required_env_vars:
            value = os.getenv(var)
            if value:
                env_vars[var] = value
                print(f"✅ {var}: {'*' * (len(value) - 4)}{value[-4:]}")
            else:
                missing.append(var)
                print(f"❌ {var}: Not set")
        
        if missing:
            print(f"\n❌ Missing environment variables: {', '.join(missing)}")
            print("Set them locally or they'll be configured in Railway dashboard")
        
        return env_vars
    
    def railway_login(self) -> bool:
        """Login to Railway."""
        try:
            result = subprocess.run(['railway', 'whoami'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Already logged in: {result.stdout.strip()}")
                return True
        except:
            pass
        
        print("🔐 Logging into Railway...")
        try:
            subprocess.run(['railway', 'login'], check=True)
            print("✅ Railway login successful")
            return True
        except subprocess.CalledProcessError:
            print("❌ Railway login failed")
            return False
    
    def create_or_connect_project(self) -> bool:
        """Create new project or connect to existing."""
        try:
            # Check if already connected
            result = subprocess.run(['railway', 'status'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and 'Project:' in result.stdout:
                print("✅ Already connected to Railway project")
                return True
        except:
            pass
        
        print("🚀 Setting up Railway project...")
        
        choice = input("Create new project or connect existing? (new/existing): ")
        
        if choice.lower() == 'new':
            project_name = input("Project name (or press Enter for auto): ").strip()
            cmd = ['railway', 'init']
            if project_name:
                cmd.extend(['--name', project_name])
            
            try:
                subprocess.run(cmd, check=True)
                print("✅ New Railway project created")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to create Railway project")
                return False
        
        else:
            try:
                subprocess.run(['railway', 'link'], check=True)
                print("✅ Connected to existing Railway project")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to connect to Railway project")
                return False
    
    def set_environment_variables(self, env_vars: Dict[str, str]):
        """Set environment variables in Railway."""
        if not env_vars:
            print("⚠️  No environment variables to set")
            return
        
        print("🔧 Setting environment variables in Railway...")
        
        for var, value in env_vars.items():
            try:
                subprocess.run(['railway', 'variables', 'set', f'{var}={value}'], 
                              check=True, capture_output=True)
                print(f"✅ Set {var}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to set {var}")
    
    def deploy(self) -> bool:
        """Deploy to Railway."""
        print("🚀 Deploying to Railway...")
        
        try:
            # Deploy using railway up
            result = subprocess.run(['railway', 'up'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Deployment successful!")
                print(result.stdout)
                
                # Try to get the URL
                try:
                    url_result = subprocess.run(['railway', 'domain'], 
                                              capture_output=True, text=True)
                    if url_result.returncode == 0 and url_result.stdout.strip():
                        print(f"🌐 Your app is available at: {url_result.stdout.strip()}")
                except:
                    pass
                
                return True
            else:
                print("❌ Deployment failed!")
                print(result.stderr)
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment failed: {e}")
            return False
    
    def open_dashboard(self):
        """Open Railway dashboard."""
        try:
            subprocess.run(['railway', 'open'], check=True)
            print("🌐 Opening Railway dashboard...")
        except subprocess.CalledProcessError:
            print("❌ Failed to open Railway dashboard")
    
    def run_deployment(self):
        """Run complete deployment process."""
        print("🚂 Railway Deployment Script")
        print("=" * 40)
        
        # Check prerequisites
        if not self.check_railway_cli():
            return False
        
        if not self.check_git_status():
            return False
        
        # Check environment variables
        env_vars = self.check_env_vars()
        
        # Railway operations
        if not self.railway_login():
            return False
        
        if not self.create_or_connect_project():
            return False
        
        # Set environment variables if available
        if env_vars:
            self.set_environment_variables(env_vars)
        
        # Deploy
        if self.deploy():
            print("\n🎉 Deployment completed successfully!")
            
            open_dashboard = input("Open Railway dashboard? (y/n): ")
            if open_dashboard.lower() == 'y':
                self.open_dashboard()
            
            return True
        else:
            print("\n❌ Deployment failed!")
            return False

def main():
    """Main deployment function."""
    deployer = RailwayDeployer()
    success = deployer.run_deployment()
    
    if success:
        print("\n✅ Your CareSetu Voice Agent is now running on Railway!")
        print("📊 Monitor your deployment in the Railway dashboard")
        print("🔍 Check logs for any issues")
        print("🌐 Test your health endpoint: https://your-app.railway.app/health")
    else:
        print("\n❌ Deployment failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()