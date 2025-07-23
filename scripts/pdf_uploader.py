"""
careSetu PDF Upload Script
Uploads all company PDFs to ChromaDB Cloud for semantic search
"""

import asyncio
import logging
from pathlib import Path
from pdf_document_processor import PDFDocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def upload_caresetu_pdfs():
    """Upload all careSetu PDFs to ChromaDB Cloud."""
    
    print("🏥 careSetu PDF Upload to ChromaDB Cloud")
    print("=" * 60)
    
    try:
        # Initialize PDF processor for careSetu
        processor = PDFDocumentProcessor(
            company_id="caresetu",
            api_key='ck-8qMvVqpxS2ZPiA4rDDrPtT4Gjer1vawnCHNqANwqyxaF',
            tenant='952f5e15-854e-461e-83d1-3cef021c755c',
            database='Assembly_AI'
        )
        
        # Define careSetu PDF configuration
        pdf_configs = [
            {
                "path": "company_pdfs/Policies.pdf",
                "type": "policies",
                "title": "careSetu Policies and Terms",
                "tags": ["healthcare", "policy", "terms", "privacy", "compliance", "medical"]
            },
            {
                "path": "company_pdfs/procedures.pdf",
                "type": "procedures", 
                "title": "careSetu Medical Procedures",
                "tags": ["healthcare", "medical", "procedure", "workflow", "treatment", "clinical"]
            },
            {
                "path": "company_pdfs/faqs.pdf",
                "type": "faqs",
                "title": "careSetu Frequently Asked Questions",
                "tags": ["healthcare", "faq", "questions", "help", "support", "patient"]
            },
            {
                "path": "company_pdfs/manuals.pdf",
                "type": "manuals",
                "title": "careSetu User Manual and Guides",
                "tags": ["healthcare", "manual", "guide", "instructions", "patient", "user"]
            },
            {
                "path": "company_pdfs/general.pdf",
                "type": "general",
                "title": "careSetu Company Information",
                "tags": ["healthcare", "company", "about", "contact", "services", "medical"]
            }
        ]
        
        print(f"📋 Uploading {len(pdf_configs)} PDFs for careSetu...")
        
        # Check if all files exist
        missing_files = []
        for config in pdf_configs:
            if not Path(config["path"]).exists():
                missing_files.append(config["path"])
        
        if missing_files:
            print(f"❌ Missing PDF files:")
            for file in missing_files:
                print(f"  - {file}")
            print(f"\nPlease ensure all PDF files are in the company_pdfs/ directory")
            return False
        
        # Process all PDFs
        results = await processor.process_multiple_pdfs(pdf_configs)
        
        # Analyze results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"\n" + "=" * 60)
        print(f"📊 CARESETU PDF UPLOAD SUMMARY")
        print(f"=" * 60)
        
        if successful:
            print(f"✅ Successfully uploaded {len(successful)} PDFs:")
            total_chunks = 0
            for result in successful:
                print(f"  📄 {result.filename}")
                print(f"     Pages: {result.pages_processed}")
                print(f"     Chunks: {result.total_chunks}")
                print(f"     Time: {result.processing_time:.2f}s")
                total_chunks += result.total_chunks
            
            print(f"\n📈 Total chunks created: {total_chunks}")
        
        if failed:
            print(f"\n❌ Failed to upload {len(failed)} PDFs:")
            for result in failed:
                print(f"  📄 {result.filename}: {result.message}")
        
        if len(successful) == len(pdf_configs):
            print(f"\n🎉 ALL CARESETU PDFS UPLOADED SUCCESSFULLY!")
            print(f"\nYour careSetu voice agent now has access to:")
            print(f"✅ Company policies and terms")
            print(f"✅ Medical procedures and workflows") 
            print(f"✅ Patient FAQs and support information")
            print(f"✅ User manuals and guides")
            print(f"✅ Company information and services")
            
            print(f"\n🔍 ChromaDB Cloud Collections Created:")
            print(f"  - caresetu_policies")
            print(f"  - caresetu_procedures")
            print(f"  - caresetu_faqs")
            print(f"  - caresetu_manuals")
            print(f"  - caresetu_general")
            
            return True
        else:
            print(f"\n⚠️ Upload partially completed. Please check failed uploads above.")
            return False
            
    except Exception as e:
        print(f"❌ Error during careSetu PDF upload: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_caresetu_search():
    """Test search functionality with careSetu data."""
    
    print(f"\n" + "=" * 60)
    print(f"🔍 TESTING CARESETU SEARCH FUNCTIONALITY")
    print(f"=" * 60)
    
    try:
        from support_agent_enhanced import EnhancedSupportAgent
        
        # Initialize careSetu support agent
        agent = EnhancedSupportAgent(
            company_id="caresetu",
            api_key='ck-8qMvVqpxS2ZPiA4rDDrPtT4Gjer1vawnCHNqANwqyxaF',
            tenant='952f5e15-854e-461e-83d1-3cef021c755c',
            database='Assembly_AI'
        )
        
        await agent.initialize()
        print("✅ careSetu support agent initialized")
        
        # Test with healthcare-specific queries
        test_queries = [
            "What are your business hours?",
            "How do I schedule an appointment?", 
            "What is your cancellation policy?",
            "What medical services do you provide?",
            "How do I contact customer support?",
            "What are your privacy policies?",
            "Do you accept insurance?",
            "What should I bring to my appointment?"
        ]
        
        session_id = "caresetu_test_session"
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🤖 Query {i}: '{query}'")
            
            response = await agent.process_customer_query(
                query=query,
                session_id=session_id,
                customer_phone="555-123-4567"
            )
            
            print(f"  Response: {response.response[:200]}...")
            print(f"  Confidence: {response.confidence:.3f}")
            print(f"  Sources: {response.sources}")
            print(f"  Processing time: {response.processing_time:.3f}s")
            
            if response.escalation_needed:
                print(f"  ⚠️ Escalation needed: {response.escalation_reason}")
        
        print(f"\n✅ careSetu search testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing careSetu search: {e}")
        return False

async def main():
    """Main function to upload PDFs and test functionality."""
    
    print("🏥 careSetu Voice Agent Setup")
    print("=" * 80)
    
    # Step 1: Upload PDFs
    upload_success = await upload_caresetu_pdfs()
    
    if upload_success:
        # Step 2: Test search functionality
        test_success = await test_caresetu_search()
        
        if test_success:
            print(f"\n" + "=" * 80)
            print(f"🎉 CARESETU VOICE AGENT READY!")
            print(f"=" * 80)
            print(f"Your careSetu voice agent is now powered by:")
            print(f"✅ ChromaDB Cloud semantic search")
            print(f"✅ Your company's actual documents")
            print(f"✅ Healthcare-specific knowledge base")
            print(f"✅ Intelligent customer support")
            
            print(f"\n📞 Ready for customer queries like:")
            print(f"  • 'How do I schedule an appointment?'")
            print(f"  • 'What are your business hours?'")
            print(f"  • 'What services do you provide?'")
            print(f"  • 'What is your cancellation policy?'")
            
            print(f"\n🚀 Next step: Implement appointment scheduling!")
        else:
            print(f"\n⚠️ PDF upload successful but search testing failed.")
    else:
        print(f"\n❌ PDF upload failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())