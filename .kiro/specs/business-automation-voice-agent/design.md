# Design Document

## Overview

The Business Automation Voice Agent is built on LiveKit's Agents framework, providing a production-ready voice processing system for customer support and appointment scheduling. The system leverages LiveKit Cloud infrastructure with AssemblyAI's Universal-Streaming technology and implements the STT → LLM → TTS pipeline orchestration. The architecture emphasizes rapid development, built-in scalability, and seamless telephony integration while reducing infrastructure complexity.

## Architecture

### LiveKit-Based Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Phone[Phone Calls via LiveKit Telephony]
        WebRTC[WebRTC Clients]
        SIP[SIP Endpoints]
    end

    subgraph "LiveKit Cloud Infrastructure"
        LKCloud[LiveKit Cloud]
        LKTelephony[LiveKit Telephony Integration]
        LKAgents[LiveKit Agents Framework]
    end

    subgraph "Agent Pipeline (STT → LLM → TTS)"
        AssemblyAI[AssemblyAI Universal-Streaming]
        Gemini[Google Gemini 2.0 Flash]
        TTS[Google Cloud TTS / ElevenLabs]
    end

    subgraph "Business Logic Modules"
        SupportAgent[Customer Support Agent]
        SchedulingAgent[Appointment Scheduling Agent]
        IntentRouter[Intent Detection & Routing]
    end

    subgraph "Integration Actions"
        CRMAction[CRM Connector Action]
        CalendarAction[Calendar Connector Action]
        KnowledgeAction[Knowledge Base RAG Action]
        NotificationAction[Email/SMS Notification Action]
    end

    subgraph "External Services"
        CRM[CRM Systems]
        Calendar[Google Calendar/Outlook]
        KnowledgeBase[Vector Database (Pinecone/Weaviate)]
        Communications[Twilio/SendGrid]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL - Customer Data)]
        Redis[(Redis - Session State)]
        Analytics[(LiveKit Analytics)]
    end

    Phone --> LKTelephony
    WebRTC --> LKCloud
    SIP --> LKCloud

    LKTelephony --> LKAgents
    LKCloud --> LKAgents

    LKAgents --> AssemblyAI
    AssemblyAI --> Gemini
    Gemini --> TTS
    TTS --> LKAgents

    LKAgents --> IntentRouter
    IntentRouter --> SupportAgent
    IntentRouter --> SchedulingAgent

    SupportAgent --> CRMAction
    SupportAgent --> KnowledgeAction
    SchedulingAgent --> CalendarAction
    SchedulingAgent --> NotificationAction

    CRMAction --> CRM
    CalendarAction --> Calendar
    KnowledgeAction --> KnowledgeBase
    NotificationAction --> Communications

    LKAgents --> PostgreSQL
    LKAgents --> Redis
    LKAgents --> Analytics
```

### LiveKit Agents Framework Benefits

- **No Custom WebRTC**: LiveKit handles all real-time audio processing
- **Built-in Orchestration**: Agent framework manages STT→LLM→TTS flow
- **Production-Ready**: Auto-scaling, monitoring, and reliability built-in
- **Telephony Integration**: Direct phone system connectivity
- **Plugin Ecosystem**: Pre-built integrations for major services

## Components and Interfaces

### LiveKit Agent Core

**Main Agent Class:**

```python
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import assemblyai, google, elevenlabs

class CustomerSupportAgent:
    def __init__(self):
        self.stt = assemblyai.STT(
            api_key=os.getenv("ASSEMBLYAI_API_KEY"),
            word_boost=["appointment", "scheduling", "support", "billing"],
            speech_model=assemblyai.SpeechModel.BEST
        )

        self.llm = google.LLM(
            model="gemini-2.0-flash-exp",
            api_key=os.getenv("GOOGLE_API_KEY")
        )

        self.tts = elevenlabs.TTS(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice="professional_voice_id"
        )

    async def entrypoint(self, ctx: JobContext):
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        assistant = VoiceAssistant(
            vad=ctx.room.local_participant.create_vad(),
            stt=self.stt,
            llm=self.llm,
            tts=self.tts,
            chat_ctx=self._create_chat_context()
        )

        assistant.start(ctx.room)
        await assistant.aclose()
