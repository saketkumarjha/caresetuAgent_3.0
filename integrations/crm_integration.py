"""CRM Integration Module for LiveKit Voice Agent."""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import aiohttp

logger = logging.getLogger(__name__)

class TicketPriority(Enum):
    """Support ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketStatus(Enum):
    """Support ticket status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

@dataclass
class CustomerInfo:
    """Customer information from CRM."""
    customer_id: str
    name: str
    phone: str
    email: str
    company: Optional[str] = None
    account_status: str = "active"
    previous_appointments: List[Dict] = None
    support_history: List[Dict] = None
    preferences: Dict = None
    created_at: Optional[datetime] = None
    last_contact: Optional[datetime] = None
    
    def __post_init__(self):
        if self.previous_appointments is None:
            self.previous_appointments = []
        if self.support_history is None:
            self.support_history = []
        if self.preferences is None:
            self.preferences = {}

@dataclass
class SupportTicket:
    """Support ticket data structure."""
    ticket_id: str
    customer_id: str
    title: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    category: str
    created_at: datetime
    updated_at: datetime
    assigned_agent: Optional[str] = None
    resolution_notes: Optional[str] = None
    conversation_context: Optional[Dict] = None

@dataclass
class InteractionLog:
    """Customer interaction log entry."""
    interaction_id: str
    customer_id: str
    session_id: str
    interaction_type: str  # "call", "chat", "email"
    channel: str  # "voice_agent", "human_agent", "web"
    summary: str
    duration_seconds: Optional[int] = None
    outcome: Optional[str] = None
    follow_up_required: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class CRMConnector:
    """CRM system connector for customer data and ticket management."""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """
        Initialize CRM connector.
        
        Args:
            api_url: CRM API base URL
            api_key: API authentication key
        """
        self.api_url = api_url or "https://api.example-crm.com"
        self.api_key = api_key
        self.session = None
        
        # In-memory storage for demo/testing (replace with actual CRM API calls)
        self._customers_db = {}
        self._tickets_db = {}
        self._interactions_db = {}
        
        logger.info("✅ CRM Connector initialized")
    
    async def initialize(self):
        """Initialize HTTP session and CRM connection."""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        # Load demo customer data
        await self._load_demo_data()
        logger.info("✅ CRM Connector ready")
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
    
    async def get_customer_by_phone(self, phone: str) -> Optional[CustomerInfo]:
        """
        Get customer information by phone number.
        
        Args:
            phone: Customer phone number
            
        Returns:
            CustomerInfo object or None if not found
        """
        logger.info(f"🔍 Looking up customer by phone: {phone}")
        
        try:
            # In production, this would be an API call to CRM
            # For demo, search in-memory database
            for customer_id, customer in self._customers_db.items():
                if customer.phone == phone:
                    logger.info(f"✅ Found customer: {customer.name} ({customer_id})")
                    return customer
            
            logger.info(f"❌ Customer not found for phone: {phone}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error looking up customer: {e}")
            return None
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[CustomerInfo]:
        """
        Get customer information by customer ID.
        
        Args:
            customer_id: Unique customer identifier
            
        Returns:
            CustomerInfo object or None if not found
        """
        logger.info(f"🔍 Looking up customer by ID: {customer_id}")
        
        try:
            customer = self._customers_db.get(customer_id)
            if customer:
                logger.info(f"✅ Found customer: {customer.name}")
                return customer
            else:
                logger.info(f"❌ Customer not found: {customer_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error looking up customer: {e}")
            return None
    
    async def update_customer_info(self, customer_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update customer information in CRM.
        
        Args:
            customer_id: Customer ID to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"📝 Updating customer {customer_id}: {list(updates.keys())}")
        
        try:
            if customer_id in self._customers_db:
                customer = self._customers_db[customer_id]
                
                # Update fields
                for field, value in updates.items():
                    if hasattr(customer, field):
                        setattr(customer, field, value)
                
                customer.last_contact = datetime.now()
                logger.info(f"✅ Customer {customer_id} updated successfully")
                return True
            else:
                logger.error(f"❌ Customer {customer_id} not found for update")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating customer: {e}")
            return False
    
    async def create_support_ticket(self, customer_id: str, title: str, description: str, 
                                  priority: TicketPriority = TicketPriority.MEDIUM,
                                  category: str = "general") -> Optional[SupportTicket]:
        """
        Create a new support ticket.
        
        Args:
            customer_id: Customer ID
            title: Ticket title
            description: Detailed description
            priority: Ticket priority
            category: Ticket category
            
        Returns:
            SupportTicket object or None if failed
        """
        logger.info(f"🎫 Creating support ticket for customer {customer_id}: {title}")
        
        try:
            ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
            now = datetime.now()
            
            ticket = SupportTicket(
                ticket_id=ticket_id,
                customer_id=customer_id,
                title=title,
                description=description,
                priority=priority,
                status=TicketStatus.OPEN,
                category=category,
                created_at=now,
                updated_at=now
            )
            
            self._tickets_db[ticket_id] = ticket
            
            # Update customer support history
            if customer_id in self._customers_db:
                customer = self._customers_db[customer_id]
                customer.support_history.append({
                    "ticket_id": ticket_id,
                    "title": title,
                    "created_at": now.isoformat(),
                    "status": ticket.status.value
                })
            
            logger.info(f"✅ Support ticket created: {ticket_id}")
            return ticket
            
        except Exception as e:
            logger.error(f"❌ Error creating support ticket: {e}")
            return None
    
    async def update_ticket_status(self, ticket_id: str, status: TicketStatus, 
                                 resolution_notes: str = None) -> bool:
        """
        Update support ticket status.
        
        Args:
            ticket_id: Ticket ID to update
            status: New ticket status
            resolution_notes: Optional resolution notes
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"📝 Updating ticket {ticket_id} status to {status.value}")
        
        try:
            if ticket_id in self._tickets_db:
                ticket = self._tickets_db[ticket_id]
                ticket.status = status
                ticket.updated_at = datetime.now()
                
                if resolution_notes:
                    ticket.resolution_notes = resolution_notes
                
                logger.info(f"✅ Ticket {ticket_id} updated successfully")
                return True
            else:
                logger.error(f"❌ Ticket {ticket_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating ticket: {e}")
            return False
    
    async def log_interaction(self, customer_id: str, session_id: str, 
                            interaction_type: str, summary: str,
                            duration_seconds: int = None, outcome: str = None,
                            follow_up_required: bool = False) -> Optional[InteractionLog]:
        """
        Log customer interaction.
        
        Args:
            customer_id: Customer ID
            session_id: Session ID
            interaction_type: Type of interaction
            summary: Interaction summary
            duration_seconds: Call duration
            outcome: Interaction outcome
            follow_up_required: Whether follow-up is needed
            
        Returns:
            InteractionLog object or None if failed
        """
        logger.info(f"📝 Logging interaction for customer {customer_id}")
        
        try:
            interaction_id = f"INT-{uuid.uuid4().hex[:8].upper()}"
            
            interaction = InteractionLog(
                interaction_id=interaction_id,
                customer_id=customer_id,
                session_id=session_id,
                interaction_type=interaction_type,
                channel="voice_agent",
                summary=summary,
                duration_seconds=duration_seconds,
                outcome=outcome,
                follow_up_required=follow_up_required
            )
            
            self._interactions_db[interaction_id] = interaction
            
            # Update customer last contact
            if customer_id in self._customers_db:
                self._customers_db[customer_id].last_contact = datetime.now()
            
            logger.info(f"✅ Interaction logged: {interaction_id}")
            return interaction
            
        except Exception as e:
            logger.error(f"❌ Error logging interaction: {e}")
            return None
    
    async def get_customer_support_history(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """
        Get customer support history.
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of records to return
            
        Returns:
            List of support history records
        """
        logger.info(f"📋 Getting support history for customer {customer_id}")
        
        try:
            if customer_id in self._customers_db:
                customer = self._customers_db[customer_id]
                history = customer.support_history[-limit:] if customer.support_history else []
                logger.info(f"✅ Found {len(history)} support records")
                return history
            else:
                logger.info(f"❌ Customer {customer_id} not found")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting support history: {e}")
            return []
    
    async def escalate_to_human(self, session_id: str, customer_id: str, 
                              escalation_reason: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Escalate conversation to human agent.
        
        Args:
            session_id: Current session ID
            customer_id: Customer ID
            escalation_reason: Reason for escalation
            context: Conversation context
            
        Returns:
            Escalation details
        """
        logger.info(f"🚨 Escalating session {session_id} to human agent")
        
        try:
            escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
            
            escalation_data = {
                "escalation_id": escalation_id,
                "session_id": session_id,
                "customer_id": customer_id,
                "reason": escalation_reason,
                "context": context,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "priority": "high" if "urgent" in escalation_reason.lower() else "medium"
            }
            
            # In production, this would trigger human agent notification
            # For demo, just log the escalation
            logger.info(f"🚨 Escalation created: {escalation_id}")
            logger.info(f"📞 Human agent notification would be sent")
            
            # Create support ticket for escalation
            if customer_id:
                await self.create_support_ticket(
                    customer_id=customer_id,
                    title=f"Escalated Call - {escalation_reason}",
                    description=f"Voice agent escalation: {escalation_reason}\nSession: {session_id}",
                    priority=TicketPriority.HIGH,
                    category="escalation"
                )
            
            return escalation_data
            
        except Exception as e:
            logger.error(f"❌ Error escalating to human: {e}")
            return {"error": str(e)}
    
    async def _load_demo_data(self):
        """Load demo customer data for testing."""
        demo_customers = [
            CustomerInfo(
                customer_id="CUST-001",
                name="John Smith",
                phone="+1234567890",
                email="john.smith@example.com",
                company="Acme Corp",
                account_status="active",
                previous_appointments=[
                    {"date": "2024-01-15", "service": "Consultation", "status": "completed"},
                    {"date": "2024-02-20", "service": "Follow-up", "status": "completed"}
                ],
                support_history=[
                    {"ticket_id": "TKT-OLD001", "title": "Billing Question", "created_at": "2024-01-10T10:00:00", "status": "resolved"}
                ],
                preferences={"communication": "email", "language": "en"}
            ),
            CustomerInfo(
                customer_id="CUST-002",
                name="Sarah Johnson",
                phone="+1987654321",
                email="sarah.johnson@example.com",
                company="Tech Solutions Inc",
                account_status="active",
                previous_appointments=[],
                support_history=[],
                preferences={"communication": "phone", "language": "en"}
            ),
            CustomerInfo(
                customer_id="CUST-003",
                name="Mike Davis",
                phone="+1555123456",
                email="mike.davis@example.com",
                account_status="premium",
                previous_appointments=[
                    {"date": "2024-03-01", "service": "Premium Support", "status": "completed"}
                ],
                support_history=[
                    {"ticket_id": "TKT-OLD002", "title": "Technical Issue", "created_at": "2024-02-28T14:30:00", "status": "resolved"}
                ],
                preferences={"communication": "email", "priority_support": True}
            )
        ]
        
        for customer in demo_customers:
            self._customers_db[customer.customer_id] = customer
        
        logger.info(f"✅ Loaded {len(demo_customers)} demo customers")

