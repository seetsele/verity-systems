"""
Verity Systems - Azure AI Foundry Integration
==============================================

Client for Microsoft Azure AI Foundry platform.
Provides access to enterprise-grade AI models including:
- GPT-4o, GPT-4 Turbo
- Azure OpenAI models
- AI agents and assistants

Docs: https://learn.microsoft.com/azure/ai-studio/
"""

import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger('VerityAzureFoundry')

# Azure AI Foundry configuration
AZURE_AI_FOUNDRY_ENDPOINT = os.getenv('AZURE_AI_FOUNDRY_ENDPOINT', 'https://verity-systems.services.ai.azure.com/api/projects/proj-veritysys')
AZURE_AI_FOUNDRY_API_KEY = os.getenv('AZURE_AI_FOUNDRY_API_KEY', '')

# Try to import Azure SDK (optional - falls back to REST API)
try:
    from azure.identity import DefaultAzureCredential, AzureKeyCredential
    from azure.ai.projects import AIProjectClient
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    logger.warning("Azure SDK not available. Using REST API fallback.")


class AzureFoundryClient:
    """
    Client for Azure AI Foundry - Microsoft's enterprise AI platform.
    
    Supports:
    - Azure OpenAI models (GPT-4o, GPT-4 Turbo, etc.)
    - AI agents and assistants
    - Enterprise-grade security and compliance
    
    Usage:
        client = AzureFoundryClient()
        result = await client.verify_claim("The Earth is round")
    """
    
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint = endpoint or AZURE_AI_FOUNDRY_ENDPOINT
        self.api_key = api_key or AZURE_AI_FOUNDRY_API_KEY
        self.project_client = None
        
        # Initialize Azure SDK client if available
        if AZURE_SDK_AVAILABLE and self.api_key:
            try:
                # Use API key credential for simpler auth
                from azure.core.credentials import AzureKeyCredential
                self.project_client = AIProjectClient(
                    endpoint=self.endpoint,
                    credential=AzureKeyCredential(self.api_key)
                )
                logger.info("✅ Azure AI Foundry client initialized with SDK")
            except Exception as e:
                logger.warning(f"SDK init failed, using REST API: {e}")
                self.project_client = None
        
        if not self.api_key:
            logger.warning("Azure AI Foundry API key not configured")
            logger.info("Set AZURE_AI_FOUNDRY_API_KEY environment variable")
    
    @property
    def is_available(self) -> bool:
        """Check if Azure AI Foundry is configured"""
        return bool(self.api_key)
    
    @property
    def name(self) -> str:
        return "Azure AI Foundry"
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to Azure AI Foundry.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (gpt-4o, gpt-4-turbo, etc.)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with response content and metadata
        """
        if not self.is_available:
            return {'error': 'Azure AI Foundry not configured', 'content': None}
        
        # Use REST API for chat completion
        import httpx
        
        try:
            headers = {
                'api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messages': messages,
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            # Azure OpenAI endpoint format
            chat_endpoint = f"{self.endpoint}/openai/deployments/{model}/chat/completions?api-version=2024-02-15-preview"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    chat_endpoint,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'content': data.get('choices', [{}])[0].get('message', {}).get('content', ''),
                        'model': model,
                        'usage': data.get('usage', {}),
                        'source': 'Azure AI Foundry'
                    }
                else:
                    logger.error(f"Azure AI Foundry error ({response.status_code}): {response.text}")
                    return {'error': f'HTTP {response.status_code}', 'content': None}
                    
        except httpx.TimeoutException:
            logger.error("Azure AI Foundry request timed out")
            return {'error': 'Request timeout', 'content': None}
        except Exception as e:
            logger.error(f"Azure AI Foundry error: {e}")
            return {'error': str(e), 'content': None}
    
    async def verify_claim(self, claim: str, context: str = "") -> Dict[str, Any]:
        """
        Verify a claim using Azure AI Foundry models.
        
        Args:
            claim: The claim to verify
            context: Optional additional context
            
        Returns:
            Dict with verification result
        """
        system_prompt = """You are an expert fact-checker. Analyze claims for accuracy.
        
For each claim, provide:
1. VERDICT: TRUE, FALSE, PARTIALLY_TRUE, UNVERIFIABLE, or MISLEADING
2. CONFIDENCE: 0.0 to 1.0
3. EXPLANATION: Brief reasoning for your verdict
4. KEY_FACTS: List of relevant facts

Respond in JSON format:
{
    "verdict": "...",
    "confidence": 0.0,
    "explanation": "...",
    "key_facts": ["...", "..."]
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Verify this claim: {claim}\n\n{f'Context: {context}' if context else ''}"}
        ]
        
        result = await self.chat_completion(messages, temperature=0.2)
        
        if result.get('content'):
            try:
                import json
                # Try to parse JSON response
                content = result['content']
                # Handle markdown code blocks
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                
                parsed = json.loads(content.strip())
                return {
                    'source': 'Azure AI Foundry',
                    'model': result.get('model', 'gpt-4o'),
                    'verdict': parsed.get('verdict', 'UNVERIFIABLE'),
                    'confidence': parsed.get('confidence', 0.5),
                    'explanation': parsed.get('explanation', ''),
                    'key_facts': parsed.get('key_facts', []),
                    'raw_response': result['content']
                }
            except json.JSONDecodeError:
                # Return raw response if not valid JSON
                return {
                    'source': 'Azure AI Foundry',
                    'model': result.get('model', 'gpt-4o'),
                    'verdict': 'UNVERIFIABLE',
                    'confidence': 0.5,
                    'explanation': result['content'],
                    'key_facts': [],
                    'raw_response': result['content']
                }
        
        return {
            'source': 'Azure AI Foundry',
            'error': result.get('error', 'Unknown error'),
            'verdict': 'UNVERIFIABLE',
            'confidence': 0.0
        }


# Convenience function for quick verification
async def verify_with_azure(claim: str) -> Dict[str, Any]:
    """Quick verification using Azure AI Foundry"""
    client = AzureFoundryClient()
    return await client.verify_claim(claim)


# Test function
async def test_azure_foundry():
    """Test Azure AI Foundry connection"""
    print("\n" + "="*60)
    print("🔵 AZURE AI FOUNDRY TEST")
    print("="*60)
    
    client = AzureFoundryClient()
    
    if not client.is_available:
        print("❌ Azure AI Foundry not configured")
        print("   Set AZURE_AI_FOUNDRY_ENDPOINT and AZURE_AI_FOUNDRY_API_KEY")
        return False
    
    print(f"✅ Endpoint: {client.endpoint[:50]}...")
    print(f"✅ API Key: {client.api_key[:10]}...")
    
    # Test verification
    print("\n📋 Testing claim verification...")
    result = await client.verify_claim("The Earth orbits the Sun")
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ Verdict: {result.get('verdict')}")
    print(f"✅ Confidence: {result.get('confidence')}")
    print(f"✅ Explanation: {result.get('explanation', '')[:100]}...")
    
    print("\n" + "="*60)
    print("✅ Azure AI Foundry integration working!")
    print("="*60)
    return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_azure_foundry())
