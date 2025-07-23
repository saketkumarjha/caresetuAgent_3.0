"""
TTS Diagnostics and Configuration Utility
Helps diagnose and fix TTS connection issues
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional
import aiohttp
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tts-diagnostics")

class TTSDiagnostics:
    """Diagnostic utility for TTS services"""
    
    def __init__(self):
        self.results = {}
    
    async def test_network_connectivity(self) -> Dict[str, Any]:
        """Test basic network connectivity"""
        print("🌐 Testing Network Connectivity...")
        
        test_urls = [
            "https://google.com",
            "https://api.cartesia.ai",
            "https://api.elevenlabs.io",
        ]
        
        results = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for url in test_urls:
                try:
                    async with session.get(url) as response:
                        results[url] = {
                            'status': response.status,
                            'success': response.status < 400,
                            'error': None
                        }
                        print(f"  ✅ {url}: {response.status}")
                except Exception as e:
                    results[url] = {
                        'status': None,
                        'success': False,
                        'error': str(e)
                    }
                    print(f"  ❌ {url}: {e}")
        
        return results
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """Check TTS-related environment variables"""
        print("🔧 Checking Environment Variables...")
        
        required_vars = {
            'CARTESIA_API_KEY': 'Cartesia TTS API Key',
            'ELEVENLABS_API_KEY': 'ElevenLabs TTS API Key',
            'GOOGLE_API_KEY': 'Google API Key (for TTS)',
        }
        
        results = {}
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # Mask the key for security
                masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                results[var] = {
                    'present': True,
                    'value': masked_value,
                    'valid_format': self._validate_api_key_format(var, value)
                }
                status = "✅" if results[var]['valid_format'] else "⚠️"
                print(f"  {status} {description}: {masked_value}")
            else:
                results[var] = {
                    'present': False,
                    'value': None,
                    'valid_format': False
                }
                print(f"  ❌ {description}: Not set")
        
        return results
    
    def _validate_api_key_format(self, var_name: str, value: str) -> bool:
        """Validate API key format"""
        if var_name == 'CARTESIA_API_KEY':
            return value.startswith('sk_car_') and len(value) > 20
        elif var_name == 'ELEVENLABS_API_KEY':
            return len(value) > 20 and value != 'ELEVENLABS_API_KEY'
        elif var_name == 'GOOGLE_API_KEY':
            return value.startswith('AIza') and len(value) > 30
        return True
    
    async def test_cartesia_api(self) -> Dict[str, Any]:
        """Test Cartesia API connectivity"""
        print("🎵 Testing Cartesia API...")
        
        api_key = os.getenv('CARTESIA_API_KEY')
        if not api_key or not api_key.startswith('sk_car_'):
            return {
                'success': False,
                'error': 'Invalid or missing Cartesia API key'
            }
        
        try:
            # Test Cartesia API endpoint
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Test voices endpoint
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(
                    'https://api.cartesia.ai/voices',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ Cartesia API: {len(data)} voices available")
                        return {
                            'success': True,
                            'voices_count': len(data),
                            'error': None
                        }
                    else:
                        error_text = await response.text()
                        print(f"  ❌ Cartesia API: HTTP {response.status}")
                        return {
                            'success': False,
                            'status': response.status,
                            'error': error_text
                        }
        
        except Exception as e:
            print(f"  ❌ Cartesia API: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def test_elevenlabs_api(self) -> Dict[str, Any]:
        """Test ElevenLabs API connectivity"""
        print("🎤 Testing ElevenLabs API...")
        
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key or api_key == 'ELEVENLABS_API_KEY':
            return {
                'success': False,
                'error': 'Invalid or missing ElevenLabs API key'
            }
        
        try:
            headers = {
                'xi-api-key': api_key,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(
                    'https://api.elevenlabs.io/v1/voices',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        voices_count = len(data.get('voices', []))
                        print(f"  ✅ ElevenLabs API: {voices_count} voices available")
                        return {
                            'success': True,
                            'voices_count': voices_count,
                            'error': None
                        }
                    else:
                        error_text = await response.text()
                        print(f"  ❌ ElevenLabs API: HTTP {response.status}")
                        return {
                            'success': False,
                            'status': response.status,
                            'error': error_text
                        }
        
        except Exception as e:
            print(f"  ❌ ElevenLabs API: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_silero_availability(self) -> Dict[str, Any]:
        """Test Silero TTS availability (local)"""
        print("🔊 Testing Silero TTS...")
        
        try:
            # Try to import and initialize Silero
            from livekit.plugins import silero
            
            # Test basic initialization
            tts = silero.TTS()
            print("  ✅ Silero TTS: Available and working")
            return {
                'success': True,
                'error': None
            }
        
        except ImportError as e:
            print(f"  ❌ Silero TTS: Import error - {e}")
            return {
                'success': False,
                'error': f'Import error: {e}'
            }
        except Exception as e:
            print(f"  ❌ Silero TTS: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run complete TTS diagnostics"""
        print("🔍 Running Complete TTS Diagnostics")
        print("=" * 50)
        
        results = {}
        
        # Test network connectivity
        results['network'] = await self.test_network_connectivity()
        print()
        
        # Check environment variables
        results['environment'] = self.check_environment_variables()
        print()
        
        # Test Silero (local)
        results['silero'] = self.test_silero_availability()
        print()
        
        # Test Cartesia API
        results['cartesia'] = await self.test_cartesia_api()
        print()
        
        # Test ElevenLabs API
        results['elevenlabs'] = await self.test_elevenlabs_api()
        print()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results)
        
        return {
            'results': results,
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> list:
        """Generate recommendations based on diagnostic results"""
        recommendations = []
        
        # Check network issues
        network_results = results.get('network', {})
        failed_connections = [url for url, result in network_results.items() if not result['success']]
        if failed_connections:
            recommendations.append({
                'priority': 'high',
                'issue': 'Network connectivity problems',
                'solution': 'Check your internet connection and firewall settings',
                'details': f'Failed to connect to: {", ".join(failed_connections)}'
            })
        
        # Check API keys
        env_results = results.get('environment', {})
        missing_keys = [var for var, result in env_results.items() if not result['present']]
        invalid_keys = [var for var, result in env_results.items() if result['present'] and not result['valid_format']]
        
        if missing_keys:
            recommendations.append({
                'priority': 'medium',
                'issue': 'Missing API keys',
                'solution': 'Add missing API keys to your .env file',
                'details': f'Missing: {", ".join(missing_keys)}'
            })
        
        if invalid_keys:
            recommendations.append({
                'priority': 'medium',
                'issue': 'Invalid API key format',
                'solution': 'Check and update API keys in your .env file',
                'details': f'Invalid format: {", ".join(invalid_keys)}'
            })
        
        # Check TTS services
        silero_result = results.get('silero', {})
        cartesia_result = results.get('cartesia', {})
        elevenlabs_result = results.get('elevenlabs', {})
        
        working_services = []
        if silero_result.get('success'):
            working_services.append('Silero (local)')
        if cartesia_result.get('success'):
            working_services.append('Cartesia')
        if elevenlabs_result.get('success'):
            working_services.append('ElevenLabs')
        
        if not working_services:
            recommendations.append({
                'priority': 'critical',
                'issue': 'No TTS services available',
                'solution': 'Fix network connection or API keys, or install Silero TTS',
                'details': 'All TTS services failed - agent cannot function'
            })
        elif len(working_services) == 1 and 'Silero' in working_services[0]:
            recommendations.append({
                'priority': 'low',
                'issue': 'Only local TTS available',
                'solution': 'Consider setting up cloud TTS for better quality',
                'details': 'Silero works but cloud TTS provides better voice quality'
            })
        else:
            recommendations.append({
                'priority': 'info',
                'issue': 'TTS services working',
                'solution': 'No action needed',
                'details': f'Working services: {", ".join(working_services)}'
            })
        
        return recommendations
    
    def print_recommendations(self, recommendations: list):
        """Print recommendations in a formatted way"""
        print("💡 Recommendations")
        print("=" * 20)
        
        priority_colors = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': '🟢'
        }
        
        for rec in recommendations:
            color = priority_colors.get(rec['priority'], '⚪')
            print(f"\n{color} {rec['priority'].upper()}: {rec['issue']}")
            print(f"   Solution: {rec['solution']}")
            print(f"   Details: {rec['details']}")

async def main():
    """Main diagnostic function"""
    diagnostics = TTSDiagnostics()
    
    try:
        results = await diagnostics.run_full_diagnostics()
        
        print("\n" + "=" * 50)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 50)
        
        # Print recommendations
        diagnostics.print_recommendations(results['recommendations'])
        
        # Save results to file
        with open('tts_diagnostics_report.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Full report saved to: tts_diagnostics_report.json")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())