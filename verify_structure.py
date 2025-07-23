#!/usr/bin/env python3
"""
Verification script to ensure all files are in their proper directories
"""

import os
import sys

def check_directory_structure():
    """Check if all required directories and files exist"""
    
    required_structure = {
        'src/': ['agent.py', 'config.py', '__init__.py'],
        'src/core/': ['stt_config.py', 'conversation_learning.py', 'conversation_context.py', '__init__.py'],
        'integrations/': ['google_calendar_integration.py', 'crm_integration.py', 'multi_tenant_support.py', '__init__.py'],
        'knowledge/engines/': ['simple_rag_engine.py', 'semantic_search.py', 'domain_expertise.py', '__init__.py'],
        'knowledge/processors/': ['pdf_processor.py', 'document_parsers.py', 'document_type_detector.py', '__init__.py'],
        'knowledge/storage/': ['unified_knowledge_base.py', 'knowledge_indexer.py', 'embedding_cache.py', '__init__.py'],
        'knowledge/managers/': ['company_document_manager.py', 'knowledge_base_semantic.py', '__init__.py'],
        'tests/': ['__init__.py'],
        'tests/diagnostics/': ['email_diagnostics.py', 'check_appointments.py', 'tts_diagnostics.py'],
        'scripts/': ['setup_calendar.py', 'pdf_uploader.py'],
        'scripts/monitoring/': ['pdf_file_monitor.py', 'demo_file_monitor.py'],
        'config/': ['credentials.json', 'token.json'],
        'docs/': ['INSTALLATION_GUIDE.md', 'GOOGLE_CALENDAR_SETUP.md', 'README.md'],
        './': ['main.py', 'README.md', 'requirements.txt', '.env.example', '.gitignore']
    }
    
    print("🔍 Verifying CareSetu Voice Agent Directory Structure...")
    print("=" * 60)
    
    all_good = True
    
    for directory, files in required_structure.items():
        print(f"\n📂 Checking {directory}")
        
        if not os.path.exists(directory):
            print(f"❌ Directory {directory} does not exist!")
            all_good = False
            continue
            
        for file in files:
            file_path = os.path.join(directory, file)
            if os.path.exists(file_path):
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file} - MISSING")
                all_good = False
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("🎉 SUCCESS! All files are in their proper directories!")
        print("🚀 Your project is ready for GitHub!")
        return True
    else:
        print("⚠️  Some files are missing or misplaced.")
        print("📋 Please check the missing files above.")
        return False

def check_import_paths():
    """Check if import paths in main files are correct"""
    print("\n🔍 Checking import paths...")
    
    # Check main.py
    if os.path.exists('main.py'):
        with open('main.py', 'r') as f:
            content = f.read()
            if 'from src.agent import main' in content or 'sys.path' in content:
                print("  ✅ main.py import paths look good")
            else:
                print("  ⚠️  main.py might need import path fixes")
    
    # Check src/agent.py
    if os.path.exists('src/agent.py'):
        with open('src/agent.py', 'r') as f:
            content = f.read()
            if 'sys.path.append' in content or 'from config import' in content:
                print("  ✅ src/agent.py import paths configured")
            else:
                print("  ⚠️  src/agent.py might need import path fixes")

def main():
    """Main verification function"""
    print("🎯 CareSetu Voice Agent - Structure Verification")
    print("=" * 60)
    
    structure_ok = check_directory_structure()
    check_import_paths()
    
    print("\n" + "=" * 60)
    
    if structure_ok:
        print("✅ VERIFICATION COMPLETE - Ready for GitHub! 🌟")
        print("\n📤 Next steps:")
        print("1. Test the application: python main.py")
        print("2. Run diagnostics: python tests/diagnostics/email_diagnostics.py")
        print("3. Commit to GitHub: git add . && git commit -m 'Restructure project' && git push")
    else:
        print("❌ VERIFICATION FAILED - Please fix missing files")
    
    return structure_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)