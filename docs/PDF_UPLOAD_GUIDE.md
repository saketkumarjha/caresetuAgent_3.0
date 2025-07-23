# PDF Upload Guide for ChromaDB Cloud Integration

## 🗑️ Step 1: Clean Up Test Data

First, run the cleanup utility to remove all test data:

```bash
python cleanup_test_data.py
```

This will remove:

- All `test_company_*` collections from ChromaDB Cloud
- Local test files and directories
- Prepare your system for production data

## 📋 Step 2: Prepare Your 5 PDFs

You need to prepare 5 PDF documents according to these categories:

### 1. **Policies PDF**

**Collection**: `your_company_policies`
**Content Should Include**:

- Privacy Policy
- Terms of Service
- Data Protection Policy
- Refund/Return Policy
- Cancellation Policy
- Code of Conduct
- Compliance Guidelines
- Security Policies

**Example Structure**:

```
COMPANY POLICIES DOCUMENT

1. PRIVACY POLICY
   - How we collect personal information
   - How we use your data
   - Data sharing practices
   - Your privacy rights

2. TERMS OF SERVICE
   - Service agreement terms
   - User responsibilities
   - Limitation of liability
   - Termination conditions

3. CANCELLATION POLICY
   - How to cancel services
   - Cancellation fees
   - Refund procedures
   - Emergency cancellations
```

### 2. **Procedures PDF**

**Collection**: `your_company_procedures`
**Content Should Include**:

- Appointment Booking Procedures
- Customer Onboarding Process
- Payment Processing Steps
- Complaint Resolution Workflow
- Emergency Procedures
- Quality Assurance Steps

**Example Structure**:

```
OPERATIONAL PROCEDURES

1. APPOINTMENT BOOKING
   Step 1: Customer calls or uses online system
   Step 2: Check availability in calendar
   Step 3: Confirm appointment details
   Step 4: Send confirmation

2. CUSTOMER ONBOARDING
   Step 1: Welcome new customer
   Step 2: Collect required information
   Step 3: Set up account
   Step 4: Provide orientation
```

### 3. **FAQs PDF**

**Collection**: `your_company_faqs`
**Content Should Include**:

- General Questions
- Service-Related FAQs
- Billing & Payment FAQs
- Technical Support FAQs
- Account Management FAQs

**Example Structure**:

```
FREQUENTLY ASKED QUESTIONS

GENERAL QUESTIONS
Q: What are your business hours?
A: We are open Monday-Friday 9AM-5PM, Saturday 10AM-2PM, closed Sunday.

Q: How do I contact customer support?
A: You can call us at (555) 123-4567 or email support@company.com

APPOINTMENT QUESTIONS
Q: How do I schedule an appointment?
A: You can schedule online at our website or call our office.

Q: Can I reschedule my appointment?
A: Yes, please give us at least 24 hours notice.
```

### 4. **Manuals PDF**

**Collection**: `your_company_manuals`
**Content Should Include**:

- User Manual/Guide
- Service Instructions
- Product Documentation
- System Usage Guide
- Training Materials

**Example Structure**:

```
USER MANUAL

GETTING STARTED
- Account setup instructions
- First-time user guide
- System requirements

USING OUR SERVICES
- How to book appointments
- How to make payments
- How to access your account

TROUBLESHOOTING
- Common issues and solutions
- Error message explanations
- When to contact support
```

### 5. **General PDF**

**Collection**: `your_company_general`
**Content Should Include**:

- Company Overview
- Mission & Values
- Service Descriptions
- Contact Information
- Business Hours
- Location Details

**Example Structure**:

```
COMPANY INFORMATION

ABOUT US
- Company history and mission
- Our values and commitment
- Team information

SERVICES WE OFFER
- Service descriptions
- Pricing information
- Service areas

CONTACT INFORMATION
- Office locations
- Phone numbers
- Email addresses
- Business hours
```

## 🔧 Step 3: Install PDF Processing Libraries

Install required libraries for PDF processing:

```bash
pip install PyPDF2
# OR
pip install pdfplumber
```

## 📤 Step 4: Upload Your PDFs

### Option A: Upload Individual PDFs

```python
from pdf_document_processor import PDFDocumentProcessor

# Initialize processor with your company ID
processor = PDFDocumentProcessor(
    company_id="careSetu",  # Replace with your actual company name
    api_key='ck-8qMvVqpxS2ZPiA4rDDrPtT4Gjer1vawnCHNqANwqyxaF',
    tenant='952f5e15-854e-461e-83d1-3cef021c755c',
    database='Assembly_AI'
)

# Upload each PDF
result = await processor.process_pdf(
    pdf_path="path/to/your/policies.pdf",
    pdf_type="policies",
    custom_title="Company Policies and Terms",
    additional_tags=["legal", "compliance"]
)

print(f"Success: {result.success}")
print(f"Chunks created: {result.total_chunks}")
```

