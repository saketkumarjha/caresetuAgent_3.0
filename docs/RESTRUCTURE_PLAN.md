# Directory Restructuring Plan

## New Structure:

```
caresetuAgent/
├── README.md                           # Main project documentation
├── requirements.txt                    # Python dependencies
├── .env.example                       # Environment variables template
├── .env                              # Environment variables (gitignored)
├── .gitignore                        # Git ignore file
│
├── src/                              # Main source code
│   ├── __init__.py
│   ├── agent.py                      # Main voice agent
│   ├── config.py                     # Configuration management
│   └── core/                         # Core components
│       ├── __init__.py
│       ├── stt_config.py            # Speech-to-text configuration
│       ├── conversation_learning.py  # Learning engine
│       └── conversation_context.py   # Context management
│
├── integrations/                     # External service integrations
│   ├── __init__.py
│   ├── google_calendar_integration.py
│   ├── crm_integration.py
│   └── multi_tenant_support.py
│
├── knowledge/                        # Knowledge management system
│   ├── __init__.py
│   ├── engines/                      # RAG and search engines
│   │   ├── __init__.py
│   │   ├── simple_rag_engine.py
│   │   ├── semantic_search.py
│   │   └── domain_expertise.py
│   ├── processors/                   # Document processing
│   │   ├── __init__.py
│   │   ├── pdf_processor.py
│   │   ├── document_parsers.py
│   │   ├── document_type_detector.py
│   │   └── enhanced_document_processor.py
│   ├── storage/                      # Knowledge storage
│   │   ├── __init__.py
│   │   ├── unified_knowledge_base.py
│   │   ├── knowledge_indexer.py
│   │   ├── embedding_cache.py
│   │   └── cloud_vector_store.py
│   └── managers/                     # Knowledge management
│       ├── __init__.py
│       ├── company_document_manager.py
│       └── knowledge_base_semantic.py
│
├── data/                            # Data storage
│   ├── knowledge_base/              # JSON knowledge files
│   ├── unified_knowledge_base/      # Processed documents
│   ├── company_documents/           # Company documents
│   ├── company_pdfs/               # PDF files
│   ├── learned_knowledge/          # Learned information
│   ├── knowledge_index/            # Search indices
│   └── processed_documents/        # Processed documents
│
├── tests/                          # Test files
│   ├── __init__.py
│   ├── unit/                       # Unit tests
│   │   ├── test_agent.py
│   │   ├── test_calendar.py
│   │   └── test_rag.py
│   ├── integration/                # Integration tests
│   │   ├── test_complete_agent.py
│   │   ├── test_calendar_integration.py
│   │   └── test_rag_integration.py
│   └── diagnostics/                # Diagnostic tools
│       ├── email_diagnostics.py
│       ├── tts_diagnostics.py
│       └── check_appointments.py
│
├── scripts/                        # Utility scripts
│   ├── setup_calendar.py
│   ├── pdf_uploader.py
│   └── monitoring/
│       ├── pdf_file_monitor.py
│       └── demo_file_monitor.py
│
├── docs/                          # Documentation
│   ├── INSTALLATION_GUIDE.md
│   ├── GOOGLE_CALENDAR_SETUP.md
│   ├── PDF_UPLOAD_GUIDE.md
│   ├── AGENT_FRAMEWORK_README.md
│   ├── CARTESIA_TTS_INTEGRATION.md
│   ├── COMPANY_DOCUMENT_MANAGER_README.md
│   └── summaries/
│       ├── CALENDAR_INTEGRATION_SUMMARY.md
│       ├── TASK_2.1_IMPLEMENTATION_SUMMARY.md
│       ├── TASK_2.2_CRM_INTEGRATION_SUMMARY.md
│       └── TASK_6.1_RAG_INTEGRATION_SUMMARY.md
│
├── config/                        # Configuration files
│   ├── credentials.json          # Google credentials (gitignored)
│   └── token.json               # OAuth tokens (gitignored)
│
└── temp/                         # Temporary files (gitignored)
    ├── chroma_db/
    ├── troubleshooting_report.txt
    ├── tts_diagnostics_report.json
    └── test_cartesia_output.wav
```

## Files to be moved:

### Core Agent Files → src/

- agent.py (main)
- config.py
- stt_config.py → src/core/
- conversation_learning.py → src/core/
- conversation_context.py → src/core/

### Integration Files → integrations/

- google_calendar_integration.py
- crm_integration.py
- multi_tenant_support.py

### Knowledge System → knowledge/

- simple_rag_engine.py → knowledge/engines/
- semantic_search.py → knowledge/engines/
- domain_expertise.py → knowledge/engines/
- pdf_processor.py → knowledge/processors/
- document_parsers.py → knowledge/processors/
- document_type_detector.py → knowledge/processors/
- enhanced_document_processor.py → knowledge/processors/
- unified_knowledge_base.py → knowledge/storage/
- knowledge_indexer.py → knowledge/storage/
- embedding_cache.py → knowledge/storage/
- cloud_vector_store.py → knowledge/storage/
- company_document_manager.py → knowledge/managers/
- knowledge_base_semantic.py → knowledge/managers/

### Test Files → tests/

- All test\_\*.py files organized by category

### Documentation → docs/

- All \*.md files except README.md

### Scripts → scripts/

- setup_calendar.py
- caresetu_pdf_uploader.py → pdf_uploader.py
- pdf_file_monitor.py → scripts/monitoring/
- demo_file_monitor.py → scripts/monitoring/

### Configuration → config/

- credentials.json
- token.json

### Data Directories → data/

- All existing data directories moved under data/