```

### Intent Detection and Routing

**Intent Router:**

```python
class IntentRouter:
    def __init__(self, llm: llm.LLM):
        self.llm = llm
        self.support_agent = SupportAgentModule()
        self.scheduling_agent = SchedulingAgentModule()

    async def route_conversation(self, message: str, context: dict) -> str:
        intent_prompt = f"""
        Analyze this customer message and determine if they need:
        1. SUPPORT - technical issues, billing questions, general help
        2. SCHEDULING - book appointment, reschedule, cancel, check availability

        Message: {message}
        Context: {context}

        Respond with just: SUPPORT or SCHEDULING
        """

        intent = await self.llm.achat(intent_prompt)

        if "SCHEDULING" in intent.content:
            return await self.scheduling_agent.handle_request(message, context)
        else:
            return await self.support_agent.handle_request(message, context)
```

### Customer Support Module

**Support Agent with RAG:**

```python
class SupportAgentModule:
    def __init__(self):
        self.knowledge_base = KnowledgeBaseConnector()
        self.crm_connector = CRMConnector()

    async def handle_request(self, message: str, context: dict) -> str:
        # Get customer info from CRM
        customer_info = await self.crm_connector.get_customer_by_phone(
            context.get("caller_phone")
        )

        # Search knowledge base
        relevant_docs = await self.knowledge_base.search(message)

        # Generate contextual response
        support_prompt = f"""
        You are a professional customer support agent.

        Customer: {customer_info}
        Question: {message}
        Knowledge Base Results: {relevant_docs}

        Provide helpful, professional support. If you cannot resolve the issue,
        offer to escalate to a human agent.
        """

        return support_prompt
```

### Appointment Scheduling Module

**Scheduling Agent with Calendar Integration:**

```python
class SchedulingAgentModule:
    def __init__(self):
        self.calendar_connector = CalendarConnector()
        self.notification_service = NotificationService()

    async def handle_request(self, message: str, context: dict) -> str:
        # Parse scheduling intent
        scheduling_info = await self._extract_scheduling_details(message)

        if scheduling_info["action"] == "book":
            return await self._handle_booking(scheduling_info, context)
        elif scheduling_info["action"] == "reschedule":
            return await self._handle_reschedule(scheduling_info, context)
        elif scheduling_info["action"] == "cancel":
            return await self._handle_cancellation(scheduling_info, context)
        else:
            return await self._show_availability(scheduling_info, context)

    async def _handle_booking(self, info: dict, context: dict) -> str:
        # Check availability
        available_slots = await self.calendar_connector.get_availability(
            date=info["date"],
            duration=info["duration"]
        )

        if available_slots:
            # Book appointment
            appointment = await self.calendar_connector.book_appointment({
                "date": info["date"],
                "time": info["time"],
                "customer_phone": context["caller_phone"],
                "service": info["service"]
            })

            # Send confirmation
            await self.notification_service.send_confirmation(appointment)

            return f"Great! I've booked your appointment for {info['date']} at {info['time']}. You'll receive a confirmation email shortly."
        else:
            return f"I don't have availability at {info['time']} on {info['date']}. Here are some alternative times: {available_slots[:3]}"
```

## Data Models

### LiveKit Agent Context

```python
@dataclass
class ConversationContext:
    session_id: str
    caller_phone: str
    customer_id: Optional[str]
    current_intent: str
    conversation_history: List[dict]
    business_data: dict
    created_at: datetime

@dataclass
class CustomerInfo:
    customer_id: str
    name: str
    phone: str
    email: str
    previous_appointments: List[dict]
    support_history: List[dict]
    preferences: dict

@dataclass
class AppointmentSlot:
    date: str
    time: str
    duration: int
    service_type: str
    available: bool
    provider: Optional[str]
