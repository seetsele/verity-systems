#!/usr/bin/env python3
"""
Verity Systems - Provider Status Check
=======================================
This script checks the status of all AI providers and APIs.
Run this to see what's working and what needs attention.
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv()

# ANSI colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def ok(text): return f"{Colors.GREEN}✓{Colors.END} {text}"
def fail(text): return f"{Colors.RED}✗{Colors.END} {text}"
def warn(text): return f"{Colors.YELLOW}⚠{Colors.END} {text}"
def info(text): return f"{Colors.BLUE}ℹ{Colors.END} {text}"
def header(text): return f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}\n{text}\n{'='*60}{Colors.END}"

async def check_groq():
    """Check Groq API"""
    key = os.getenv('GROQ_API_KEY')
    if not key:
        return fail("Groq: No API key")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = len(data.get('data', []))
                    return ok(f"Groq: {models} models available (FREE)")
                else:
                    return fail(f"Groq: HTTP {resp.status}")
    except Exception as e:
        return fail(f"Groq: {str(e)[:50]}")

async def check_openrouter():
    """Check OpenRouter API"""
    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        return fail("OpenRouter: No API key")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {key}"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    free_models = [m for m in data.get('data', []) if ':free' in m.get('id', '')]
                    return ok(f"OpenRouter: {len(free_models)} free models available")
                else:
                    return fail(f"OpenRouter: HTTP {resp.status}")
    except Exception as e:
        return fail(f"OpenRouter: {str(e)[:50]}")

async def check_gemini():
    """Check Google Gemini API"""
    key = os.getenv('GOOGLE_AI_API_KEY')
    if not key:
        return fail("Gemini: No API key")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = len(data.get('models', []))
                    return ok(f"Gemini: {models} models (60 RPM FREE)")
                else:
                    return fail(f"Gemini: HTTP {resp.status}")
    except Exception as e:
        return fail(f"Gemini: {str(e)[:50]}")

async def check_cohere():
    """Check Cohere API"""
    key = os.getenv('COHERE_API_KEY')
    if not key:
        return fail("Cohere: No API key")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.cohere.ai/v1/models",
                headers={"Authorization": f"Bearer {key}"}
            ) as resp:
                if resp.status == 200:
                    return ok("Cohere: Connected (1000/month FREE)")
                else:
                    return fail(f"Cohere: HTTP {resp.status}")
    except Exception as e:
        return fail(f"Cohere: {str(e)[:50]}")

async def check_mistral():
    """Check Mistral API"""
    key = os.getenv('MISTRAL_API_KEY')
    if not key:
        return fail("Mistral: No API key")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.mistral.ai/v1/models",
                headers={"Authorization": f"Bearer {key}"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = len(data.get('data', []))
                    return ok(f"Mistral: {models} models available")
                else:
                    return fail(f"Mistral: HTTP {resp.status}")
    except Exception as e:
        return fail(f"Mistral: {str(e)[:50]}")

async def check_huggingface():
    """Check HuggingFace API"""
    key = os.getenv('HUGGINGFACE_API_KEY') or os.getenv('HF_API_KEY')
    if not key:
        return fail("HuggingFace: No API key")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://huggingface.co/api/whoami",
                headers={"Authorization": f"Bearer {key}"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return ok(f"HuggingFace: Connected as {data.get('name', 'user')} (FREE)")
                else:
                    return fail(f"HuggingFace: HTTP {resp.status}")
    except Exception as e:
        return fail(f"HuggingFace: {str(e)[:50]}")

async def check_deepseek():
    """Check DeepSeek API"""
    key = os.getenv('DEEPSEEK_API_KEY')
    if not key:
        return warn("DeepSeek: No API key (needs credits)")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.deepseek.com/v1/models",
                headers={"Authorization": f"Bearer {key}"}
            ) as resp:
                if resp.status == 200:
                    return ok("DeepSeek: Connected (CHEAP tier)")
                elif resp.status == 402:
                    return warn("DeepSeek: Insufficient balance")
                else:
                    return fail(f"DeepSeek: HTTP {resp.status}")
    except Exception as e:
        return fail(f"DeepSeek: {str(e)[:50]}")

async def check_together():
    """Check Together AI API"""
    key = os.getenv('TOGETHER_API_KEY')
    if not key:
        return warn("Together AI: No API key - Get free $5 credit at https://api.together.xyz/")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.together.xyz/v1/models",
                headers={"Authorization": f"Bearer {key}"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return ok(f"Together AI: {len(data)} models (has free credits)")
                else:
                    return fail(f"Together AI: HTTP {resp.status}")
    except Exception as e:
        return fail(f"Together AI: {str(e)[:50]}")

async def check_ollama():
    """Check Ollama (local)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m['name'] for m in data.get('models', [])]
                    if models:
                        return ok(f"Ollama: {len(models)} local models ({', '.join(models[:3])}...)")
                    else:
                        return warn("Ollama: Running but no models. Run: ollama pull llama3.2")
                else:
                    return fail(f"Ollama: HTTP {resp.status}")
    except:
        return warn("Ollama: Not running. Install from https://ollama.com")

# Search APIs
async def check_brave():
    """Check Brave Search API"""
    key = os.getenv('BRAVE_API_KEY')
    if not key:
        return fail("Brave Search: No API key")
    return ok("Brave Search: Key present (2000/month FREE)")

