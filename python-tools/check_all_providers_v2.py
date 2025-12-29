#!/usr/bin/env python3
"""
Verity Systems - Ultimate Provider Check v2.0
Tests ALL 15+ LLM providers with beautiful output

Run: python check_all_providers_v2.py
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# All supported providers with their API key env vars
PROVIDERS = {
    # === FREE TIER PROVIDERS (No Credit Card Required!) ===
    "cerebras": {
        "name": "Cerebras",
        "env_key": "CEREBRAS_API_KEY",
        "tier": "FREE",
        "speed": "3000+ tok/sec (World's Fastest!)",
        "models": ["llama-3.3-70b", "llama-3.1-8b", "qwen-3-32b"],
        "url": "https://cloud.cerebras.ai/"
    },
    "sambanova": {
        "name": "SambaNova", 
        "env_key": "SAMBANOVA_API_KEY",
        "tier": "FREE",
        "speed": "500+ tok/sec",
        "models": ["Meta-Llama-3.1-405B-Instruct", "DeepSeek-V3", "Qwen2.5-Coder-32B-Instruct"],
        "url": "https://cloud.sambanova.ai/"
    },
    "groq": {
        "name": "Groq",
        "env_key": "GROQ_API_KEY", 
        "tier": "FREE",
        "speed": "700+ tok/sec",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
        "url": "https://console.groq.com/"
    },
    "openrouter": {
        "name": "OpenRouter",
        "env_key": "OPENROUTER_API_KEY",
        "tier": "FREE",
        "speed": "Varies by model",
        "models": ["meta-llama/llama-3.1-8b-instruct:free", "google/gemma-2-9b-it:free", "microsoft/phi-3-mini-128k-instruct:free"],
        "url": "https://openrouter.ai/"
    },
    "huggingface": {
        "name": "Hugging Face",
        "env_key": "HUGGINGFACE_API_KEY",
        "tier": "FREE",
        "speed": "~50 tok/sec",
        "models": ["meta-llama/Llama-3.2-3B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"],
        "url": "https://huggingface.co/settings/tokens"
    },
    
    # === CHEAP TIER PROVIDERS (Very Affordable) ===
    "fireworks": {
        "name": "Fireworks AI",
        "env_key": "FIREWORKS_API_KEY",
        "tier": "$1 Free Credit",
        "speed": "200+ tok/sec",
        "models": ["llama-v3p1-70b-instruct", "mixtral-8x22b-instruct", "qwen2p5-72b-instruct"],
        "url": "https://fireworks.ai/"
    },
    "novita": {
        "name": "Novita AI",
        "env_key": "NOVITA_API_KEY",
        "tier": "Cheap",
        "speed": "~100 tok/sec",
        "models": ["llama-3.3-70b-instruct", "deepseek-v3", "qwen-2.5-72b-instruct"],
        "url": "https://novita.ai/"
    },
    "together_ai": {
        "name": "Together AI",
        "env_key": "TOGETHER_API_KEY",
        "tier": "$25 Free Credit",
        "speed": "~150 tok/sec",
        "models": ["Llama-3.2-90B-Vision-Instruct-Turbo", "DeepSeek-R1-Distill-Llama-70B-free"],
        "url": "https://api.together.xyz/"
    },
    "deepseek": {
        "name": "DeepSeek",
        "env_key": "DEEPSEEK_API_KEY",
        "tier": "Cheap",
        "speed": "~100 tok/sec",
        "models": ["deepseek-chat", "deepseek-coder"],
        "url": "https://platform.deepseek.com/"
    },
    
    # === STANDARD TIER PROVIDERS ===
    "gemini": {
        "name": "Google Gemini",
        "env_key": "GOOGLE_AI_API_KEY",
        "tier": "FREE Tier Available",
        "speed": "~80 tok/sec",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
        "url": "https://makersuite.google.com/app/apikey"
    },
    "cohere": {
        "name": "Cohere",
        "env_key": "COHERE_API_KEY",
        "tier": "1000 calls/month FREE",
        "speed": "~60 tok/sec",
        "models": ["command-r", "command-r-plus", "command-light"],
        "url": "https://dashboard.cohere.ai/"
    },
    "mistral": {
        "name": "Mistral AI",
        "env_key": "MISTRAL_API_KEY",
        "tier": "FREE Tier Available",
        "speed": "~100 tok/sec",
        "models": ["mistral-small-latest", "mistral-large-latest", "codestral-latest"],
        "url": "https://console.mistral.ai/"
    },
    "perplexity": {
        "name": "Perplexity",
        "env_key": "PERPLEXITY_API_KEY",
        "tier": "Paid (Search-Grounded)",
        "speed": "~50 tok/sec",
        "models": ["llama-3.1-sonar-small-128k-online", "llama-3.1-sonar-large-128k-online"],
        "url": "https://www.perplexity.ai/settings/api"
    },
    
    # === LOCAL PROVIDERS ===
    "ollama": {
        "name": "Ollama (Local)",
        "env_key": None,  # No API key needed
        "tier": "FREE (Local)",
        "speed": "Varies by GPU",
        "models": ["llama3.1", "mistral", "gemma2", "qwen2.5"],
        "url": "https://ollama.com/"
    },
}


def check_api_key(provider_id: str, provider_info: Dict) -> Tuple[bool, str]:
    """Check if API key is configured for a provider"""
    env_key = provider_info.get("env_key")
    
    if env_key is None:
        # Local provider like Ollama
        return True, "No key needed"
    
    api_key = os.getenv(env_key, "")
    
    if not api_key or api_key.startswith("your_") or api_key.startswith("your-"):
        return False, f"Not configured"
    
    # Mask the key for display
    masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    return True, masked


async def test_provider(provider_id: str) -> Tuple[bool, str, float]:
    """Actually test a provider by making an API call"""
    try:
        # Import the unified LLM gateway
        from verity_unified_llm import UnifiedLLMGateway
        
        gateway = UnifiedLLMGateway()
        
        start = time.time()
        result = await gateway.complete(
            prompt="Say 'OK' in one word only.",
            provider=provider_id,
            max_tokens=5,
            timeout=15
        )
        elapsed = time.time() - start
        
        if result and result.get("text"):
            return True, result.get("text", "")[:20], elapsed
        return False, "Empty response", elapsed
        
    except Exception as e:
        return False, str(e)[:50], 0


def print_header():
    """Print the header"""
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██╗   ██╗███████╗██████╗ ██╗████████╗██╗   ██╗                            ║
║   ██║   ██║██╔════╝██╔══██╗██║╚══██╔══╝╚██╗ ██╔╝                            ║
║   ██║   ██║█████╗  ██████╔╝██║   ██║    ╚████╔╝                             ║
║   ╚██╗ ██╔╝██╔══╝  ██╔══██╗██║   ██║     ╚██╔╝                              ║
║    ╚████╔╝ ███████╗██║  ██║██║   ██║      ██║                               ║
║     ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝                               ║
║                                                                              ║
║                 ULTIMATE PROVIDER CHECK v2.0                                 ║
║                 15+ LLM Providers • Deep Research Mode                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}
""")


