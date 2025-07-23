# Company Document Management System

## Overview

The Company Document Management System is a comprehensive solution for handling company-specific documents, particularly privacy policies and appointment guides. It provides automated document processing, categorization, validation, and policy extraction capabilities, enabling the voice agent to access and utilize company-specific information during customer interactions.

## Key Features

- **Document Upload and Processing**: Handles document upload and asynchronous processing with error recovery
- **Automatic Document Categorization**: Identifies document types based on content analysis
- **Document Validation**: Validates documents against type-specific rules to ensure quality
- **Policy Extraction**: Extracts structured data from documents (business hours, cancellation policies, etc.)
- **Vector-Based Search**: Enables semantic search across company documents
- **Multi-Tenant Support**: Isolates documents by company ID for security and privacy

## Architecture

The system consists of the following components:

1. **CompanyDocumentManager**: Main class that orchestrates document processing
2. **DocumentProcessor**: Handles text extraction and chunking
3. **VectorStore**: Manages vector embeddings and search functionality
4. **EmbeddingCache**: Caches embeddings for improved performance

## Document Categories

The system supports various document categories:

- **Privacy Policy**: Contains data collection, usage, and protection information
- **Appointment Guide**: Contains booking, cancellation, and scheduling information
- **Terms of Service**: Contains legal terms and conditions
- **FAQ**: Contains frequently asked questions and answers
- **General**: Default category for unclassified documents

## Policy Extraction

The system extracts structured data from documents based on their category:

### Appointment Guide Policies

- Business hours
- Cancellation policy
- Appointment booking methods
- Notice period requirements
- Cancellation fees

### Privacy Policy Information

- Data retention periods
- Data collection purposes
- Data sharing policies

## Usage

### Initializing the System

```python
# Initialize document processor
document_processor = DocumentProcessor(output_dir="processed_documents")
await document_processor.start_processing()

# Initialize vector store
vector_store = VectorStore(persist_directory="chroma_db")

# Initialize company document manager
document_manager = CompanyDocumentManager(
    document_processor=document_processor,
    vector_store=vector_store,
    output_dir="company_documents",
    embedding_cache_dir="embedding_cache"
)
await document_manager.start_processing()
```

### Uploading Documents

```python
# Upload a document
result = await document_manager.upload_document(
    document_path="privacy_policy.pdf",
    company_id="acme_corp",
    document_type="privacy_policy",  # Optional, will be auto-detected if not provided
    metadata={"author": "Legal Team", "version": "1.2"}  # Optional
)

doc_id = result["doc_id"]
```

### Checking Processing Status

```python
# Check processing status
status = await document_manager.get_processing_status(doc_id)
print(f"Status: {status}")

# Get processing results
results = await document_manager.get_processing_results(doc_id)
print(f"Results: {results}")
```

### Searching Documents

```python
# Search company documents
search_results = await document_manager.search_company_documents(
    company_id="acme_corp",
    query="cancellation policy",
    document_type="appointment_guide",  # Optional
    max_results=5
)

for result in search_results:
    print(f"Content: {result['content']}")
    print(f"Score: {result['relevance_score']}")
    print(f"Metadata: {result['metadata']}")
```

### Listing Company Documents

```python
# Get all documents for a company
documents = await document_manager.get_company_documents("acme_corp")

for doc in documents:
    print(f"Document ID: {doc['doc_id']}")
    print(f"Title: {doc['title']}")
    print(f"Type: {doc['document_type']}")
    print(f"Validation: {doc['validation_result']}")
    print(f"Extracted Policies: {doc['extracted_policies']}")
```

## Integration with Voice Agent

The Company Document Management System integrates with the voice agent through:

1. **Knowledge Base Integration**: Company documents are indexed and made available for RAG
2. **Policy-Aware Responses**: Extracted policies are used to provide accurate information
3. **Context-Aware Search**: Customer queries are matched to relevant company documents

## Testing

Run the comprehensive test script to verify functionality:

```bash
python test_company_document_manager.py
```

The test script validates:

- Document upload and processing
- Document categorization and validation
- Policy extraction and structured data generation
- Document search with vector-based tagging
- Company documents listing

## Future Enhancements

- Support for more document formats (PDF, DOCX, HTML)
- Advanced semantic chunking for improved search relevance
- Document versioning and update tracking
- Automated policy conflict detection
- Enhanced multi-language support