```

### Integration Actions

```python
class LiveKitAction:
    """Base class for LiveKit agent actions"""

    async def execute(self, params: dict, context: ConversationContext) -> dict:
        raise NotImplementedError

class CRMAction(LiveKitAction):
    async def get_customer(self, phone: str) -> CustomerInfo:
        # CRM API integration
        pass

    async def create_ticket(self, issue: dict) -> str:
        # Create support ticket
        pass

class CalendarAction(LiveKitAction):
    async def check_availability(self, date: str, time: str) -> List[AppointmentSlot]:
        # Calendar API integration
        pass

    async def book_appointment(self, appointment: dict) -> str:
        # Book appointment
        pass
```

## Error Handling

### LiveKit Agent Error Handling

```python
class AgentErrorHandler:
    def __init__(self, assistant: VoiceAssistant):
        self.assistant = assistant

    async def handle_stt_error(self, error: Exception):
        """Handle speech recognition errors"""
        await self.assistant.say(
            "I'm having trouble hearing you clearly. Could you please repeat that?"
        )

    async def handle_llm_error(self, error: Exception):
        """Handle LLM processing errors"""
        await self.assistant.say(
            "I'm experiencing a technical issue. Let me connect you with a human agent."
        )
        await self._escalate_to_human()

    async def handle_integration_error(self, service: str, error: Exception):
        """Handle external service errors"""
        fallback_messages = {
            "crm": "I can't access your account right now, but I can still help you.",
            "calendar": "The scheduling system is temporarily unavailable. Can I take your information and call you back?",
            "knowledge_base": "Let me connect you with a specialist who can help."
        }

        await self.assistant.say(fallback_messages.get(service, "I'm experiencing technical difficulties."))
```

## Testing Strategy

### LiveKit Agent Testing

**1. Agent Playground Testing:**

- Use LiveKit Agents Playground for real-time testing
- Test conversation flows without building frontend
- Validate STT→LLM→TTS pipeline performance

**2. Integration Testing:**

```python
import pytest
from livekit.agents.test import AgentTestCase

class TestCustomerSupportAgent(AgentTestCase):
    async def test_support_conversation_flow(self):
        # Test complete support conversation
        responses = await self.simulate_conversation([
            "I need help with my billing",
            "I was charged twice last month",
            "My account number is 12345"
        ])

        assert "billing" in responses[0].lower()
        assert "human agent" in responses[-1].lower() or "resolved" in responses[-1].lower()

    async def test_appointment_booking_flow(self):
        # Test appointment booking
        responses = await self.simulate_conversation([
            "I'd like to schedule an appointment",
            "Next Tuesday at 2 PM",
            "Yes, that works for me"
        ])

        assert "appointment" in responses[0].lower()
        assert "confirmed" in responses[-1].lower()
```

**3. Performance Testing:**

- Latency testing: <500ms end-to-end response time
- Concurrent call handling with LiveKit Cloud scaling
- Speech recognition accuracy with business terminology

## Deployment Strategy

### LiveKit Cloud Deployment

**Environment Configuration:**

```bash
# Production environment variables
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-production-api-key
LIVEKIT_API_SECRET=your-production-secret
ASSEMBLYAI_API_KEY=your-assemblyai-key
GOOGLE_API_KEY=your-google-gemini-key
ELEVENLABS_API_KEY=your-elevenlabs-key

# Database connections
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379

# External service APIs
CRM_API_URL=https://your-crm-api.com
CALENDAR_API_URL=https://your-calendar-api.com
```

**Production Deployment:**

```python
# Deploy to LiveKit Cloud
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=CustomerSupportAgent().entrypoint,
            prewarm_fnc=prewarm_process
        )
    )
```

### Monitoring and Analytics

**LiveKit Built-in Analytics:**

- Call duration and quality metrics
- Speech recognition accuracy
- Response latency tracking
- Concurrent call handling

**Custom Business Metrics:**

- First-call resolution rate
- Appointment booking conversion
- Customer satisfaction scores
- Escalation rates

This design leverages LiveKit's proven infrastructure while focusing development effort on business logic rather than infrastructure complexity.
