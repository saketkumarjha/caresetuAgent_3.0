"""Support Conversation Flows with Multi-step Handling and Context Awareness."""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict

from conversation_context import ConversationContextManager, ContextType, ConversationMemory

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """States in support conversation flow."""
    GREETING = "greeting"
    PROBLEM_IDENTIFICATION = "problem_identification"
    INFORMATION_GATHERING = "information_gathering"
    SOLUTION_PROVIDING = "solution_providing"
    VERIFICATION = "verification"
    ESCALATION = "escalation"
    RESOLUTION = "resolution"

class IssueCategory(Enum):
    """Categories of support issues."""
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    SCHEDULING = "scheduling"
    COMPLAINT = "complaint"
    GENERAL = "general"

class EscalationLevel(Enum):
    """Escalation levels for support issues."""
    TIER_1 = "tier_1"  # Agent can handle
    TIER_2 = "tier_2"  # Specialist required
    TIER_3 = "tier_3"  # Manager/Expert required

@dataclass
class EscalationRule:
    """Rule for determining when to escalate."""
    issue_categories: List[IssueCategory]
    trigger_keywords: List[str]
    conditions: Dict[str, Any]  # e.g., {"escalation_count": 2, "solution_attempts": 3}
    escalation_level: EscalationLevel
    reason: str

@dataclass
class ConversationStep:
    """Individual step in conversation flow."""
    state: ConversationState
    required_info: List[str]  # Information needed to complete this step
    collected_info: Dict[str, Any]  # Information collected so far
    next_expected: str  # What we expect from user next
    step_description: str  # Description of current step

@dataclass
class QualityMetrics:
    """Quality metrics for conversation analysis."""
    resolution_time: float  # Time to resolution in seconds
    customer_satisfaction: float  # 0.0 to 1.0
    escalation_count: int
    solution_attempts: int
    agent_performance: float  # 0.0 to 1.0
    knowledge_sources_used: int
    confidence_average: float