class CRMAction:
    """LiveKit agent action for CRM operations."""
    
    def __init__(self, crm_connector: CRMConnector):
        """Initialize CRM action with connector."""
        self.crm = crm_connector
        logger.info("✅ CRM Action initialized")
    
    async def get_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get customer info by phone number for voice agent."""
        customer = await self.crm.get_customer_by_phone(phone)
        if customer:
            return asdict(customer)
        return None
    
    async def create_support_ticket(self, customer_id: str, title: str, 
                                  description: str, priority: str = "medium") -> Optional[Dict[str, Any]]:
        """Create support ticket for voice agent."""
        priority_enum = TicketPriority(priority.lower())
        ticket = await self.crm.create_support_ticket(customer_id, title, description, priority_enum)
        if ticket:
            return asdict(ticket)
        return None
    
    async def log_call_interaction(self, customer_id: str, session_id: str, 
                                 summary: str, duration: int = None, 
                                 outcome: str = None) -> bool:
        """Log voice call interaction."""
        interaction = await self.crm.log_interaction(
            customer_id=customer_id,
            session_id=session_id,
            interaction_type="voice_call",
            summary=summary,
            duration_seconds=duration,
            outcome=outcome
        )
        return interaction is not None
    
    async def escalate_call(self, session_id: str, customer_id: str, 
                          reason: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate call to human agent."""
        return await self.crm.escalate_to_human(session_id, customer_id, reason, context)

