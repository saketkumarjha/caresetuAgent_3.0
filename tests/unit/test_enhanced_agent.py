"""
Test the enhanced agent with both support and calendar capabilities
"""

import asyncio
import logging
from agent import BusinessVoiceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-enhanced-agent")

async def test_enhanced_agent():
    """Test the enhanced agent with mixed requests"""
    
    print("🤖 Testing Enhanced Agent with Calendar Integration")
    print("=" * 55)
    
    try:
        # Initialize the enhanced agent
        print("🔧 Initializing enhanced agent...")
        agent = BusinessVoiceAgent()
        print("✅ Enhanced agent initialized successfully")
        
        # Test different types of requests
        test_scenarios = [
            # Calendar requests
            ("Calendar", "I need to book an appointment"),
            ("Calendar", "What times are available tomorrow?"),
            ("Calendar", "Can I schedule something for next week?"),
            
            # Support requests (will use RAG)
            ("Support", "What services does CareSetu offer?"),
            ("Support", "How do I download the app?"),
            ("Support", "What are your business hours?"),
            
            # Mixed requests
            ("Mixed", "I have a health question and want to book an appointment"),
        ]
        
        print(f"\n🎭 Testing Different Request Types:")
        print("-" * 45)
        
        for category, scenario in test_scenarios:
            print(f"\n📂 Category: {category}")
            print(f"👤 Customer: {scenario}")
            
            # Check intent detection
            is_calendar = agent.detect_calendar_intent(scenario)
            print(f"🎯 Calendar Intent Detected: {is_calendar}")
            
            # Generate response using RAG-enhanced method
            try:
                response = await agent._generate_rag_enhanced_response(scenario, "test_session")
                if response:
                    print(f"🤖 Agent: {response}")
                else:
                    print(f"🤖 Agent: [No specific response - would use general LLM]")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Test calendar status
        print(f"\n📊 System Status:")
        print(f"   Calendar Available: {agent.calendar is not None}")
        print(f"   RAG Engine Available: {agent.rag_engine is not None}")
        print(f"   Knowledge Base Available: {agent.knowledge_base is not None}")
        
        print(f"\n✅ Enhanced agent testing completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_agent())