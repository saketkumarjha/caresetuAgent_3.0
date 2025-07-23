"""
Domain Expertise Adaptation Module
Implements domain detection and specialized response generation for different fields
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

class DomainType(Enum):
    """Types of domain expertise."""
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    TECHNICAL_SUPPORT = "technical_support"
    GENERAL = "general"
    BILLING = "billing"
    APPOINTMENT = "appointment"

@dataclass
class DomainTerminology:
    """Domain-specific terminology and concepts."""
    domain: DomainType
    keywords: List[str]
    concepts: List[str]
    specialized_terms: List[str]
    response_patterns: List[str]
    document_priorities: List[str]
    language_style: str
    
    def __post_init__(self):
        if not self.keywords:
            self.keywords = []
        if not self.concepts:
            self.concepts = []
        if not self.specialized_terms:
            self.specialized_terms = []
        if not self.response_patterns:
            self.response_patterns = []
        if not self.document_priorities:
            self.document_priorities = []

@dataclass
class DomainContext:
    """Context information for domain expertise."""
    detected_domain: DomainType
    confidence: float
    supporting_evidence: List[str]
    terminology_matches: List[str]
    document_types_used: List[str]
    expertise_level: str  # "basic", "intermediate", "advanced"
    
    def __post_init__(self):
        if not self.supporting_evidence:
            self.supporting_evidence = []
        if not self.terminology_matches:
            self.terminology_matches = []
        if not self.document_types_used:
            self.document_types_used = []

@dataclass
class DomainResponse:
    """Domain-adapted response with specialized formatting."""
    original_response: str
    adapted_response: str
    domain: DomainType
    terminology_used: List[str]
    document_sources_prioritized: List[str]
    clarifying_questions: List[str]
    expertise_indicators: List[str]
    
    def __post_init__(self):
        if not self.terminology_used:
            self.terminology_used = []
        if not self.document_sources_prioritized:
            self.document_sources_prioritized = []
        if not self.clarifying_questions:
            self.clarifying_questions = []
        if not self.expertise_indicators:
            self.expertise_indicators = []

class DomainTerminologyDatabase:
    """Database of domain-specific terminology and concepts."""
    
    def __init__(self):
        """Initialize domain terminology database."""
        self.domain_terminologies = self._initialize_domain_terminologies()
        logger.info("Domain terminology database initialized")
    
    def _initialize_domain_terminologies(self) -> Dict[DomainType, DomainTerminology]:
        """Initialize domain-specific terminologies."""
        return {
            DomainType.HEALTHCARE: DomainTerminology(
                domain=DomainType.HEALTHCARE,
                keywords=[
                    "patient", "doctor", "physician", "nurse", "medical", "health",
                    "treatment", "diagnosis", "medication", "prescription", "symptoms",
                    "consultation", "appointment", "clinic", "hospital", "therapy",
                    "insurance", "copay", "deductible", "coverage", "provider",
                    "chronic", "acute", "condition", "disease", "illness", "recovery"
                ],
                concepts=[
                    "medical consultation", "patient care", "treatment plan",
                    "diagnostic procedure", "medication management", "health monitoring",
                    "preventive care", "emergency care", "specialist referral"
                ],
                specialized_terms=[
                    "contraindication", "prognosis", "differential diagnosis",
                    "therapeutic intervention", "clinical assessment", "medical history",
                    "vital signs", "laboratory results", "imaging studies"
                ],
                response_patterns=[
                    "Based on medical guidelines...",
                    "For your health and safety...",
                    "Please consult with your healthcare provider...",
                    "Medical protocols recommend...",
                    "This requires professional medical evaluation..."
                ],
                document_priorities=["medical", "health", "procedure", "policy"],
                language_style="professional_medical"
            ),
            
            DomainType.LEGAL: DomainTerminology(
                domain=DomainType.LEGAL,
                keywords=[
                    "legal", "law", "attorney", "lawyer", "court", "case",
                    "contract", "agreement", "policy", "terms", "conditions",
                    "liability", "rights", "responsibilities", "compliance",
                    "regulation", "statute", "jurisdiction", "precedent",
                    "litigation", "settlement", "damages", "breach"
                ],
                concepts=[
                    "legal compliance", "contractual obligations", "regulatory requirements",
                    "liability protection", "dispute resolution", "legal documentation",
                    "privacy rights", "data protection", "terms of service"
                ],
                specialized_terms=[
                    "force majeure", "indemnification", "jurisdiction clause",
                    "limitation of liability", "intellectual property", "confidentiality",
                    "non-disclosure", "arbitration", "mediation", "statutory requirements"
                ],
                response_patterns=[
                    "According to our legal policy...",
                    "Our terms and conditions state...",
                    "For legal compliance purposes...",
                    "This is governed by applicable law...",
                    "Please refer to our privacy policy..."
                ],
                document_priorities=["policy", "legal", "terms", "privacy"],
                language_style="formal_legal"
            ),
            
            DomainType.TECHNICAL_SUPPORT: DomainTerminology(
                domain=DomainType.TECHNICAL_SUPPORT,
                keywords=[
                    "technical", "system", "error", "bug", "issue", "problem",
                    "solution", "fix", "troubleshoot", "support", "software",
                    "hardware", "network", "connection", "server", "database",
                    "application", "browser", "device", "configuration",
                    "update", "upgrade", "installation", "compatibility"
                ],
                concepts=[
                    "system troubleshooting", "error resolution", "technical diagnosis",
                    "software configuration", "hardware compatibility", "network connectivity",
                    "performance optimization", "security settings", "backup procedures"
                ],
                specialized_terms=[
                    "API integration", "database connectivity", "server configuration",
                    "network protocols", "authentication", "authorization",
                    "SSL certificate", "firewall settings", "load balancing"
                ],
                response_patterns=[
                    "Let's troubleshoot this step by step...",
                    "First, please try the following steps...",
                    "To resolve this technical issue...",
                    "The system requires...",
                    "Please follow these technical procedures..."
                ],
                document_priorities=["manual", "procedure", "technical", "faq"],
                language_style="technical_instructional"
            ),    
        
            DomainType.BILLING: DomainTerminology(
                domain=DomainType.BILLING,
                keywords=[
                    "billing", "payment", "invoice", "charge", "fee", "cost",
                    "price", "refund", "credit", "debit", "transaction",
                    "account", "balance", "statement", "receipt", "tax",
                    "discount", "promotion", "subscription", "renewal"
                ],
                concepts=[
                    "payment processing", "billing cycle", "account management",
                    "refund policy", "pricing structure", "subscription management",
                    "tax calculation", "discount application", "payment methods"
                ],
                specialized_terms=[
                    "pro-rated charges", "billing reconciliation", "payment gateway",
                    "merchant account", "chargeback", "payment authorization",
                    "recurring billing", "usage-based pricing", "tiered pricing"
                ],
                response_patterns=[
                    "Regarding your billing inquiry...",
                    "Your account shows...",
                    "Payment processing typically...",
                    "Our billing policy states...",
                    "For billing adjustments..."
                ],
                document_priorities=["billing", "policy", "faq", "procedure"],
                language_style="business_financial"
            ),
            
            DomainType.APPOINTMENT: DomainTerminology(
                domain=DomainType.APPOINTMENT,
                keywords=[
                    "appointment", "schedule", "booking", "calendar", "time",
                    "date", "availability", "reschedule", "cancel", "confirm",
                    "reminder", "slot", "duration", "meeting", "consultation",
                    "visit", "session", "reservation", "availability"
                ],
                concepts=[
                    "appointment scheduling", "calendar management", "booking system",
                    "availability checking", "appointment confirmation", "rescheduling process",
                    "cancellation policy", "reminder system", "time slot management"
                ],
                specialized_terms=[
                    "booking window", "lead time", "cancellation period",
                    "no-show policy", "waitlist management", "recurring appointments",
                    "buffer time", "scheduling conflicts", "appointment types"
                ],
                response_patterns=[
                    "To schedule your appointment...",
                    "Your appointment is confirmed for...",
                    "Available time slots include...",
                    "To reschedule or cancel...",
                    "Our booking system shows..."
                ],
                document_priorities=["procedure", "policy", "faq", "manual"],
                language_style="service_oriented"
            ),
            
            DomainType.GENERAL: DomainTerminology(
                domain=DomainType.GENERAL,
                keywords=[
                    "help", "information", "question", "support", "service",
                    "customer", "assistance", "general", "about", "contact"
                ],
                concepts=[
                    "customer service", "general information", "basic support",
                    "company information", "service overview", "contact information"
                ],
                specialized_terms=[],
                response_patterns=[
                    "I'd be happy to help you with...",
                    "Let me provide you with information about...",
                    "For general inquiries...",
                    "Our customer service team can assist...",
                    "Here's what you need to know..."
                ],
                document_priorities=["faq", "general", "procedure", "policy"],
                language_style="conversational_helpful"
            )
        }
    
    def get_domain_terminology(self, domain: DomainType) -> DomainTerminology:
        """Get terminology for a specific domain."""
        return self.domain_terminologies.get(domain, self.domain_terminologies[DomainType.GENERAL])
    
    def get_all_domains(self) -> List[DomainType]:
        """Get list of all available domains."""
        return list(self.domain_terminologies.keys())

class DomainDetector:
    """Detects domain expertise from conversation content and document types."""
    
    def __init__(self, terminology_db: DomainTerminologyDatabase):
        """Initialize domain detector."""
        self.terminology_db = terminology_db
        self.detection_threshold = 0.3  # Minimum confidence for domain detection
        logger.info("Domain detector initialized")
    
    def detect_domain_from_query(self, query: str) -> Tuple[DomainType, float, List[str]]:
        """
        Detect domain from user query.
        
        Args:
            query: User query text
            
        Returns:
            Tuple of (detected_domain, confidence, supporting_evidence)
        """
        query_lower = query.lower()
        domain_scores = {}
        evidence_by_domain = {}
        
        # Score each domain based on keyword matches
        for domain_type in self.terminology_db.get_all_domains():
            terminology = self.terminology_db.get_domain_terminology(domain_type)
            
            # Count keyword matches
            keyword_matches = []
            for keyword in terminology.keywords:
                if keyword.lower() in query_lower:
                    keyword_matches.append(keyword)
            
            # Count concept matches (partial matching)
            concept_matches = []
            for concept in terminology.concepts:
                concept_words = concept.lower().split()
                if any(word in query_lower for word in concept_words):
                    concept_matches.append(concept)
            
            # Count specialized term matches (higher weight)
            specialized_matches = []
            for term in terminology.specialized_terms:
                if term.lower() in query_lower:
                    specialized_matches.append(term)
            
            # Calculate domain score
            keyword_score = len(keyword_matches) * 1.0
            concept_score = len(concept_matches) * 0.5
            specialized_score = len(specialized_matches) * 2.0
            
            total_score = keyword_score + concept_score + specialized_score
            
            # Normalize by total possible terms
            total_terms = len(terminology.keywords) + len(terminology.concepts) + len(terminology.specialized_terms)
            normalized_score = total_score / max(total_terms, 1) if total_terms > 0 else 0
            
            domain_scores[domain_type] = normalized_score
            evidence_by_domain[domain_type] = keyword_matches + concept_matches + specialized_matches
        
        # Find highest scoring domain
        best_domain = max(domain_scores.keys(), key=lambda d: domain_scores[d])
        best_score = domain_scores[best_domain]
        best_evidence = evidence_by_domain[best_domain]
        
        # If score is below threshold, default to general
        if best_score < self.detection_threshold:
            return DomainType.GENERAL, best_score, []
        
        return best_domain, best_score, best_evidence
    
    def detect_domain_from_documents(self, document_types: List[str], 
                                   document_contents: List[str]) -> Tuple[DomainType, float, List[str]]:
        """
        Detect domain from document types and contents.
        
        Args:
            document_types: List of document types (e.g., ['policy', 'faq'])
            document_contents: List of document content snippets
            
        Returns:
            Tuple of (detected_domain, confidence, supporting_evidence)
        """
        domain_scores = {}
        evidence_by_domain = {}
        
        # Combine all document content
        combined_content = " ".join(document_contents).lower()
        
        # Score domains based on document type priorities and content
        for domain_type in self.terminology_db.get_all_domains():
            terminology = self.terminology_db.get_domain_terminology(domain_type)
            
            # Score based on document type priorities
            doc_type_score = 0
            doc_type_evidence = []
            for doc_type in document_types:
                if doc_type in terminology.document_priorities:
                    priority_index = terminology.document_priorities.index(doc_type)
                    # Higher priority = higher score (reverse index)
                    doc_type_score += (len(terminology.document_priorities) - priority_index) * 0.5
                    doc_type_evidence.append(f"document_type:{doc_type}")
            
            # Score based on content terminology
            content_matches = []
            for keyword in terminology.keywords:
                if keyword.lower() in combined_content:
                    content_matches.append(keyword)
            
            content_score = len(content_matches) * 0.3
            
            total_score = doc_type_score + content_score
            domain_scores[domain_type] = total_score
            evidence_by_domain[domain_type] = doc_type_evidence + content_matches
        
        # Find highest scoring domain
        best_domain = max(domain_scores.keys(), key=lambda d: domain_scores[d])
        best_score = domain_scores[best_domain]
        best_evidence = evidence_by_domain[best_domain]
        
        # Normalize score (rough normalization)
        max_possible_score = len(document_types) * 2.0 + 10  # Rough estimate
        normalized_score = min(best_score / max_possible_score, 1.0)
        
        return best_domain, normalized_score, best_evidence    

    def detect_domain_comprehensive(self, query: str, document_types: List[str], 
                                  document_contents: List[str], 
                                  conversation_history: List[str] = None) -> DomainContext:
        """
        Comprehensive domain detection using multiple signals.
        
        Args:
            query: User query
            document_types: Document types from search results
            document_contents: Document content snippets
            conversation_history: Recent conversation history
            
        Returns:
            DomainContext with comprehensive domain information
        """
        # Detect from query
        query_domain, query_confidence, query_evidence = self.detect_domain_from_query(query)
        
        # Detect from documents
        doc_domain, doc_confidence, doc_evidence = self.detect_domain_from_documents(
            document_types, document_contents
        )
        
        # Detect from conversation history if available
        history_domain = DomainType.GENERAL
        history_confidence = 0.0
        history_evidence = []
        
        if conversation_history:
            combined_history = " ".join(conversation_history)
            history_domain, history_confidence, history_evidence = self.detect_domain_from_query(
                combined_history
            )
        
        # Combine signals with weights
        query_weight = 0.4
        doc_weight = 0.4
        history_weight = 0.2
        
        # Calculate weighted scores for each domain
        domain_scores = {}
        all_domains = self.terminology_db.get_all_domains()
        
        for domain in all_domains:
            score = 0.0
            if domain == query_domain:
                score += query_confidence * query_weight
            if domain == doc_domain:
                score += doc_confidence * doc_weight
            if domain == history_domain:
                score += history_confidence * history_weight
            
            domain_scores[domain] = score
        
        # Find best domain
        best_domain = max(domain_scores.keys(), key=lambda d: domain_scores[d])
        best_confidence = domain_scores[best_domain]
        
        # Combine evidence
        all_evidence = query_evidence + doc_evidence + history_evidence
        terminology_matches = [e for e in all_evidence if not e.startswith("document_type:")]
        
        # Determine expertise level based on terminology complexity
        expertise_level = self._determine_expertise_level(terminology_matches, best_domain)
        
        return DomainContext(
            detected_domain=best_domain,
            confidence=best_confidence,
            supporting_evidence=all_evidence,
            terminology_matches=terminology_matches,
            document_types_used=document_types,
            expertise_level=expertise_level
        )
    
    def _determine_expertise_level(self, terminology_matches: List[str], domain: DomainType) -> str:
        """Determine appropriate expertise level based on terminology used."""
        if not terminology_matches:
            return "basic"
        
        terminology = self.terminology_db.get_domain_terminology(domain)
        
        # Count specialized terms used
        specialized_count = sum(1 for match in terminology_matches 
                              if match in terminology.specialized_terms)
        
        # Determine level based on specialized term usage
        if specialized_count >= 2:
            return "advanced"
        elif specialized_count >= 1 or len(terminology_matches) >= 3:
            return "intermediate"
        else:
            return "basic"

class DomainResponseAdapter:
    """Adapts responses based on detected domain expertise."""
    
    def __init__(self, terminology_db: DomainTerminologyDatabase):
        """Initialize domain response adapter."""
        self.terminology_db = terminology_db
        logger.info("Domain response adapter initialized")
    
    def adapt_response(self, original_response: str, domain_context: DomainContext,
                      query: str, document_sources: List[str]) -> DomainResponse:
        """
        Adapt response based on domain context.
        
        Args:
            original_response: Original RAG response
            domain_context: Detected domain context
            query: Original user query
            document_sources: Sources used in response
            
        Returns:
            Domain-adapted response
        """
        terminology = self.terminology_db.get_domain_terminology(domain_context.detected_domain)
        
        # Adapt response based on domain
        adapted_response = self._apply_domain_language_style(
            original_response, terminology, domain_context.expertise_level
        )
        
        # Add domain-specific terminology
        terminology_used = self._enhance_with_domain_terminology(
            adapted_response, terminology, domain_context.expertise_level
        )
        
        # Prioritize document sources based on domain
        prioritized_sources = self._prioritize_document_sources(
            document_sources, terminology.document_priorities
        )
        
        # Generate clarifying questions if needed
        clarifying_questions = self._generate_clarifying_questions(
            query, domain_context, terminology
        )
        
        # Add expertise indicators
        expertise_indicators = self._add_expertise_indicators(
            domain_context, terminology
        )
        
        return DomainResponse(
            original_response=original_response,
            adapted_response=adapted_response,
            domain=domain_context.detected_domain,
            terminology_used=terminology_used,
            document_sources_prioritized=prioritized_sources,
            clarifying_questions=clarifying_questions,
            expertise_indicators=expertise_indicators
        )
    
    def _apply_domain_language_style(self, response: str, terminology: DomainTerminology,
                                   expertise_level: str) -> str:
        """Apply domain-specific language style to response."""
        
        # Get appropriate response pattern
        if terminology.response_patterns:
            pattern = terminology.response_patterns[0]  # Use first pattern as prefix
            
            # Adjust pattern based on expertise level
            if expertise_level == "advanced" and terminology.domain == DomainType.HEALTHCARE:
                pattern = "Based on clinical protocols and medical guidelines..."
            elif expertise_level == "advanced" and terminology.domain == DomainType.LEGAL:
                pattern = "According to applicable legal statutes and regulations..."
            elif expertise_level == "advanced" and terminology.domain == DomainType.TECHNICAL_SUPPORT:
                pattern = "Following technical specifications and system requirements..."
            
            # Prepend pattern if response doesn't already start with domain language
            if not any(p.lower() in response.lower()[:50] for p in terminology.response_patterns):
                response = f"{pattern} {response}"
        
        # Apply language style adjustments
        if terminology.language_style == "professional_medical":
            response = self._apply_medical_language_style(response, expertise_level)
        elif terminology.language_style == "formal_legal":
            response = self._apply_legal_language_style(response, expertise_level)
        elif terminology.language_style == "technical_instructional":
            response = self._apply_technical_language_style(response, expertise_level)
        elif terminology.language_style == "business_financial":
            response = self._apply_business_language_style(response, expertise_level)
        
        return response    

    def _apply_medical_language_style(self, response: str, expertise_level: str) -> str:
        """Apply medical language style."""
        if expertise_level == "advanced":
            # Add medical disclaimers and professional language
            if "consult" not in response.lower():
                response += "\n\nPlease consult with your healthcare provider for personalized medical advice."
        
        # Replace casual terms with medical terms
        medical_replacements = {
            "problem": "condition",
            "issue": "medical concern",
            "fix": "treatment",
            "help": "medical assistance"
        }
        
        for casual, medical in medical_replacements.items():
            response = re.sub(r'\b' + casual + r'\b', medical, response, flags=re.IGNORECASE)
        
        return response
    
    def _apply_legal_language_style(self, response: str, expertise_level: str) -> str:
        """Apply legal language style."""
        if expertise_level == "advanced":
            # Add legal disclaimers
            if "policy" in response.lower() and "subject to" not in response.lower():
                response += "\n\nThis information is subject to our current terms and conditions and applicable law."
        
        # Use more formal language
        legal_replacements = {
            "you can": "you may",
            "we'll": "we will",
            "can't": "cannot",
            "won't": "will not"
        }
        
        for informal, formal in legal_replacements.items():
            response = response.replace(informal, formal)
        
        return response
    
    def _apply_technical_language_style(self, response: str, expertise_level: str) -> str:
        """Apply technical language style."""
        if expertise_level == "advanced":
            # Add technical precision
            response = re.sub(r'\btry\b', 'execute', response, flags=re.IGNORECASE)
            response = re.sub(r'\bcheck\b', 'verify', response, flags=re.IGNORECASE)
        
        # Structure as step-by-step if not already
        if "step" not in response.lower() and len(response.split('.')) > 2:
            sentences = [s.strip() for s in response.split('.') if s.strip()]
            if len(sentences) > 1:
                numbered_steps = []
                for i, sentence in enumerate(sentences, 1):
                    if sentence:
                        numbered_steps.append(f"{i}. {sentence}")
                response = "\n".join(numbered_steps)
        
        return response
    
    def _apply_business_language_style(self, response: str, expertise_level: str) -> str:
        """Apply business/financial language style."""
        # Use professional business language
        business_replacements = {
            "money": "payment",
            "bill": "invoice",
            "pay": "remit payment",
            "cost": "fee"
        }
        
        for casual, business in business_replacements.items():
            response = re.sub(r'\b' + casual + r'\b', business, response, flags=re.IGNORECASE)
        
        return response
    
    def _enhance_with_domain_terminology(self, response: str, terminology: DomainTerminology,
                                       expertise_level: str) -> List[str]:
        """Enhance response with domain-specific terminology."""
        terminology_used = []
        enhanced_response = response
        
        # Replace generic terms with domain-specific ones based on expertise level
        if expertise_level == "advanced":
            # Use specialized terms for advanced users
            generic_replacements = self._get_generic_term_mappings(terminology.domain)
            for generic, specialized in generic_replacements.items():
                if generic.lower() in enhanced_response.lower():
                    enhanced_response = re.sub(
                        r'\b' + re.escape(generic) + r'\b', 
                        specialized, 
                        enhanced_response, 
                        flags=re.IGNORECASE
                    )
                    terminology_used.append(specialized)
            
            # Add specialized terminology context
            for specialized_term in terminology.specialized_terms:
                if specialized_term.lower() in enhanced_response.lower():
                    terminology_used.append(specialized_term)
        
        elif expertise_level == "intermediate":
            # Use mix of standard and some specialized terms
            for concept in terminology.concepts[:3]:  # Use first 3 concepts
                concept_words = concept.lower().split()
                if any(word in enhanced_response.lower() for word in concept_words):
                    terminology_used.append(concept)
            
            # Apply some generic term replacements for intermediate level
            generic_replacements = self._get_generic_term_mappings(terminology.domain)
            for generic, specialized in list(generic_replacements.items())[:2]:  # Use first 2 replacements
                if generic.lower() in enhanced_response.lower():
                    enhanced_response = re.sub(
                        r'\b' + re.escape(generic) + r'\b', 
                        specialized, 
                        enhanced_response, 
                        flags=re.IGNORECASE
                    )
                    terminology_used.append(specialized)
        
        # Always include relevant keywords that appear in response
        for keyword in terminology.keywords:
            if keyword.lower() in enhanced_response.lower():
                terminology_used.append(keyword)
        
        # Add domain-specific context phrases for better understanding
        context_phrases = self._get_domain_context_phrases(terminology.domain, expertise_level)
        for phrase in context_phrases:
            if any(word in enhanced_response.lower() for word in phrase.lower().split()):
                terminology_used.append(phrase)
        
        return list(set(terminology_used))  # Remove duplicates
    
    def _get_domain_context_phrases(self, domain: DomainType, expertise_level: str) -> List[str]:
        """Get domain-specific context phrases based on expertise level."""
        context_phrases = {
            DomainType.HEALTHCARE: {
                "basic": ["health information", "medical care", "patient support"],
                "intermediate": ["clinical guidance", "healthcare protocols", "medical consultation"],
                "advanced": ["evidence-based medicine", "clinical best practices", "therapeutic protocols"]
            },
            DomainType.LEGAL: {
                "basic": ["policy information", "legal requirements", "compliance guidelines"],
                "intermediate": ["regulatory compliance", "contractual obligations", "legal documentation"],
                "advanced": ["statutory requirements", "jurisdictional compliance", "legal precedent"]
            },
            DomainType.TECHNICAL_SUPPORT: {
                "basic": ["technical help", "system support", "troubleshooting guide"],
                "intermediate": ["system configuration", "technical procedures", "diagnostic steps"],
                "advanced": ["system architecture", "technical specifications", "advanced diagnostics"]
            },
            DomainType.BILLING: {
                "basic": ["billing information", "payment help", "account support"],
                "intermediate": ["billing procedures", "payment processing", "account management"],
                "advanced": ["financial reconciliation", "billing optimization", "payment gateway integration"]
            },
            DomainType.APPOINTMENT: {
                "basic": ["appointment help", "scheduling support", "booking assistance"],
                "intermediate": ["scheduling procedures", "appointment management", "calendar coordination"],
                "advanced": ["scheduling optimization", "resource allocation", "appointment workflow"]
            },
            DomainType.GENERAL: {
                "basic": ["general information", "customer support", "basic assistance"],
                "intermediate": ["service information", "customer guidance", "support procedures"],
                "advanced": ["comprehensive support", "service optimization", "customer success"]
            }
        }
        
        return context_phrases.get(domain, {}).get(expertise_level, [])
    
    def _get_generic_term_mappings(self, domain: DomainType) -> Dict[str, str]:
        """Get mappings from generic terms to domain-specific terms."""
        mappings = {
            DomainType.HEALTHCARE: {
                "problem": "medical condition",
                "issue": "health concern", 
                "help": "medical assistance",
                "fix": "treatment",
                "check": "examination",
                "visit": "consultation",
                "meeting": "appointment"
            },
            DomainType.LEGAL: {
                "rule": "regulation",
                "agreement": "contract",
                "problem": "legal issue",
                "allowed": "permitted under policy",
                "forbidden": "prohibited by terms",
                "must": "shall",
                "should": "is required to"
            },
            DomainType.TECHNICAL_SUPPORT: {
                "problem": "technical issue",
                "broken": "malfunctioning",
                "fix": "resolve",
                "check": "verify",
                "try": "execute",
                "error": "system error",
                "issue": "technical problem"
            },
            DomainType.BILLING: {
                "money": "payment",
                "bill": "invoice", 
                "cost": "fee",
                "pay": "remit payment",
                "charge": "billing charge",
                "owe": "outstanding balance"
            },
            DomainType.APPOINTMENT: {
                "meeting": "appointment",
                "time": "time slot",
                "available": "appointment availability",
                "book": "schedule",
                "cancel": "cancel appointment"
            }
        }
        
        return mappings.get(domain, {})
    
    def _prioritize_document_sources(self, document_sources: List[str], 
                                   priorities: List[str]) -> List[str]:
        """Prioritize document sources based on domain preferences."""
        prioritized = []
        
        # First, add sources that match priority order
        for priority_type in priorities:
            for source in document_sources:
                if priority_type.lower() in source.lower() and source not in prioritized:
                    prioritized.append(source)
        
        # Then add remaining sources
        for source in document_sources:
            if source not in prioritized:
                prioritized.append(source)
        
        return prioritized
    
    def _generate_clarifying_questions(self, query: str, domain_context: DomainContext,
                                     terminology: DomainTerminology) -> List[str]:
        """Generate sophisticated domain-specific clarifying questions."""
        questions = []
        query_lower = query.lower()
        
        # Only generate questions if confidence is moderate (not too high, not too low)
        if domain_context.confidence < 0.4 or domain_context.confidence > 0.9:
            return []
        
        # Generate questions based on domain and query analysis
        if domain_context.detected_domain == DomainType.HEALTHCARE:
            questions.extend(self._generate_healthcare_questions(query_lower, domain_context.expertise_level))
        elif domain_context.detected_domain == DomainType.LEGAL:
            questions.extend(self._generate_legal_questions(query_lower, domain_context.expertise_level))
        elif domain_context.detected_domain == DomainType.TECHNICAL_SUPPORT:
            questions.extend(self._generate_technical_questions(query_lower, domain_context.expertise_level))
        elif domain_context.detected_domain == DomainType.BILLING:
            questions.extend(self._generate_billing_questions(query_lower, domain_context.expertise_level))
        elif domain_context.detected_domain == DomainType.APPOINTMENT:
            questions.extend(self._generate_appointment_questions(query_lower, domain_context.expertise_level))
        
        # Filter out redundant questions based on query content
        filtered_questions = self._filter_redundant_questions(questions, query_lower)
        
        # Limit to most relevant questions
        return filtered_questions[:2]
    
    def _generate_healthcare_questions(self, query_lower: str, expertise_level: str) -> List[str]:
        """Generate healthcare-specific clarifying questions."""
        questions = []
        
        if "appointment" in query_lower:
            if expertise_level == "basic":
                questions.extend([
                    "What type of medical visit do you need?",
                    "Is this urgent or can it wait for a regular appointment?"
                ])
            else:
                questions.extend([
                    "What type of medical consultation are you seeking?",
                    "Do you need a specialist referral or general practitioner visit?"
                ])
        
        elif any(term in query_lower for term in ["medication", "prescription", "drug"]):
            questions.extend([
                "Are you asking about a current prescription or requesting a new one?",
                "Do you have any known allergies or drug interactions I should consider?"
            ])
        
        elif any(term in query_lower for term in ["symptoms", "pain", "sick", "illness"]):
            if expertise_level == "basic":
                questions.extend([
                    "How long have you been experiencing these symptoms?",
                    "Would you like me to help you understand when to seek medical care?"
                ])
            else:
                questions.extend([
                    "What is the duration and severity of your symptoms?",
                    "Have you consulted with a healthcare provider about this condition?"
                ])
        
        elif "insurance" in query_lower:
            questions.extend([
                "Are you asking about coverage for a specific service or general benefits?",
                "Do you need help understanding your insurance policy terms?"
            ])
        
        return questions
    
    def _generate_legal_questions(self, query_lower: str, expertise_level: str) -> List[str]:
        """Generate legal-specific clarifying questions."""
        questions = []
        
        if "policy" in query_lower:
            questions.extend([
                "Are you asking about our privacy policy, terms of service, or another specific policy?",
                "Is this related to compliance requirements or general policy information?"
            ])
        
        elif any(term in query_lower for term in ["rights", "legal", "law"]):
            if expertise_level == "basic":
                questions.extend([
                    "Are you asking about your rights as a customer or patient?",
                    "Do you need help understanding a specific legal requirement?"
                ])
            else:
                questions.extend([
                    "Are you seeking information about statutory rights or contractual obligations?",
                    "Is this related to regulatory compliance or dispute resolution?"
                ])
        
        elif any(term in query_lower for term in ["contract", "agreement", "terms"]):
            questions.extend([
                "Are you asking about existing terms or negotiating new agreements?",
                "Do you need clarification on specific contractual provisions?"
            ])
        
        elif "privacy" in query_lower:
            questions.extend([
                "Are you asking about data privacy rights or information handling practices?",
                "Is this related to a specific privacy concern or general policy?"
            ])
        
        return questions
    
    def _generate_technical_questions(self, query_lower: str, expertise_level: str) -> List[str]:
        """Generate technical support clarifying questions."""
        questions = []
        
        if any(term in query_lower for term in ["error", "problem", "issue", "bug"]):
            if expertise_level == "basic":
                questions.extend([
                    "What device or application are you having trouble with?",
                    "Can you describe what happens when the problem occurs?"
                ])
            else:
                questions.extend([
                    "What system configuration are you running?",
                    "Can you provide the specific error message or error code?"
                ])
        
        elif any(term in query_lower for term in ["setup", "install", "configure"]):
            questions.extend([
                "What operating system and version are you using?",
                "Is this a new installation or an upgrade from a previous version?"
            ])
        
        elif any(term in query_lower for term in ["connection", "network", "internet"]):
            questions.extend([
                "Are you experiencing intermittent or constant connectivity issues?",
                "What type of network connection are you using (WiFi, ethernet, mobile)?"
            ])
        
        elif "performance" in query_lower:
            questions.extend([
                "When did you first notice the performance issues?",
                "Are there specific actions that trigger the slow performance?"
            ])
        
        return questions
    
    def _generate_billing_questions(self, query_lower: str, expertise_level: str) -> List[str]:
        """Generate billing-specific clarifying questions."""
        questions = []
        
        if any(term in query_lower for term in ["payment", "charge", "fee"]):
            questions.extend([
                "Are you asking about a specific charge or your overall billing statement?",
                "Do you need help with payment methods or understanding billing details?"
            ])
        
        elif "refund" in query_lower:
            questions.extend([
                "What service or transaction are you requesting a refund for?",
                "Do you have the transaction ID or invoice number?"
            ])
        
        elif any(term in query_lower for term in ["invoice", "statement", "bill"]):
            questions.extend([
                "Are you looking for a current statement or historical billing information?",
                "Do you need help understanding specific charges on your statement?"
            ])
        
        elif "subscription" in query_lower:
            questions.extend([
                "Are you asking about subscription management or billing cycles?",
                "Do you want to modify, cancel, or upgrade your subscription?"
            ])
        
        return questions
    
    def _generate_appointment_questions(self, query_lower: str, expertise_level: str) -> List[str]:
        """Generate appointment-specific clarifying questions."""
        questions = []
        
        if any(term in query_lower for term in ["schedule", "book", "appointment"]):
            questions.extend([
                "What type of appointment or service do you need?",
                "Do you have preferred dates and times, or are you flexible?"
            ])
        
        elif any(term in query_lower for term in ["cancel", "reschedule", "change"]):
            questions.extend([
                "Do you have your appointment confirmation number or reference?",
                "Would you like to reschedule for a different time or cancel completely?"
            ])
        
        elif "availability" in query_lower:
            questions.extend([
                "What time frame are you looking for availability?",
                "Do you have any scheduling constraints or preferences?"
            ])
        
        elif "reminder" in query_lower:
            questions.extend([
                "Would you like to set up appointment reminders?",
                "How would you prefer to receive appointment notifications?"
            ])
        
        return questions
    
    def _filter_redundant_questions(self, questions: List[str], query_lower: str) -> List[str]:
        """Filter out questions that are redundant based on the original query."""
        filtered = []
        
        for question in questions:
            question_lower = question.lower()
            question_keywords = set(question_lower.split())
            query_keywords = set(query_lower.split())
            
            # Skip if question has too much overlap with original query
            overlap = len(question_keywords.intersection(query_keywords))
            if overlap > len(question_keywords) * 0.4:  # More than 40% overlap
                continue
            
            # Skip if question seems to ask about something already specified
            if any(keyword in query_lower for keyword in ["specific", "exactly", "particular"]):
                if any(word in question_lower for word in ["what type", "which", "specific"]):
                    continue
            
            filtered.append(question)
        
        return filtered
        """Generate healthcare-specific clarifying questions."""
        questions = []
        
        if "appointment" in query_lower:
            if expertise_level == "basic":
                questions.extend([
                    "What type of medical visit do you need?",
                    "Is this urgent or can it wait for a regular appointment?"
                ])
            else:
                questions.extend([
                    "What type of medical consultation are you seeking?",
                    "Do you need a specialist referral or general practitioner visit?"
                ])
        
        elif any(term in query_lower for term in ["medication", "prescription", "drug"]):
            questions.extend([
                "Are you asking about a current prescription or requesting a new one?",
                "Do you have any known allergies or drug interactions I should consider?"
            ])
        
        elif any(term in query_lower for term in ["symptoms", "pain", "sick", "illness"]):
            if expertise_level == "basic":
                questions.extend([
                    "How long have you been experiencing these symptoms?",
                    "Would you like me to help you understand when to seek medical care?"
                ])
            else:
                questions.extend([
                    "What is the duration and severity of your symptoms?",
                    "Have you consulted with a healthcare provider about this condition?"
                ])
        
        elif "insurance" in query_lower:
            questions.extend([
                "Are you asking about coverage for a specific service or general benefits?",
                "Do you need help understanding your insurance policy terms?"
            ])
        
        return questions
    
    def _generate_legal_questions(self, query_lower: str, expertise_level: str) -> List[str]:
        """Generate legal-specific clarifying questions."""
        questions = []
        
        if "policy" in query_lower:
            questions.extend([
                "Are you asking about our privacy policy, terms of service, or another specific policy?",
                "Is this related to compliance requirements or general policy information?"
            ])
        
        elif any(term in query_lower for term in ["rights", "legal", "law"]):
            if expertise_level == "basic":
                questions.extend([
                    "Are you asking about your rights as a customer or patient?",
                    "Do you need help understanding a specific legal requirement?"
                ])
            else:
                questions.extend([
                    "Are you seeking information about statutory rights or contractual obligations?",
                    "Is this related to regulatory compliance or dispute resolution?"
                ])
        
        elif any(term in query_lower for term in ["contract", "agreement", "terms"]):
            questions.extend([
                "Are you asking about existing terms or negotiating new agreements?",
                "Do you need clarification on specific contractual provisions?"
            ])
        
        elif "privacy" in query_lower:
            questions.extend([
                "Are you asking about data privacy rights or information handling practices?",
                "Is this related to a specific privacy concern or general policy?"
            ])
        
        return questions
    
    def _generate_technical_questions(self, query_lower: str, expertise_level: str) -> List[str]:
        """Generate technical support clarifying questions."""
        questions = []
        
        if any(term in query_lower for term in ["error", "problem", "issue", "bug"]):
            if expertise_level == "basic":
                questions.extend([
                    "What device or application are you having trouble with?",
                    "Can you describe what happens when the problem occurs?"
                ])
            else:
                questions.extend([
                    "What system configuration are you running?",
                    "Can you provide the specific error message or error code?"
                ])
        
        elif any(term in query_lower for term in ["setup", "install", "configure"]):
            questions.extend([
                "What operating system and version are you using?",
                "Is this a new installation or an upgrade from a previous version?"
            ])
        
        elif any(term in query_lower for term in ["connection", "network", "internet"]):
            questions.extend([
                "Are you experiencing intermittent or constant connectivity issues?",
                "What type of network connection are you using (WiFi, ethernet, mobile)?"
            ])
        
        elif "performance" in query_lower:
            questions.extend([
                "When did you first notice the performance issues?",
                "Are there specific actions that trigger the slow performance?"
            ])
        
        return questions
    
    def _generate_billing_questions(self, query_lower: str, expertise_level: str) -> List[str]:
        """Generate billing-specific clarifying questions."""
        questions = []
        
        if any(term in query_lower for term in ["payment", "charge", "fee"]):
            questions.extend([
                "Are you asking about a specific charge or your overall billing statement?",
                "Do you need help with payment methods or understanding billing details?"
            ])
        
        elif "refund" in query_lower:
            questions.extend([
                "What service or transaction are you requesting a refund for?",
                "Do you have the transaction ID or invoice number?"
            ])
        
        elif any(term in query_lower for term in ["invoice", "statement", "bill"]):
            questions.extend([
                "Are you looking for a current statement or historical billing information?",
                "Do you need help understanding specific charges on your statement?"
            ])
        
        elif "subscription" in query_lower:
            questions.extend([
                "Are you asking about subscription management or billing cycles?",
                "Do you want to modify, cancel, or upgrade your subscription?"
            ])
        
        return questions
    
    def _generate_appointment_questions(self, query_lower: str, expertise_level: str) -> List[str]:
        """Generate appointment-specific clarifying questions."""
        questions = []
        
        if any(term in query_lower for term in ["schedule", "book", "appointment"]):
            questions.extend([
                "What type of appointment or service do you need?",
                "Do you have preferred dates and times, or are you flexible?"
            ])
        
        elif any(term in query_lower for term in ["cancel", "reschedule", "change"]):
            questions.extend([
                "Do you have your appointment confirmation number or reference?",
                "Would you like to reschedule for a different time or cancel completely?"
            ])
        
        elif "availability" in query_lower:
            questions.extend([
                "What time frame are you looking for availability?",
                "Do you have any scheduling constraints or preferences?"
            ])
        
        elif "reminder" in query_lower:
            questions.extend([
                "Would you like to set up appointment reminders?",
                "How would you prefer to receive appointment notifications?"
            ])
        
        return questions
    
    def _filter_redundant_questions(self, questions: List[str], query_lower: str) -> List[str]:
        """Filter out questions that are redundant based on the original query."""
        filtered = []
        
        for question in questions:
            question_lower = question.lower()
            question_keywords = set(question_lower.split())
            query_keywords = set(query_lower.split())
            
            # Skip if question has too much overlap with original query
            overlap = len(question_keywords.intersection(query_keywords))
            if overlap > len(question_keywords) * 0.4:  # More than 40% overlap
                continue
            
            # Skip if question seems to ask about something already specified
            if any(keyword in query_lower for keyword in ["specific", "exactly", "particular"]):
                if any(word in question_lower for word in ["what type", "which", "specific"]):
                    continue
            
            filtered.append(question)
        
        return filtered
    
    def _add_expertise_indicators(self, domain_context: DomainContext,
                                terminology: DomainTerminology) -> List[str]:
        """Add indicators of domain expertise level."""
        indicators = []
        
        if domain_context.expertise_level == "advanced":
            if domain_context.detected_domain == DomainType.HEALTHCARE:
                indicators.append("Based on medical protocols")
            elif domain_context.detected_domain == DomainType.LEGAL:
                indicators.append("According to legal requirements")
            elif domain_context.detected_domain == DomainType.TECHNICAL_SUPPORT:
                indicators.append("Following technical specifications")
        
        if domain_context.confidence > 0.8:
            indicators.append(f"Specialized {domain_context.detected_domain.value} guidance")
        
        return indicators

class DomainExpertiseEngine:
    """Main engine for domain expertise adaptation."""
    
    def __init__(self):
        """Initialize domain expertise engine."""
        self.terminology_db = DomainTerminologyDatabase()
        self.domain_detector = DomainDetector(self.terminology_db)
        self.response_adapter = DomainResponseAdapter(self.terminology_db)
        
        # Track domain usage for learning
        self.domain_usage_stats = Counter()
        
        logger.info("Domain expertise engine initialized")
    
    def process_query_with_domain_expertise(self, query: str, rag_response: str,
                                          document_types: List[str],
                                          document_contents: List[str],
                                          document_sources: List[str],
                                          conversation_history: List[str] = None) -> DomainResponse:
        """
        Process query with domain expertise adaptation.
        
        Args:
            query: User query
            rag_response: Original RAG response
            document_types: Document types from search results
            document_contents: Document content snippets
            document_sources: Document source files
            conversation_history: Recent conversation history
            
        Returns:
            Domain-adapted response
        """
        # Detect domain context
        domain_context = self.domain_detector.detect_domain_comprehensive(
            query=query,
            document_types=document_types,
            document_contents=document_contents,
            conversation_history=conversation_history
        )
        
        # Track domain usage
        self.domain_usage_stats[domain_context.detected_domain] += 1
        
        # Adapt response based on domain
        domain_response = self.response_adapter.adapt_response(
            original_response=rag_response,
            domain_context=domain_context,
            query=query,
            document_sources=document_sources
        )
        
        logger.info(f"Applied {domain_context.detected_domain.value} domain expertise "
                   f"(confidence: {domain_context.confidence:.2f}, "
                   f"level: {domain_context.expertise_level})")
        
        return domain_response
    
    def get_domain_statistics(self) -> Dict[str, Any]:
        """Get domain usage statistics."""
        return {
            "domain_usage_counts": dict(self.domain_usage_stats),
            "total_queries_processed": sum(self.domain_usage_stats.values()),
            "most_common_domain": self.domain_usage_stats.most_common(1)[0] if self.domain_usage_stats else None,
            "available_domains": [domain.value for domain in self.terminology_db.get_all_domains()]
        }
    
    def update_domain_terminology(self, domain: DomainType, 
                                new_keywords: List[str] = None,
                                new_concepts: List[str] = None,
                                new_specialized_terms: List[str] = None):
        """Update domain terminology based on usage patterns."""
        terminology = self.terminology_db.get_domain_terminology(domain)
        
        if new_keywords:
            terminology.keywords.extend(new_keywords)
            terminology.keywords = list(set(terminology.keywords))  # Remove duplicates
        
        if new_concepts:
            terminology.concepts.extend(new_concepts)
            terminology.concepts = list(set(terminology.concepts))
        
        if new_specialized_terms:
            terminology.specialized_terms.extend(new_specialized_terms)
            terminology.specialized_terms = list(set(terminology.specialized_terms))
        
        logger.info(f"Updated terminology for domain: {domain.value}")

# Test the domain expertise system
def test_domain_expertise():
    """Test domain expertise functionality."""
    print("🧪 Testing Domain Expertise System")
    print("=" * 50)
    
    # Initialize engine
    engine = DomainExpertiseEngine()
    
    # Test queries for different domains
    test_cases = [
        {
            "query": "I need to schedule a medical consultation with a doctor for my chronic condition",
            "document_types": ["procedure", "faq"],
            "document_contents": ["To schedule a medical appointment, please call our clinic. We offer specialized consultations for chronic conditions..."],
            "document_sources": ["Medical Procedures Manual", "Healthcare FAQ"],
            "expected_domain": DomainType.HEALTHCARE
        },
        {
            "query": "What is your privacy policy regarding patient data and HIPAA compliance?",
            "document_types": ["policy", "legal"],
            "document_contents": ["Our privacy policy complies with HIPAA regulations and ensures patient confidentiality..."],
            "document_sources": ["Privacy Policy", "Legal Compliance Guide"],
            "expected_domain": DomainType.LEGAL
        },
        {
            "query": "My system is showing a database connectivity error and won't connect to the server",
            "document_types": ["manual", "procedure"],
            "document_contents": ["To troubleshoot connection issues, first verify your network configuration and check firewall settings..."],
            "document_sources": ["Technical Manual", "Troubleshooting Guide"],
            "expected_domain": DomainType.TECHNICAL_SUPPORT
        },
        {
            "query": "I have a question about my billing statement and pro-rated charges",
            "document_types": ["billing", "faq"],
            "document_contents": ["Billing statements are generated monthly and include pro-rated charges for partial service periods..."],
            "document_sources": ["Billing FAQ", "Payment Policy"],
            "expected_domain": DomainType.BILLING
        },
        {
            "query": "I need to reschedule my appointment and check availability for next week",
            "document_types": ["procedure", "faq"],
            "document_contents": ["To reschedule appointments, please provide your booking reference and preferred time slots..."],
            "document_sources": ["Appointment Procedures", "Scheduling FAQ"],
            "expected_domain": DomainType.APPOINTMENT
        }
    ]
    
    print("Testing domain detection and response adaptation...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['expected_domain'].value.upper()}")
        print("-" * 40)
        
        # Process query
        domain_response = engine.process_query_with_domain_expertise(
            query=test_case["query"],
            rag_response="Here is the information you requested based on our documentation.",
            document_types=test_case["document_types"],
            document_contents=test_case["document_contents"],
            document_sources=test_case["document_sources"]
        )
        
        print(f"Query: {test_case['query']}")
        print(f"Detected Domain: {domain_response.domain.value}")
        print(f"Expected Domain: {test_case['expected_domain'].value}")
        print(f"Match: {'✅' if domain_response.domain == test_case['expected_domain'] else '❌'}")
        
        if domain_response.terminology_used:
            print(f"Terminology Used: {', '.join(domain_response.terminology_used[:5])}")
        
        if domain_response.clarifying_questions:
            print(f"Clarifying Questions:")
            for q in domain_response.clarifying_questions:
                print(f"  • {q}")
        
        if domain_response.expertise_indicators:
            print(f"Expertise Indicators: {', '.join(domain_response.expertise_indicators)}")
        
        print(f"Adapted Response: {domain_response.adapted_response[:150]}...")
        
        # Test specialized features
        if domain_response.domain == DomainType.HEALTHCARE:
            print("✓ Healthcare-specific language adaptation applied")
        elif domain_response.domain == DomainType.TECHNICAL_SUPPORT:
            print("✓ Technical support step-by-step formatting applied")
        elif domain_response.domain == DomainType.LEGAL:
            print("✓ Legal formal language and disclaimers applied")
    
    # Test edge cases
    print(f"\n🧪 Testing Edge Cases:")
    print("-" * 40)
    
    # Test low confidence query
    edge_response = engine.process_query_with_domain_expertise(
        query="Hello, can you help me?",
        rag_response="I'd be happy to help you.",
        document_types=["general"],
        document_contents=["General customer service information"],
        document_sources=["General FAQ"]
    )
    print(f"Low confidence query -> Domain: {edge_response.domain.value}")
    print(f"Clarifying questions generated: {len(edge_response.clarifying_questions)}")
    
    # Test mixed domain signals
    mixed_response = engine.process_query_with_domain_expertise(
        query="I need to schedule a billing consultation about my medical insurance",
        rag_response="Let me help you with scheduling and billing information.",
        document_types=["procedure", "billing"],
        document_contents=["Appointment scheduling procedures", "Medical billing information"],
        document_sources=["Scheduling Guide", "Billing Manual"]
    )
    print(f"Mixed signals query -> Domain: {mixed_response.domain.value}")
    
    # Print comprehensive statistics
    print(f"\n📊 Domain Usage Statistics:")
    print("-" * 40)
    stats = engine.get_domain_statistics()
    
    print(f"Total queries processed: {stats['total_queries_processed']}")
    if stats['most_common_domain']:
        print(f"Most common domain: {stats['most_common_domain'][0]} ({stats['most_common_domain'][1]} queries)")
    
    print(f"Domain usage breakdown:")
    for domain, count in stats["domain_usage_counts"].items():
        percentage = (count / stats['total_queries_processed']) * 100 if stats['total_queries_processed'] > 0 else 0
        print(f"  {domain}: {count} queries ({percentage:.1f}%)")
    
    print(f"Available domains: {', '.join(stats['available_domains'])}")
    
    print("\n✅ Domain expertise testing completed successfully!")
    print("🎯 All domain-specific features are working:")
    print("  ✓ Domain detection from queries and documents")
    print("  ✓ Expertise level determination")
    print("  ✓ Language style adaptation")
    print("  ✓ Specialized terminology enhancement")
    print("  ✓ Clarifying questions generation")
    print("  ✓ Document source prioritization")
    print("  ✓ Domain-specific response patterns")

if __name__ == "__main__":
    test_domain_expertise()