# Test the CRM integration
async def test_crm_integration():
    """Test CRM integration functionality."""
    
    print("🧪 Testing CRM Integration")
    print("=" * 50)
    
    # Initialize CRM connector
    crm = CRMConnector()
    await crm.initialize()
    
    # Test customer lookup
    print("\n🔍 Testing customer lookup...")
    customer = await crm.get_customer_by_phone("+1234567890")
    if customer:
        print(f"✅ Found customer: {customer.name} ({customer.customer_id})")
        print(f"📧 Email: {customer.email}")
        print(f"🏢 Company: {customer.company}")
        print(f"📋 Support history: {len(customer.support_history)} tickets")
    
    # Test support ticket creation
    print("\n🎫 Testing support ticket creation...")
    if customer:
        ticket = await crm.create_support_ticket(
            customer_id=customer.customer_id,
            title="Voice Agent Test Ticket",
            description="Testing CRM integration from voice agent",
            priority=TicketPriority.MEDIUM
        )
        if ticket:
            print(f"✅ Created ticket: {ticket.ticket_id}")
            print(f"📝 Title: {ticket.title}")
            print(f"⚡ Priority: {ticket.priority.value}")
    
    # Test interaction logging
    print("\n📝 Testing interaction logging...")
    if customer:
        interaction = await crm.log_interaction(
            customer_id=customer.customer_id,
            session_id="test-session-001",
            interaction_type="voice_call",
            summary="Customer called about billing question, resolved successfully",
            duration_seconds=180,
            outcome="resolved"
        )
        if interaction:
            print(f"✅ Logged interaction: {interaction.interaction_id}")
            print(f"📞 Type: {interaction.interaction_type}")
            print(f"⏱️ Duration: {interaction.duration_seconds}s")
    
    # Test escalation
    print("\n🚨 Testing escalation...")
    if customer:
        escalation = await crm.escalate_to_human(
            session_id="test-session-002",
            customer_id=customer.customer_id,
            escalation_reason="Complex technical issue requiring specialist",
            context={"issue_type": "technical", "urgency": "high"}
        )
        print(f"✅ Escalation created: {escalation.get('escalation_id')}")
        print(f"🚨 Status: {escalation.get('status')}")
    
    # Test CRM Action wrapper
    print("\n🎬 Testing CRM Action wrapper...")
    crm_action = CRMAction(crm)
    
    customer_data = await crm_action.get_customer_by_phone("+1987654321")
    if customer_data:
        print(f"✅ CRM Action found customer: {customer_data['name']}")
    
    await crm.close()
    print("\n✅ CRM Integration test completed")

if __name__ == "__main__":
    asyncio.run(test_crm_integration())