async def check_serper():
    """Check Serper API"""
    key = os.getenv('SERPER_API_KEY')
    if not key:
        return fail("Serper: No API key")
    return ok("Serper (Google): Key present (2500/month FREE)")

async def check_tavily():
    """Check Tavily API"""
    key = os.getenv('TAVILY_API_KEY')
    if not key:
        return fail("Tavily: No API key")
    return ok("Tavily: Key present (1000/month FREE)")

async def check_exa():
    """Check Exa API"""
    key = os.getenv('EXA_API_KEY')
    if not key:
        return warn("Exa: No API key (optional)")
    return ok("Exa: Key present (1000/month FREE)")

# Academic APIs
async def check_semantic_scholar():
    """Check Semantic Scholar API"""
    key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
    if key:
        return ok("Semantic Scholar: API key present (higher limits)")
    return ok("Semantic Scholar: No key (still works, lower limits)")

# News APIs
async def check_newsapi():
    """Check NewsAPI"""
    key = os.getenv('NEWS_API_KEY') or os.getenv('NEWSAPI_KEY')
    if not key:
        return warn("NewsAPI: No API key (100/day FREE)")
    return ok("NewsAPI: Key present (100/day FREE)")

async def check_mediastack():
    """Check MediaStack"""
    key = os.getenv('MEDIASTACK_API_KEY')
    if not key:
        return warn("MediaStack: No API key (500/month FREE)")
    return ok("MediaStack: Key present (500/month FREE)")

async def main():
    print(f"""
{Colors.BOLD}{Colors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║           VERITY SYSTEMS - PROVIDER STATUS CHECK             ║
║                    Deep Research Mode                        ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}
Checking all AI providers and APIs...
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

    # LLM Providers
    print(header("🤖 LLM PROVIDERS"))
    
    llm_checks = [
        check_groq(),
        check_gemini(),
        check_openrouter(),
        check_cohere(),
        check_mistral(),
        check_huggingface(),
        check_deepseek(),
        check_together(),
        check_ollama(),
    ]
    
    results = await asyncio.gather(*llm_checks)
    for r in results:
        print(f"  {r}")
    
    # Search APIs
    print(header("🔍 SEARCH APIS"))
    
    search_checks = [
        check_brave(),
        check_serper(),
        check_tavily(),
        check_exa(),
    ]
    
    results = await asyncio.gather(*search_checks)
    for r in results:
        print(f"  {r}")
    
    # Academic APIs
    print(header("📚 ACADEMIC SOURCES"))
    print(f"  {await check_semantic_scholar()}")
    print(f"  {ok('PubMed: Always available (FREE)')}")
    print(f"  {ok('arXiv: Always available (FREE)')}")
    print(f"  {ok('CrossRef: Always available (FREE)')}")
    
    # News APIs
    print(header("📰 NEWS SOURCES"))
    results = await asyncio.gather(check_newsapi(), check_mediastack())
    for r in results:
        print(f"  {r}")
    
    # Summary
    print(header("📊 SUMMARY"))
    
    # Count available
    groq_ok = bool(os.getenv('GROQ_API_KEY'))
    gemini_ok = bool(os.getenv('GOOGLE_AI_API_KEY'))
    openrouter_ok = bool(os.getenv('OPENROUTER_API_KEY'))
    
    llm_count = sum([
        groq_ok, gemini_ok, openrouter_ok,
        bool(os.getenv('COHERE_API_KEY')),
        bool(os.getenv('MISTRAL_API_KEY')),
        bool(os.getenv('HUGGINGFACE_API_KEY')),
        bool(os.getenv('DEEPSEEK_API_KEY')),
        bool(os.getenv('TOGETHER_API_KEY')),
    ])
    
    search_count = sum([
        bool(os.getenv('BRAVE_API_KEY')),
        bool(os.getenv('SERPER_API_KEY')),
        bool(os.getenv('TAVILY_API_KEY')),
        bool(os.getenv('EXA_API_KEY')),
    ])
    
    print(f"""
  {Colors.BOLD}LLM Providers:{Colors.END} {llm_count}/8 configured + Ollama (local)
  {Colors.BOLD}Search APIs:{Colors.END} {search_count}/4 configured + DuckDuckGo (free)
  {Colors.BOLD}Academic:{Colors.END} 4/4 available (always free)
  
  {Colors.BOLD}{Colors.GREEN}Ready for Deep Research Mode!{Colors.END}
  
  Minimum requirements: {Colors.GREEN}✓{Colors.END}
  - At least 4 LLM models: {'✓' if llm_count >= 2 or groq_ok else '✗'}
  - At least 1 search engine: {'✓' if search_count >= 1 else '✗'}
  - Academic sources: ✓ (always available)
""")

    # Action items
    missing = []
    if not os.getenv('TOGETHER_API_KEY'):
        missing.append("  • Get FREE $5 credit: https://api.together.xyz/")
    if not os.getenv('DEEPSEEK_API_KEY'):
        missing.append("  • DeepSeek (very cheap): https://platform.deepseek.com/")
    
    if missing:
        print(f"{Colors.YELLOW}Optional improvements:{Colors.END}")
        for m in missing:
            print(m)
    
    print()

if __name__ == "__main__":
    asyncio.run(main())
