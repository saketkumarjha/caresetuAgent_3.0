"""
careSetu Knowledge Integration
Enhances the support agent with specific careSetu knowledge
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

from knowledge_base_chromadb_cloud import CloudKnowledgeBaseConnector, KnowledgeDocument

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CareSetuKnowledgeEnhancer:
    """
    Enhances the careSetu knowledge base with specific information
    extracted from PDFs and structured for better retrieval.
    """
    
    def __init__(self, 
                 api_key: str = 'ck-8qMvVqpxS2ZPiA4rDDrPtT4Gjer1vawnCHNqANwqyxaF',
                 tenant: str = '952f5e15-854e-461e-83d1-3cef021c755c',
                 database: str = 'Assembly_AI'):
        """Initialize the knowledge enhancer."""
        self.api_key = api_key
        self.tenant = tenant
        self.database = database
        
        # Initialize knowledge base connector
        self.kb = CloudKnowledgeBaseConnector(
            company_id="caresetu",
            api_key=api_key,
            tenant=tenant,
            database=database
        )
    
    async def enhance_knowledge_base(self):
        """Enhance the knowledge base with structured careSetu information."""
        logger.info("🔄 Enhancing careSetu knowledge base...")
        
        # Load existing knowledge base
        await self.kb.load_knowledge_base()
        
        # Add structured FAQ documents
        await self._add_structured_faqs()
        
        # Add structured procedures
        await self._add_structured_procedures()
        
        # Add business information
        await self._add_business_information()
        
        # Add service information
        await self._add_service_information()
        
        logger.info("✅ careSetu knowledge base enhancement completed")
    
    async def _add_structured_faqs(self):
        """Add structured FAQ documents for better retrieval."""
        faqs = [
            {
                "question": "Who can use the CareSetu App?",
                "answer": "Any adult above 18 years old. Minors must be added under a Primary User account.",
                "category": "registration"
            },
            {
                "question": "Can I browse without registering?",
                "answer": "Yes. Non-registered users can browse, use the self-assessment tool, and share the app.",
                "category": "registration"
            },
            {
                "question": "What services does CareSetu offer?",
                "answer": "Services include online consultation, lab/sample collection, drug delivery, home therapies, post-surgery care, and more.",
                "category": "services"
            },
            {
                "question": "Is my personal and medical data safe?",
                "answer": "Yes. Data is encrypted and stored securely following privacy regulations.",
                "category": "privacy"
            },
            {
                "question": "How do I schedule an appointment?",
                "answer": "Log in to the CareSetu App, choose a service (consultation, diagnostics, etc.), select a Healthcare Service Provider, and confirm your appointment.",
                "category": "appointments"
            },
            {
                "question": "What are your business hours?",
                "answer": "Our digital platform is available 24/7. Healthcare Service Provider hours vary by provider and can be viewed in the app.",
                "category": "general"
            },
            {
                "question": "How do I contact customer support?",
                "answer": "You can contact our support team at saket@jha.com or through the Help section in the CareSetu App.",
                "category": "support"
            },
            {
                "question": "What is your cancellation policy?",
                "answer": "Cancellation policies vary by Healthcare Service Provider. Generally, cancellations should be made at least 4 hours before the appointment to avoid cancellation fees.",
                "category": "appointments"
            }
        ]
        
        for i, faq in enumerate(faqs):
            doc_id = f"caresetu_faq_{i+1}"
            
            # Create document
            doc = KnowledgeDocument(
                id=doc_id,
                title=f"FAQ: {faq['question']}",
                content=f"Question: {faq['question']}\nAnswer: {faq['answer']}",
                category="faqs",
                tags=["faq", faq["category"], "question", "answer", "support"],
                company_id="caresetu"
            )
            
            # Add to knowledge base
            await self.kb.add_document(doc)
            logger.info(f"✅ Added FAQ document: {doc.title}")
    
    async def _add_structured_procedures(self):
        """Add structured procedure documents."""
        procedures = [
            {
                "title": "Registration Process",
                "content": """
                Registration Process for CareSetu:
                1. Download and install the CareSetu App from Play Store or App Store.
                2. Register as a Primary User (must be an adult, 18+).
                3. Add Secondary Users if needed (for family members).
                4. HSP Registered Users are assigned a UHID/UMR.
                """,
                "category": "registration"
            },
            {
                "title": "Booking Appointments",
                "content": """
                How to Book Appointments on CareSetu:
                1. Log in using your credentials.
                2. Choose service: consultation, diagnostics, medicine delivery, etc.
                3. Select a Healthcare Service Provider (HSP).
                4. Choose available date and time slot.
                5. Confirm appointment and make payment if necessary.
                """,
                "category": "appointments"
            },
            {
                "title": "Uploading Prescriptions",
                "content": """
                How to Upload Prescriptions on CareSetu:
                1. Navigate to Health Records section.
                2. Select "Upload Prescription" option.
                3. Take a photo or upload an existing image of your prescription.
                4. Add relevant details like doctor name and date.
                5. Submit for processing.
                """,
                "category": "records"
            },
            {
                "title": "Cancellation Process",
                "content": """
                How to Cancel Appointments on CareSetu:
                1. Go to the Bookings section in the app.
                2. Find the appointment you wish to cancel.
                3. Select the cancel option.
                4. Provide a reason for cancellation if prompted.
                5. Confirm cancellation.
                
                Note: Cancellations should be made at least 4 hours before the appointment to avoid cancellation fees.
                """,
                "category": "appointments"
            }
        ]
        
        for i, procedure in enumerate(procedures):
            doc_id = f"caresetu_procedure_{i+1}"
            
            # Create document
            doc = KnowledgeDocument(
                id=doc_id,
                title=procedure["title"],
                content=procedure["content"],
                category="procedures",
                tags=["procedure", procedure["category"], "workflow", "steps", "guide"],
                company_id="caresetu"
            )
            
            # Add to knowledge base
            await self.kb.add_document(doc)
            logger.info(f"✅ Added procedure document: {doc.title}")
    
    async def _add_business_information(self):
        """Add business information documents."""
        business_info = {
            "title": "CareSetu Business Information",
            "content": """
            CareSetu - Business Information
            
            Company Details:
            - Operated by: Akhil Systems Private Limited (ASPL)
            - Registered Office: #205-206, Vardhman Times Plaza, Plot No. 13, Rd No. 44,
              Pitampura Commercial Complex, New Delhi - 110034
            - Contact: saket@jha.com
            
            Business Hours:
            - Digital Platform: Available 24/7
            - Customer Support: Monday to Friday, 9:00 AM to 6:00 PM
            - Healthcare Service Provider hours vary by provider
            
            Contact Information:
            - Email: saket@jha.com
            - Website: www.caresetu.com
            - App: Available on Play Store and App Store
            """,
            "category": "general",
            "tags": ["business", "hours", "contact", "company", "information"]
        }
        
        # Create document
        doc = KnowledgeDocument(
            id="caresetu_business_info",
            title=business_info["title"],
            content=business_info["content"],
            category="general",
            tags=business_info["tags"],
            company_id="caresetu"
        )
        
        # Add to knowledge base
        await self.kb.add_document(doc)
        logger.info(f"✅ Added business information document: {doc.title}")
    
    async def _add_service_information(self):
        """Add service information documents."""
        services = {
            "title": "CareSetu Services",
            "content": """
            CareSetu Services
            
            Healthcare Services Available:
            1. Online Consultations - Connect with doctors virtually
            2. Lab/Diagnostic Services - Book tests and sample collection
            3. Medicine Delivery - Order prescriptions for home delivery
            4. Home Healthcare - Therapies and care at your home
            5. Post-Surgery Care - Recovery support and follow-ups
            
            How to Access Services:
            - Download the CareSetu App
            - Register as a user
            - Browse and select the service you need
            - Choose a healthcare provider
            - Book appointment or service
            - Make payment if required
            
            Service Hours:
            Digital platform is available 24/7, but actual service hours depend on the healthcare provider's availability.
            """,
            "category": "services",
            "tags": ["services", "healthcare", "consultation", "diagnostics", "medicine", "delivery"]
        }
        
        # Create document
        doc = KnowledgeDocument(
            id="caresetu_services",
            title=services["title"],
            content=services["content"],
            category="general",
            tags=services["tags"],
            company_id="caresetu"
        )
        
        # Add to knowledge base
        await self.kb.add_document(doc)
        logger.info(f"✅ Added services information document: {doc.title}")

async def main():
    """Main function to enhance careSetu knowledge base."""
    print("🏥 careSetu Knowledge Enhancement")
    print("=" * 60)
    
    enhancer = CareSetuKnowledgeEnhancer()
    await enhancer.enhance_knowledge_base()
    
    print("✅ Knowledge base enhancement completed!")
    print("\nYour careSetu support agent now has enhanced knowledge about:")
    print("  • Registration and account procedures")
    print("  • Appointment booking and cancellation")
    print("  • Business hours and contact information")
    print("  • Available healthcare services")
    print("  • Frequently asked questions")
    
    print("\nTry testing the support agent again with specific questions!")

if __name__ == "__main__":
    asyncio.run(main())