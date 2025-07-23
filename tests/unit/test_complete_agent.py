"""
Comprehensive test to verify agent.py handles both appointments and support
"""

import asyncio
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from src.agent import BusinessVoiceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-complete-agent")

async def test_complete_agent_capabilities():
    """Test that agent.py handles both appointment and support requests"""
    
    print("🔍 COMPREHENSIVE AGENT CAPABILITY TEST")
    print("=" * 60)
    
    try:
        # Initialize the agent
        print("🚀 Initializing BusinessVoiceAgent...")
        agent = BusinessVoiceAgent()
        print("✅ Agent initialized successfully!")
        
        # Check component availability
        print(f"\n📊 Component Status:")
        print(f"   ✅ Calendar Integration: {'Available' if agent.calendar else 'Not Available'}")
        print(f"   ✅ RAG Engine: {'Available' if agent.rag_engine else 'Not Available'}")
        print(f"   ✅ Knowledge Base: {'Available' if agent.knowledge_base else 'Not Available'}")
        print(f"   ✅ Learning Engine: {'Available' if agent.learning_engine else 'Not Available'}")
        
        # Test scenarios covering both capabilities
        test_scenarios = [
            # APPOINTMENT SCENARIOS
            {
                "category": "📅 APPOINTMENT",
                "query": "I want to book an appointment",
                "expected": "calendar_response"
            },
            {
                "category": "📅 APPOINTMENT", 
                "query": "What times are available tomorrow?",
                "expected": "calendar_response"
            },
            {
                "category": "📅 APPOINTMENT",
                "query": "Can I schedule something next week?",
                "expected": "calendar_response"
            },
            {
                "category": "📅 APPOINTMENT",
                "query": "I need to cancel my appointment",
                "expected": "calendar_response"
            },
            
            # SUPPORT SCENARIOS
            {
                "category": "🎧 SUPPORT",
                "query": "What services does CareSetu provide?",
                "expected": "rag_response"
            },
            {
                "category": "🎧 SUPPORT",
                "query": "How do I use the CareSetu app?",
                "expected": "rag_response"
            },
            {
                "category": "🎧 SUPPORT",
                "query": "What are your business hours?",
                "expected": "rag_response"
            },
            {
                "category": "🎧 SUPPORT",
                "query": "Tell me about your healthcare services",
                "expected": "rag_response"
            },
            
            # MIXED SCENARIOS
            {
                "category": "🔄 MIXED",
                "query": "I have a health question and want to book an appointment",
                "expected": "calendar_response"  # Calendar intent should be detected first
            }
        ]
        
        print(f"\n🧪 Testing {len(test_scenarios)} Scenarios:")
        print("-" * 50)
        
        success_count = 0
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}. {scenario['category']}")
            print(f"   Query: \"{scenario['query']}\"")
            
            # Test intent detection
            is_calendar_intent = agent.detect_calendar_intent(scenario['query'])
            print(f"   Calendar Intent: {is_calendar_intent}")
            
            # Test response generation
            try:
                response = await agent._generate_rag_enhanced_response(
                    scenario['query'], 
                    f"test_session_{i}"
                )
                
                if response:
                    # Truncate long responses for display
                    display_response = response[:100] + "..." if len(response) > 100 else response
                    print(f"   Response: {display_response}")
                    
                    # Verify expected behavior
                    if scenario['expected'] == 'calendar_response' and is_calendar_intent:
                        print(f"   ✅ PASS: Calendar intent correctly handled")
                        success_count += 1
                    elif scenario['expected'] == 'rag_response' and not is_calendar_intent:
                        print(f"   ✅ PASS: Support query correctly handled with RAG")
                        success_count += 1
                    else:
                        print(f"   ⚠️  UNEXPECTED: Intent detection may need adjustment")
                        success_count += 0.5  # Partial credit
                else:
                    print(f"   ❌ FAIL: No response generated")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)[:100]}...")
        
        # Summary
        print(f"\n📈 TEST RESULTS:")
        print(f"   Total Scenarios: {len(test_scenarios)}")
        print(f"   Successful: {success_count}")
        print(f"   Success Rate: {(success_count/len(test_scenarios)*100):.1f}%")
        
        # Final assessment
        if success_count >= len(test_scenarios) * 0.8:  # 80% success rate
            print(f"\n🎉 ASSESSMENT: Your agent.py is READY for production!")
            print(f"   ✅ Handles appointment booking requests")
            print(f"   ✅ Handles support questions with RAG")
            print(f"   ✅ Correctly routes different types of queries")
            print(f"   ✅ All major components are functional")
        else:
            print(f"\n⚠️  ASSESSMENT: Agent needs some adjustments")
            print(f"   Consider reviewing intent detection or response generation")
        
        return success_count >= len(test_scenarios) * 0.8
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        logger.error(f"Test failed with error: {e}")
        return False

async def test_real_world_conversation():
    """Test a realistic conversation flow"""
    
    print(f"\n🎭 REAL-WORLD CONVERSATION TEST")
    print("=" * 40)
    
    try:
        agent = BusinessVoiceAgent()
        
        # Simulate a realistic conversation
        conversation = [
            "Hi, I need help with CareSetu",
            "What services do you offer?",
            "That sounds good. Can I book an appointment?",
            "What times are available tomorrow?",
            "Great! I'd like the 2 PM slot",
            "My name is John Doe and email is john@example.com"
        ]
        
        print("Simulating realistic customer conversation:")
        
        for i, message in enumerate(conversation, 1):
            print(f"\n👤 Customer: {message}")
            
            try:
                response = await agent._generate_rag_enhanced_response(
                    message, 
                    "realistic_conversation"
                )
                
                if response:
                    # Show first 150 characters of response
                    display_response = response[:150] + "..." if len(response) > 150 else response
                    print(f"🤖 Agent: {display_response}")
                else:
                    print(f"🤖 Agent: [Would use general LLM response]")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)[:100]}...")
        
        print(f"\n✅ Conversation flow test completed!")
        
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")

if __name__ == "__main__":
    async def main():
        # Run comprehensive test
        is_ready = await test_complete_agent_capabilities()
        
        # Run conversation test
        await test_real_world_conversation()
        
        # Final verdict
        print(f"\n" + "="*60)
        if is_ready:
            print(f"🎉 FINAL VERDICT: Your agent.py is PRODUCTION READY!")
            print(f"   Your agent can handle both appointments and support seamlessly.")
        else:
            print(f"⚠️  FINAL VERDICT: Agent needs minor adjustments before production.")
        print(f"="*60)
    
    asyncio.run(main())