### Option B: Batch Upload All PDFs

```python
# Configure all your PDFs
pdf_configs = [
    {
        "path": "path/to/policies.pdf",
        "type": "policies",
        "title": "Company Policies and Terms",
        "tags": ["legal", "compliance", "terms"]
    },
    {
        "path": "path/to/procedures.pdf",
        "type": "procedures",
        "title": "Operational Procedures",
        "tags": ["operations", "workflow", "process"]
    },
    {
        "path": "path/to/faqs.pdf",
        "type": "faqs",
        "title": "Frequently Asked Questions",
        "tags": ["help", "support", "questions"]
    },
    {
        "path": "path/to/manuals.pdf",
        "type": "manuals",
        "title": "User Manual and Guides",
        "tags": ["manual", "instructions", "guide"]
    },
    {
        "path": "path/to/general.pdf",
        "type": "general",
        "title": "Company Information",
        "tags": ["company", "about", "contact"]
    }
]

# Process all PDFs
results = await processor.process_multiple_pdfs(pdf_configs)

# Check results
for result in results:
    print(f"{result.filename}: {'✅' if result.success else '❌'} {result.message}")
```

## 🧪 Step 5: Test Your Upload

Create a simple test script:

```python
import asyncio
from pdf_document_processor import PDFDocumentProcessor

async def upload_my_pdfs():
    processor = PDFDocumentProcessor(
        company_id="your_company_name",  # Your company name
        api_key='ck-8qMvVqpxS2ZPiA4rDDrPtT4Gjer1vawnCHNqANwqyxaF',
        tenant='952f5e15-854e-461e-83d1-3cef021c755c',
        database='Assembly_AI'
    )

    # Upload your first PDF as a test
    result = await processor.process_pdf(
        pdf_path="your_policies.pdf",  # Replace with actual path
        pdf_type="policies"
    )

    if result.success:
        print(f"✅ Success! Created {result.total_chunks} chunks")
    else:
        print(f"❌ Failed: {result.message}")

# Run the test
asyncio.run(upload_my_pdfs())
```

## 🔍 Step 6: Test Search Functionality

After uploading, test the search:

```python
from support_agent_enhanced import EnhancedSupportAgent

async def test_search():
    agent = EnhancedSupportAgent(
        company_id="your_company_name",
        api_key='ck-8qMvVqpxS2ZPiA4rDDrPtT4Gjer1vawnCHNqANwqyxaF',
        tenant='952f5e15-854e-461e-83d1-3cef021c755c',
        database='Assembly_AI'
    )

    await agent.initialize()

    # Test with real customer queries
    response = await agent.process_customer_query(
        query="How do I cancel my appointment?",
        session_id="test_session"
    )

    print(f"Response: {response.response}")
    print(f"Confidence: {response.confidence}")
    print(f"Sources: {response.sources}")

asyncio.run(test_search())
```

## 📊 Expected Results

After successful upload, you should see:

1. **ChromaDB Cloud Collections**:

   - `your_company_policies`
   - `your_company_procedures`
   - `your_company_faqs`
   - `your_company_manuals`
   - `your_company_general`

2. **Search Capabilities**:

   - Semantic search across all documents
   - Relevant answers to customer queries
   - Source attribution for responses

3. **Performance**:
   - Fast vector similarity search
   - Accurate document retrieval
   - Context-aware responses

## 🚨 Important Notes

1. **Company ID**: Replace `"your_company_name"` with your actual company identifier
2. **File Paths**: Use absolute paths to your PDF files
3. **PDF Quality**: Ensure PDFs contain searchable text (not just images)
4. **Content Organization**: Structure your PDFs with clear headings and sections
5. **Testing**: Test with real customer queries after upload

## 🆘 Troubleshooting

**PDF Not Processing**:

- Check if PDF contains searchable text
- Verify file path is correct
- Ensure PDF libraries are installed

**No Search Results**:

- Verify documents were uploaded successfully
- Check if query matches document content
- Try different search terms

**Connection Issues**:

- Verify ChromaDB Cloud credentials
- Check internet connection
- Ensure API limits aren't exceeded

Once you have your 5 PDFs ready, just let me know and I'll help you upload them!