class SupportConversationFlows:
    """
    Manages multi-step support conversation flows with context awareness.
    Handles escalation matrix, quality assurance, and conversation analytics.
    """
    
    def __init__(self, context_manager: ConversationContextManager):
        """
        Initialize support conversation flows.
        
        Args:
            context_manager: Conversation context manager for memory retention
        """
        self.context_manager = context_manager
        
        # Active conversation flows
        self.active_flows: Dict[str, Dict[str, Any]] = {}
        
        # Quality metrics tracking
        self.quality_metrics: Dict[str, QualityMetrics] = {}
        
        # Escalation rules matrix
        self.escalation_rules = self._initialize_escalation_rules()
        
        logger.info("✅ Support Conversation Flows initialized")
    
    def _initialize_escalation_rules(self) -> List[EscalationRule]:
        """Initialize escalation rules matrix."""
        return [
            # Technical issues - escalate after multiple failed attempts
            EscalationRule(
                issue_categories=[IssueCategory.TECHNICAL],
                trigger_keywords=["not working", "broken", "error", "bug", "system"],
                conditions={"solution_attempts": 3},
                escalation_level=EscalationLevel.TIER_2,
                reason="Multiple failed technical troubleshooting attempts"
            ),
            
            # Billing issues - escalate for complex billing disputes
            EscalationRule(
                issue_categories=[IssueCategory.BILLING],
                trigger_keywords=["refund", "charge", "billing", "payment", "invoice"],
                conditions={"escalation_count": 1},
                escalation_level=EscalationLevel.TIER_2,
                reason="Billing dispute requires specialist review"
            ),
            
            # Complaints - immediate escalation for serious complaints
            EscalationRule(
                issue_categories=[IssueCategory.COMPLAINT],
                trigger_keywords=["complaint", "manager", "supervisor", "unhappy", "terrible"],
                conditions={"immediate": True},
                escalation_level=EscalationLevel.TIER_3,
                reason="Customer complaint requires management attention"
            ),
            
            # General escalation triggers
            EscalationRule(
                issue_categories=[IssueCategory.GENERAL],
                trigger_keywords=["escalation", "human", "agent", "person"],
                conditions={"conversation_length": 4},
                escalation_level=EscalationLevel.TIER_2,
                reason="Customer requested human assistance"
            )
        ]
    
    async def start_conversation_flow(self, session_id: str, user_message: str,
                                   issue_category: IssueCategory,
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a new support conversation flow.
        
        Args:
            session_id: Unique session identifier
            user_message: Initial user message
            issue_category: Detected issue category
            context: Additional context information
            
        Returns:
            Response dictionary with next steps
        """
        
        logger.info(f"🚀 Starting conversation flow for session: {session_id}")
        
        # Initialize conversation flow state
        flow_state = {
            "session_id": session_id,
            "issue_category": issue_category,
            "current_state": ConversationState.GREETING,
            "current_step_index": 0,
            "steps": self._get_flow_template(issue_category),
            "escalation_count": 0,
            "solution_attempts": 0,
            "started_at": datetime.now(),
            "resolved": False
        }
        
        self.active_flows[session_id] = flow_state
        
        # Initialize quality metrics
        self.quality_metrics[session_id] = QualityMetrics(
            resolution_time=0.0,
            customer_satisfaction=0.0,
            escalation_count=0,
            solution_attempts=0,
            agent_performance=0.0,
            knowledge_sources_used=0,
            confidence_average=0.0
        )
        
        # Process the initial message
        return await self.process_step(session_id, user_message, context)
    
    def _get_flow_template(self, issue_category: IssueCategory) -> List[Dict[str, Any]]:
        """Get conversation flow template based on issue category."""
        
        if issue_category == IssueCategory.TECHNICAL:
            return [
                {
                    "state": ConversationState.GREETING,
                    "required_info": [],
                    "collected_info": {},
                    "next_expected": "problem_description",
                    "step_description": "Greet customer and acknowledge technical issue"
                },
                {
                    "state": ConversationState.PROBLEM_IDENTIFICATION,
                    "required_info": ["device_type", "browser", "error_message"],
                    "collected_info": {},
                    "next_expected": "technical_details",
                    "step_description": "Identify specific technical problem"
                },
                {
                    "state": ConversationState.INFORMATION_GATHERING,
                    "required_info": ["steps_to_reproduce", "when_started"],
                    "collected_info": {},
                    "next_expected": "troubleshooting_info",
                    "step_description": "Gather detailed troubleshooting information"
                },
                {
                    "state": ConversationState.SOLUTION_PROVIDING,
                    "required_info": [],
                    "collected_info": {},
                    "next_expected": "solution_feedback",
                    "step_description": "Provide step-by-step solution"
                },
                {
                    "state": ConversationState.VERIFICATION,
                    "required_info": [],
                    "collected_info": {},
                    "next_expected": "verification_response",
                    "step_description": "Verify solution worked"
                }
            ]
        
        elif issue_category == IssueCategory.BILLING:
            return [
                {
                    "state": ConversationState.GREETING,
                    "required_info": [],
                    "collected_info": {},
                    "next_expected": "billing_question",
                    "step_description": "Greet customer and acknowledge billing inquiry"
                },
                {
                    "state": ConversationState.PROBLEM_IDENTIFICATION,
                    "required_info": ["account_number", "billing_period", "issue_description"],
                    "collected_info": {},
                    "next_expected": "billing_details",
                    "step_description": "Identify specific billing issue"
                },
                {
                    "state": ConversationState.SOLUTION_PROVIDING,
                    "required_info": [],
                    "collected_info": {},
                    "next_expected": "solution_acceptance",
                    "step_description": "Provide billing resolution"
                },
                {
                    "state": ConversationState.VERIFICATION,
                    "required_info": [],
                    "collected_info": {},
                    "next_expected": "satisfaction_confirmation",
                    "step_description": "Confirm billing issue resolved"
                }
            ]
        
        else:  # General support flow
            return [
                {
                    "state": ConversationState.GREETING,
                    "required_info": [],
                    "collected_info": {},
                    "next_expected": "customer_inquiry",
                    "step_description": "Greet customer and understand inquiry"
                },
                {
                    "state": ConversationState.PROBLEM_IDENTIFICATION,
                    "required_info": ["issue_description"],
                    "collected_info": {},
                    "next_expected": "problem_details",
                    "step_description": "Identify customer's specific need"
                },
                {
                    "state": ConversationState.SOLUTION_PROVIDING,
                    "required_info": [],
                    "collected_info": {},
                    "next_expected": "solution_feedback",
                    "step_description": "Provide appropriate solution or information"
                },
                {
                    "state": ConversationState.VERIFICATION,
                    "required_info": [],
                    "collected_info": {},
                    "next_expected": "final_confirmation",
                    "step_description": "Ensure customer needs are met"
                }
            ]
    
    async def process_step(self, session_id: str, user_message: str,
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process current conversation step with context awareness.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            context: Conversation context
            
        Returns:
            Response with next step guidance
        """
        
        if session_id not in self.active_flows:
            logger.error(f"❌ No active flow found for session: {session_id}")
            return await self._handle_general_response(session_id, user_message, context)
        
        flow_state = self.active_flows[session_id]
        current_step = flow_state["steps"][flow_state["current_step_index"]]
        state = ConversationState(current_step["state"])
        
        # Process based on current conversation state
        if state == ConversationState.GREETING:
            response = await self._handle_greeting_state(session_id, user_message, context)
        elif state == ConversationState.PROBLEM_IDENTIFICATION:
            response = await self._handle_problem_identification(session_id, user_message, context)
        elif state == ConversationState.INFORMATION_GATHERING:
            response = await self._handle_information_gathering(session_id, user_message, context)
        elif state == ConversationState.SOLUTION_PROVIDING:
            response = await self._handle_solution_providing(session_id, user_message, context)
        elif state == ConversationState.VERIFICATION:
            response = await self._handle_verification(session_id, user_message, context)
        else:
            response = await self._handle_general_response(session_id, user_message, context)
        
        # Update quality metrics
        await self._update_quality_metrics(session_id, response)
        
        # Check for escalation triggers
        escalation_needed, escalation_reason = await self._check_escalation_triggers(
            user_message, current_step, flow_state
        )
        
        if escalation_needed:
            logger.info(f"🚨 Escalation triggered for session {session_id}: {escalation_reason}")
            await self._handle_escalation(session_id, user_message, response, escalation_reason)
        
        return response
    
    async def _handle_greeting_state(self, session_id: str, user_message: str,
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle greeting state with personalized response."""
        
        flow_state = self.active_flows[session_id]
        
        # Personalize greeting based on customer history
        customer_history = context.get("customer_history", {})
        if customer_history.get("previous_interactions", 0) > 0:
            greeting = f"Hello! I see you've contacted us before. I'm here to help with your {flow_state['issue_category'].value} inquiry."
        else:
            greeting = f"Hello! I'm here to help you with your {flow_state['issue_category'].value} question. Is there something specific I can assist you with today?"
        
        # Advance to next step
        await self._advance_to_next_step(session_id)
        
        return {
            "response": greeting,
            "sources_used": [],
            "confidence": 0.9,
            "escalation_needed": False,
            "next_expected": "problem_description",
            "session_id": session_id,
            "current_step": flow_state["current_step_index"],
            "total_steps": len(flow_state["steps"])
        }
    
    async def _handle_problem_identification(self, session_id: str, user_message: str,
                                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle problem identification with targeted questions."""
        
        flow_state = self.active_flows[session_id]
        current_step = flow_state["steps"][flow_state["current_step_index"]]
        
        # Extract information from user message
        extracted_info = await self._extract_information(user_message, current_step["required_info"])
        
        # Update collected information
        current_step["collected_info"].update(extracted_info)
        
        # Analyze problem description
        problem_analysis = await self._analyze_problem_description(user_message, flow_state["issue_category"])
        
        # Generate targeted follow-up questions based on issue category
        if flow_state["issue_category"] == IssueCategory.TECHNICAL:
            if "error" in user_message.lower():
                follow_up = "Can you describe the exact error message you're seeing and when this issue first appeared?"
            elif "browser" in user_message.lower():
                follow_up = "Which web browser are you using? For example, Chrome, Safari, Firefox, or Edge?"
            else:
                follow_up = "To help troubleshoot this, I need to know: What device are you using, and does this happen every time or only sometimes?"
        
        elif flow_state["issue_category"] == IssueCategory.BILLING:
            follow_up = "I'll help you with your billing question. Can you provide your account number and tell me which billing period you're asking about?"
        
        else:
            follow_up = f"I understand you need help with {flow_state['issue_category'].value}. Can you provide a bit more detail about what you're trying to accomplish?"
        
        # Check if step is complete
        if self._is_step_complete(current_step):
            await self._advance_to_next_step(session_id)
        
        return {
            "response": follow_up,
            "sources_used": [],
            "confidence": 0.8,
            "escalation_needed": False,
            "problem_analysis": problem_analysis,
            "collected_info": current_step["collected_info"],
            "session_id": session_id,
            "current_step": flow_state["current_step_index"],
            "total_steps": len(flow_state["steps"])
        }
    
    async def _handle_information_gathering(self, session_id: str, user_message: str,
                                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle information gathering with missing info requests."""
        
        flow_state = self.active_flows[session_id]
        current_step = flow_state["steps"][flow_state["current_step_index"]]
        
        # Extract information from user message
        extracted_info = await self._extract_information(user_message, current_step["required_info"])
        current_step["collected_info"].update(extracted_info)
        
        # Check what information is still missing
        missing_info = []
        for required in current_step["required_info"]:
            if required not in current_step["collected_info"] or not current_step["collected_info"][required]:
                missing_info.append(required)
        
        if missing_info:
            # Ask for missing information
            if "device_type" in missing_info:
                response = "What device are you using? For example, computer, tablet, or phone?"
            elif "browser" in missing_info:
                response = "Which web browser are you using? Chrome, Safari, Firefox, or another browser?"
            elif "steps_to_reproduce" in missing_info:
                response = "Can you walk me through exactly what happens when you try to access the system?"
            else:
                response = f"I need a bit more information. Can you provide {', '.join(missing_info).replace('_', ' ')}?"
            
            return {
                "response": response,
                "sources_used": [],
                "confidence": 0.8,
                "escalation_needed": False,
                "missing_info": missing_info,
                "next_expected": "required_information",
                "session_id": session_id,
                "current_step": flow_state["current_step_index"],
                "total_steps": len(flow_state["steps"])
            }
        
        else:
            # All information collected, move to solution
            await self._advance_to_next_step(session_id)
            
            return {
                "response": "Thank you for that information. Let me find the best solution for your situation.",
                "sources_used": [],
                "confidence": 0.9,
                "escalation_needed": False,
                "collected_info": current_step["collected_info"],
                "session_id": session_id,
                "current_step": flow_state["current_step_index"],
                "total_steps": len(flow_state["steps"])
            }
    
    async def _handle_solution_providing(self, session_id: str, user_message: str,
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solution providing with contextual solutions."""
        
        flow_state = self.active_flows[session_id]
        current_step = flow_state["steps"][flow_state["current_step_index"]]
        
        # Get collected information from previous steps
        collected_info = current_step["collected_info"]
        for step in flow_state["steps"][:flow_state["current_step_index"]]:
            collected_info.update(step["collected_info"])
        
        # Generate contextual solution based on collected information
        solution = await self._generate_contextual_solution(collected_info, flow_state["issue_category"])
        
        # Increment solution attempts
        flow_state["solution_attempts"] += 1
        
        response_text = f"Based on what you've told me, here's what I recommend: {solution['steps']}. Would you like to try this solution?"
        
        await self._advance_to_next_step(session_id)
        
        return {
            "response": response_text,
            "sources_used": solution.get("sources_used", []),
            "confidence": solution.get("confidence", 0.8),
            "escalation_needed": False,
            "solution_provided": solution,
            "session_id": session_id,
            "current_step": flow_state["current_step_index"],
            "total_steps": len(flow_state["steps"])
        }
    
    async def _handle_verification(self, session_id: str, user_message: str,
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solution verification and follow-up."""
        
        flow_state = self.active_flows[session_id]
        escalation_needed = False
        
        # Check if solution worked
        if any(word in user_message.lower() for word in ["yes", "worked", "fixed", "resolved", "good"]):
            # Solution successful
            await self._mark_conversation_resolved(session_id, True)
            response = "Great! I'm glad that resolved your issue. Is there anything else I can help you with today?"
        
        elif any(word in user_message.lower() for word in ["no", "didn't work", "still", "not working"]):
            # Solution didn't work
            escalation_needed = True
            response = "I understand the solution didn't work. Let me try a different approach or connect you with a specialist who can provide additional help."
        
        else:
            # Need clarification
            response = "Did that solution work for you? Please let me know if your issue is resolved or if you need additional assistance."
        
        # Update quality metrics
        await self._update_quality_metrics(session_id, {"solution_successful": "yes" in user_message.lower()})
        
        return {
            "response": response,
            "sources_used": [],
            "confidence": 0.9,
            "escalation_needed": escalation_needed,
            "session_id": session_id,
            "current_step": flow_state["current_step_index"],
            "total_steps": len(flow_state["steps"])
        }
    
    async def _handle_general_response(self, session_id: str, user_message: str,
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general response when no specific flow is active."""
        
        # Get conversation summary for context
        conversation_summary = await self.context_manager.get_conversation_summary(session_id)
        
        response = "I understand. Let me make sure I have all the information I need to help you effectively."
        
        return {
            "response": response,
            "sources_used": [],
            "confidence": 0.7,
            "escalation_needed": False,
            "session_id": session_id,
            "conversation_summary": conversation_summary
        }
    
    async def _extract_information(self, message: str, required_info: List[str]) -> Dict[str, Any]:
        """Extract required information from user message."""
        
        extracted = {}
        message_lower = message.lower()
        
        # Simple extraction logic (in production, use NLP)
        for info_type in required_info:
            if info_type == "device_type":
                if any(device in message_lower for device in ["computer", "laptop", "desktop"]):
                    extracted[info_type] = "computer"
                elif any(device in message_lower for device in ["phone", "mobile", "iphone", "android"]):
                    extracted[info_type] = "mobile"
                elif "tablet" in message_lower:
                    extracted[info_type] = "tablet"
            
            elif info_type == "browser":
                browsers = ["chrome", "firefox", "safari", "edge", "internet explorer"]
                for browser in browsers:
                    if browser in message_lower:
                        extracted[info_type] = browser
                        break
            
            elif info_type == "error_message":
                if "error" in message_lower:
                    extracted[info_type] = message  # In production, extract specific error
        
        return extracted
    
    async def _analyze_problem_description(self, message: str, issue_category: IssueCategory) -> Dict[str, Any]:
        """Analyze problem description and return analysis."""
        
        message_lower = message.lower()
        
        return {
            "keywords": message.lower().split(),
            "severity": "high" if any(word in message_lower for word in ["urgent", "critical", "emergency"]) else "medium",
            "complexity": "complex" if len(message.split()) > 20 else "standard",
            "category": issue_category.value
        }
    
    async def _generate_contextual_solution(self, collected_info: Dict[str, Any], 
                                          issue_category: IssueCategory) -> Dict[str, Any]:
        """Generate contextual solution based on collected information."""
        
        # Mock solution generation (in production, use knowledge base + LLM)
        if issue_category == IssueCategory.TECHNICAL:
            solution = {
                "steps": "1. Clear your browser cache and cookies. 2. Restart your browser. 3. Try accessing the system again.",
                "sources": ["Technical FAQ", "Browser Troubleshooting Guide"],
                "confidence": 0.8,
            }
        elif issue_category == IssueCategory.BILLING:
            solution = {
                "steps": "I can see the charge on your account. Let me verify the details and process any necessary adjustments.",
                "sources": ["Billing Policy", "Account Management Guide"],
                "confidence": 0.9,
            }
        else:
            solution = {
                "steps": "Based on your question, here's what I recommend...",
                "sources": ["General FAQ"],
                "confidence": 0.7
            }
        
        return solution
    
    def _is_step_complete(self, step: Dict[str, Any]) -> bool:
        """Check if current step has collected all required information."""
        
        required_info = step["required_info"]
        collected_info = step["collected_info"]
        
        # Check if all required information is collected
        for required in required_info:
            if required not in collected_info or not collected_info[required]:
                return False
        
        return True
    
    async def _advance_to_next_step(self, session_id: str):
        """Advance conversation to next step."""
        
        if session_id not in self.active_flows:
            return
        
        flow_state = self.active_flows[session_id]
        current_index = flow_state["current_step_index"]
        
        if current_index < len(flow_state["steps"]) - 1:
            flow_state["current_step_index"] += 1
            logger.info(f"📈 Advanced to step {flow_state['current_step_index']} for session {session_id}")
        else:
            # Conversation flow complete
            await self._mark_conversation_resolved(session_id, True)
    
    async def _mark_conversation_resolved(self, session_id: str, resolved: bool):
        """Mark conversation as resolved and update metrics."""
        
        if session_id not in self.active_flows:
            return
        
        flow_state = self.active_flows[session_id]
        flow_state["resolved"] = resolved
        flow_state["ended_at"] = datetime.now()
        
        # Update quality metrics
        if session_id in self.quality_metrics:
            metrics = self.quality_metrics[session_id]
            start_time = datetime.fromisoformat(flow_state.get("started_at", datetime.now()).isoformat())
            end_time = datetime.now()
            metrics.resolution_time = (end_time - start_time).total_seconds()
            
            quality_score = self._calculate_quality_score(flow_state)
            metrics.customer_satisfaction = quality_score
        
        logger.info(f"✅ Conversation {session_id} resolved: {resolved}")
    
    def _calculate_quality_score(self, flow_state: Dict[str, Any]) -> float:
        """Calculate conversation quality score."""
        
        score = 1.0
        
        # Deduct for escalations
        score -= (flow_state.get("escalation_count", 0) * 0.2)
        
        # Deduct for long conversations
        if flow_state.get("current_step_index", 0) > 5:
            score -= 0.1
        
        # Bonus for quick resolution
        if flow_state.get("current_step_index", 0) <= 3 and flow_state.get("resolved"):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _check_escalation_triggers(self, user_message: str, current_step: Dict[str, Any],
                                       flow_state: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if escalation is needed based on rules and conditions."""
        
        user_message_lower = user_message.lower()
        
        # Check escalation rules
        for rule in self.escalation_rules:
            # Check if issue category matches
            issue_category = IssueCategory(flow_state["issue_category"])
            if issue_category not in rule.issue_categories and IssueCategory.GENERAL not in rule.issue_categories:
                continue
            
            # Check keyword triggers
            if any(keyword.lower() in user_message_lower for keyword in rule.trigger_keywords):
                return True, f"Rule trigger: {rule.reason}"
            
            # Check conditional conditions
            if self._check_escalation_conditions(rule.conditions, flow_state):
                return True, f"Rule trigger: {rule.reason}"
        
        # Check step-specific escalation triggers
        if "escalation_triggers" in current_step:
            for trigger in current_step["escalation_triggers"]:
                if trigger.lower() in user_message_lower:
                    return True, f"Step trigger: {trigger}"
        
        # Check general escalation conditions
        if flow_state.get("escalation_count", 0) > 2:  # Multiple escalation attempts
            return True, "Multiple escalation attempts"
        
        if flow_state.get("current_step_index", 0) > 4:  # Long conversation
            return True, "Conversation length exceeded normal flow"
        
        return False, ""
    
    def _check_escalation_conditions(self, conditions: Dict[str, Any], flow_state: Dict[str, Any]) -> bool:
        """Check if escalation conditions are met."""
        
        for condition, value in conditions.items():
            if condition == "immediate" and value:
                return True
            elif condition == "escalation_count" and flow_state.get("escalation_count", 0) >= value:
                return True
            elif condition == "solution_attempts" and flow_state.get("solution_attempts", 0) > value:
                return True
            elif condition == "conversation_length" and flow_state.get("current_step_index", 0) > value:
                return True
        
        return False
    
    async def _handle_escalation(self, session_id: str, user_message: str, 
                               response_data: Dict[str, Any], escalation_reason: str):
        """Handle escalation to human agents."""
        
        if session_id in self.active_flows:
            self.active_flows[session_id]["escalation_count"] += 1
        
        # Update quality metrics
        if session_id in self.quality_metrics:
            metrics = self.quality_metrics[session_id]
            metrics.escalation_count += 1
        
        # Log escalation details
        escalation_data = {
            "session_id": session_id,
            "escalation_reason": escalation_reason,
            "conversation_summary": await self.context_manager.get_conversation_summary(session_id),
            "customer_context": response_data.get("customer_context"),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Generate escalation response
        escalation_response = "I understand this needs additional attention. Let me connect you with a specialist who can provide the help you need. Please hold for just a moment."
        
        # Update response data
        response_data.update({
            "escalation_needed": True,
            "escalation_reason": escalation_reason,
            "escalation_data": escalation_data,
            "response": escalation_response,
            "sources_used": [],
            "confidence": 1.0
        })
        
        logger.info(f"🚨 Escalation logged for session {session_id}: {escalation_reason}")
    
    async def _update_quality_metrics(self, session_id: str, step_response: Dict[str, Any]):
        """Update quality metrics based on conversation step."""
        
        if session_id not in self.quality_metrics:
            return
        
        metrics = self.quality_metrics[session_id]
        
        # Update confidence average
        confidence = step_response.get("confidence", 0.0)
        metrics.confidence_average = (metrics.confidence_average + confidence) / 2
        
        # Update knowledge sources used
        sources_used = step_response.get("sources_used", [])
        metrics.knowledge_sources_used += len(sources_used)
        
        # Update agent performance based on confidence
        agent_performance_score = (metrics.agent_performance + confidence) / 2
        metrics.agent_performance = max(0.0, min(1.0, agent_performance_score))
    
    async def get_conversation_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a conversation."""
        
        if session_id not in self.active_flows:
            return {"error": "Session not found"}
        
        flow_state = self.active_flows[session_id]
        metrics = self.quality_metrics.get(session_id)
        
        if not metrics:
            return {"error": "No metrics available"}
        
        return {
            "session_id": session_id,
            "issue_category": flow_state["issue_category"].value,
            "current_step": flow_state["current_step_index"],
            "total_steps": len(flow_state["steps"]),
            "escalation_count": flow_state["escalation_count"],
            "duration_minutes": self._calculate_duration(flow_state) / 60,
            "resolved": flow_state.get("resolved", False),
            "quality_metrics": {
                "confidence": metrics.confidence_average,
                "agent_performance": metrics.agent_performance,
                "knowledge_sources_used": metrics.knowledge_sources_used,
                "escalation_count": metrics.escalation_count
            }
        }
    
    def _calculate_duration(self, flow_state: Dict[str, Any]) -> float:
        """Calculate conversation duration in seconds."""
        
        start_time = flow_state.get("started_at")
        end_time = flow_state.get("ended_at", datetime.now())
        
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
        
        return (end_time - start_time).total_seconds()
    
    async def get_all_active_flows(self) -> List[Dict[str, Any]]:
        """Get all active conversation flows."""
        
        active_flows = []
        for session_id, flow_state in self.active_flows.items():
            active_flows.append({
                "session_id": session_id,
                "issue_category": flow_state["issue_category"].value,
                "current_step": flow_state["current_step_index"],
                "total_steps": len(flow_state["steps"]),
                "escalation_count": flow_state["escalation_count"],
                "duration_minutes": self._calculate_duration(flow_state) / 60,
                "resolved": flow_state.get("resolved", False)
            })
        
        return active_flows
    
    async def cleanup_completed_flows(self):
        """Clean up completed conversation flows."""
        
        completed_sessions = []
        for session_id, flow_state in self.active_flows.items():
            if flow_state.get("resolved") or flow_state.get("ended_at"):
                completed_sessions.append(session_id)
        
        for session_id in completed_sessions:
            # Archive flow data for analytics
            await self._archive_flow_data(session_id)
            
            # Remove from active flows
            if session_id in self.active_flows:
                del self.active_flows[session_id]
            
            if session_id in self.quality_metrics:
                del self.quality_metrics[session_id]
        
        if completed_sessions:
            logger.info(f"🧹 Cleaned up {len(completed_sessions)} completed flows")
    
    async def _archive_flow_data(self, session_id: str):
        """Archive completed flow data for analytics."""
        
        flow_data = {
            "session_id": session_id,
            "flow_state": self.active_flows.get(session_id),
            "quality_metrics": dict(asdict(self.quality_metrics[session_id])) if session_id in self.quality_metrics else None,
            "archived_at": datetime.now().isoformat()
        }
        
        # In production, save to database for analytics
        logger.info(f"📁 Archived flow data for session {session_id}")

# Test support conversation flows
async def test_conversation_flows():
    """Test support conversation flows."""
    
    print("🧪 Testing Support Conversation Flows")
    print("=" * 50)
    
    # Initialize context manager and flows
    from conversation_context import ConversationContextManager
    context_manager = ConversationContextManager()
    await context_manager.initialize()
    
    flows = SupportConversationFlows(context_manager)
    
    # Test technical support flow
    session_id = "test_tech_session"
    
    print("\n🔧 Testing Technical Support Flow")
    print("-" * 30)
    
    # Start conversation flow
    response1 = await flows.start_conversation_flow(
        session_id=session_id,
        user_message="My system is not working properly",
        issue_category=IssueCategory.TECHNICAL,
        context={"customer_phone": "+1234567890"}
    )
    
    print(f"Agent: {response1['response']}")
    
    # Continue conversation
    response2 = await flows.process_step(
        session_id=session_id,
        user_message="I'm getting an error when I try to log in",
        context={"customer_phone": "+1234567890"}
    )
    
    print(f"Agent: {response2['response']}")
    
    # Test escalation trigger
    response3 = await flows.process_step(
        session_id=session_id,
        user_message="This is urgent! The whole system is down!",
        context={"customer_phone": "+1234567890"}
    )
    
    print(f"Agent: {response3['response']}")
    print(f"Escalation needed: {response3['escalation_needed']}")
    
    # Get analytics
    analytics = await flows.get_conversation_analytics(session_id)
    print(f"\n📊 Conversation Analytics:")
    print(f"  Issue Category: {analytics['issue_category']}")
    print(f"  Current Step: {analytics['current_step']}/{analytics['total_steps']}")
    print(f"  Escalation Count: {analytics['escalation_count']}")
    print(f"  Duration: {analytics['duration_minutes']:.1f} minutes")
    
    # Test billing session
    billing_session = "test_billing_session"
    
    print("\n💰 Testing Billing Support Flow")
    print("-" * 30)
    
    billing_response = await flows.start_conversation_flow(
        session_id=billing_session,
        user_message="I was charged twice for my subscription",
        issue_category=IssueCategory.BILLING,
        context={"customer_phone": "+1234567890"}
    )
    
    print(f"Agent: {billing_response['response']}")
    
    # Get analytics
    analytics = await flows.get_conversation_analytics(billing_session)
    print(f"\n📊 Conversation Analytics:")
    print(f"  Issue Category: {analytics['issue_category']}")
    print(f"  Current Step: {analytics['current_step']}/{analytics['total_steps']}")
    print(f"  Escalation Count: {analytics['escalation_count']}")
    print(f"  Duration: {analytics['duration_minutes']:.1f} minutes")
    
    # Clean up
    await flows.cleanup_completed_flows()
    print(f"\n✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_conversation_flows())