def print_provider_status(results: Dict):
    """Print provider status in a nice table"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}═══════════════════════════════════════════════════════════════════════════════{Colors.END}")
    print(f"{Colors.BOLD}                         PROVIDER STATUS REPORT{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}═══════════════════════════════════════════════════════════════════════════════{Colors.END}\n")
    
    # Group by tier
    free_providers = []
    cheap_providers = []
    standard_providers = []
    local_providers = []
    
    for pid, info in PROVIDERS.items():
        tier = info.get("tier", "")
        if "FREE" in tier.upper() and "Credit" not in tier:
            free_providers.append((pid, info, results.get(pid, {})))
        elif "Credit" in tier or tier == "Cheap":
            cheap_providers.append((pid, info, results.get(pid, {})))
        elif "Local" in tier:
            local_providers.append((pid, info, results.get(pid, {})))
        else:
            standard_providers.append((pid, info, results.get(pid, {})))
    
    def print_group(title: str, providers: List, emoji: str):
        if not providers:
            return
        print(f"\n{Colors.BOLD}{emoji} {title}{Colors.END}")
        print(f"{'─' * 75}")
        
        for pid, info, result in providers:
            has_key, key_status = result.get("key_check", (False, "Unknown"))
            working = result.get("working", False)
            
            if working:
                status = f"{Colors.GREEN}✓ WORKING{Colors.END}"
                response_time = result.get("response_time", 0)
                if response_time > 0:
                    status += f" ({response_time:.2f}s)"
            elif has_key:
                status = f"{Colors.YELLOW}○ KEY SET (untested){Colors.END}"
            else:
                status = f"{Colors.RED}✗ NO KEY{Colors.END}"
            
            name = info["name"].ljust(18)
            speed = info.get("speed", "")[:25].ljust(25)
            
            print(f"  {name} │ {speed} │ {status}")
    
    print_group("🆓 FREE TIER (No Credit Card Required!)", free_providers, "")
    print_group("💰 CHEAP TIER (Very Affordable)", cheap_providers, "")
    print_group("⭐ STANDARD TIER", standard_providers, "")
    print_group("🏠 LOCAL PROVIDERS", local_providers, "")


def print_summary(results: Dict):
    """Print summary statistics"""
    total = len(PROVIDERS)
    configured = sum(1 for r in results.values() if r.get("key_check", (False,))[0])
    working = sum(1 for r in results.values() if r.get("working", False))
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}═══════════════════════════════════════════════════════════════════════════════{Colors.END}")
    print(f"{Colors.BOLD}                              SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}═══════════════════════════════════════════════════════════════════════════════{Colors.END}\n")
    
    print(f"  Total Providers:     {total}")
    print(f"  API Keys Configured: {configured}/{total} ({configured/total*100:.0f}%)")
    print(f"  Tested & Working:    {working}/{total}")
    
    # Deep Research Mode status
    if working >= 4:
        print(f"\n  {Colors.BOLD}{Colors.GREEN}🚀 DEEP RESEARCH MODE: READY{Colors.END}")
        print(f"     You have {working} working LLM providers!")
        print(f"     Minimum required: 4 for Deep Research Mode")
    elif configured >= 4:
        print(f"\n  {Colors.BOLD}{Colors.YELLOW}⚠ DEEP RESEARCH MODE: LIKELY READY{Colors.END}")
        print(f"     You have {configured} configured providers (not all tested)")
    else:
        print(f"\n  {Colors.BOLD}{Colors.RED}✗ DEEP RESEARCH MODE: NOT READY{Colors.END}")
        print(f"     Need at least 4 LLM providers configured")
        print(f"     Currently have: {configured}")
    
    # FREE providers recommendation
    free_configured = sum(1 for pid, info in PROVIDERS.items() 
                         if "FREE" in info.get("tier", "").upper() 
                         and results.get(pid, {}).get("key_check", (False,))[0])
    
    if free_configured < 3:
        print(f"\n  {Colors.BOLD}{Colors.YELLOW}💡 TIP: Get more FREE providers!{Colors.END}")
        for pid, info in PROVIDERS.items():
            if "FREE" in info.get("tier", "").upper() and "Credit" not in info.get("tier", ""):
                if not results.get(pid, {}).get("key_check", (False,))[0]:
                    print(f"     → {info['name']}: {info['url']}")


def print_env_template():
    """Print .env template for missing keys"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}═══════════════════════════════════════════════════════════════════════════════{Colors.END}")
    print(f"{Colors.BOLD}                     QUICK SETUP - COPY TO .env{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}═══════════════════════════════════════════════════════════════════════════════{Colors.END}\n")
    
    print("# === FREE PROVIDERS (Recommended!) ===")
    for pid in ["cerebras", "sambanova", "groq", "openrouter", "huggingface"]:
        info = PROVIDERS.get(pid, {})
        env_key = info.get("env_key")
        if env_key:
            key = os.getenv(env_key, "")
            if not key or key.startswith("your"):
                print(f"# {info['name']} - {info['url']}")
                print(f"{env_key}=your_key_here")
                print()


async def main():
    """Main function"""
    print_header()
    
    print(f"\n{Colors.CYAN}Checking API keys...{Colors.END}\n")
    
    results = {}
    
    # Check all API keys
    for provider_id, provider_info in PROVIDERS.items():
        has_key, status = check_api_key(provider_id, provider_info)
        results[provider_id] = {
            "key_check": (has_key, status)
        }
    
    # Optionally test providers
    test_mode = "--test" in sys.argv or "-t" in sys.argv
    
    if test_mode:
        print(f"\n{Colors.CYAN}Testing providers (this may take a minute)...{Colors.END}\n")
        
        for provider_id, provider_info in PROVIDERS.items():
            has_key = results[provider_id]["key_check"][0]
            if has_key and provider_info.get("env_key"):  # Skip local providers without test
                print(f"  Testing {provider_info['name']}...", end=" ", flush=True)
                working, response, elapsed = await test_provider(provider_id)
                results[provider_id]["working"] = working
                results[provider_id]["response_time"] = elapsed
                results[provider_id]["response"] = response
                
                if working:
                    print(f"{Colors.GREEN}✓{Colors.END} ({elapsed:.2f}s)")
                else:
                    print(f"{Colors.RED}✗{Colors.END} {response[:30]}")
    
    print_provider_status(results)
    print_summary(results)
    
    if "--env" in sys.argv:
        print_env_template()
    
    print(f"\n{Colors.CYAN}Run with --test to test API connections{Colors.END}")
    print(f"{Colors.CYAN}Run with --env to show .env template{Colors.END}\n")


if __name__ == "__main__":
    asyncio.run(main())
