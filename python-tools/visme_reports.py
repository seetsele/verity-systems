"""
Verity Systems - Visme Integration
Visual content generation for fact-check reports and infographics

GitHub Education: Visme Pro credits available
Use for: Creating shareable visual fact-check reports
"""

import os
import json
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('VerityVisme')

# Configuration
VISME_API_KEY = os.getenv('VISME_API_KEY')
VISME_API_URL = 'https://api.visme.co/v1'


class VerdictStyle(Enum):
    """Visual styles for different verdicts"""
    TRUE = {'color': '#22c55e', 'icon': 'check-circle', 'bg': '#dcfce7'}
    FALSE = {'color': '#ef4444', 'icon': 'x-circle', 'bg': '#fee2e2'}
    PARTIALLY_TRUE = {'color': '#f59e0b', 'icon': 'alert-triangle', 'bg': '#fef3c7'}
    MISLEADING = {'color': '#f97316', 'icon': 'alert-circle', 'bg': '#ffedd5'}
    UNVERIFIABLE = {'color': '#6b7280', 'icon': 'help-circle', 'bg': '#f3f4f6'}


@dataclass
class InfographicTemplate:
    """Pre-defined infographic templates"""
    FACT_CHECK_CARD = 'fact-check-card'
    DETAILED_REPORT = 'detailed-report'
    SOCIAL_SHARE = 'social-share'
    WEEKLY_SUMMARY = 'weekly-summary'
    SOURCE_BREAKDOWN = 'source-breakdown'


class VismeReportGenerator:
    """Generate visual fact-check reports using Visme API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or VISME_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        } if self.api_key else {}
        
        if not self.api_key:
            logger.warning("Visme API key not configured - visual reports disabled")
    
    def _get_verdict_style(self, verdict: str) -> Dict[str, str]:
        """Get visual style for verdict"""
        try:
            return VerdictStyle[verdict.upper()].value
        except KeyError:
            return VerdictStyle.UNVERIFIABLE.value
    
    async def create_fact_check_card(self, result: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Create a shareable fact-check card infographic
        
        Returns:
            Dict with 'image_url', 'share_url', 'embed_code'
        """
        if not self.api_key:
            return self._generate_fallback_card(result)
        
        verdict = result.get('verdict', 'UNVERIFIABLE')
        style = self._get_verdict_style(verdict)
        
        template_data = {
            'template_id': InfographicTemplate.FACT_CHECK_CARD,
            'format': 'png',
            'variables': {
                # Claim information
                'claim_text': self._truncate_text(result.get('claim', ''), 200),
                'claim_source': result.get('source', 'User submitted'),
                
                # Verdict display
                'verdict': verdict,
                'verdict_color': style['color'],
                'verdict_bg': style['bg'],
                'verdict_icon': style['icon'],
                
                # Confidence
                'confidence': f"{result.get('confidence', 0):.0f}%",
                'confidence_bar_width': f"{result.get('confidence', 0)}%",
                
                # Sources
                'sources_count': len(result.get('sources', [])),
                'top_sources': self._format_sources(result.get('sources', [])[:3]),
                'ai_models_used': len(result.get('providers', [])),
                
                # Metadata
                'verification_date': datetime.utcnow().strftime('%B %d, %Y'),
                'verification_id': result.get('id', 'N/A')[:8],
                
                # Branding
                'brand_name': 'Verity Systems',
                'brand_url': 'verity-systems.com'
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{VISME_API_URL}/projects/generate',
                    headers=self.headers,
                    json=template_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'image_url': data.get('image_url'),
                            'share_url': data.get('share_url'),
                            'embed_code': self._generate_embed_code(data.get('share_url')),
                            'project_id': data.get('project_id')
                        }
                    else:
                        logger.error(f"Visme API error: {response.status}")
                        return self._generate_fallback_card(result)
        except Exception as e:
            logger.error(f"Failed to create fact-check card: {e}")
            return self._generate_fallback_card(result)
    
    async def create_detailed_report(self, result: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Create a detailed multi-page report"""
        if not self.api_key:
            return None
        
        verdict = result.get('verdict', 'UNVERIFIABLE')
        style = self._get_verdict_style(verdict)
        
        # Build source analysis data
        source_data = []
        for source in result.get('sources', []):
            source_data.append({
                'name': source.get('name', 'Unknown'),
                'verdict': source.get('verdict', 'N/A'),
                'confidence': source.get('confidence', 0),
                'url': source.get('url', '')
            })
        
        template_data = {
            'template_id': InfographicTemplate.DETAILED_REPORT,
            'format': 'pdf',
            'variables': {
                # Header
                'report_title': 'Fact-Check Verification Report',
                'claim_text': result.get('claim', ''),
                'verdict': verdict,
                'verdict_color': style['color'],
                'confidence': result.get('confidence', 0),
                
                # Analysis breakdown
                'reasoning': result.get('reasoning', 'No detailed reasoning available.'),
                'key_findings': result.get('key_findings', []),
                
                # Source analysis
                'sources': source_data,
                'source_agreement': self._calculate_source_agreement(result.get('sources', [])),
                
                # AI analysis
                'ai_providers': result.get('providers', []),
                'consensus_score': result.get('consensus_score', 0),
                
                # Metadata
                'generated_at': datetime.utcnow().isoformat(),
                'report_id': result.get('id', '')
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{VISME_API_URL}/projects/generate',
                    headers=self.headers,
                    json=template_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'pdf_url': data.get('pdf_url'),
                            'share_url': data.get('share_url'),
                            'project_id': data.get('project_id')
                        }
        except Exception as e:
            logger.error(f"Failed to create detailed report: {e}")
        
        return None
    
    async def create_social_share_image(
        self, 
        result: Dict[str, Any],
        platform: str = 'twitter'
    ) -> Optional[str]:
        """
        Create optimized image for social media sharing
        
        Platforms: twitter, facebook, linkedin, instagram
        """
        if not self.api_key:
            return None
        
        # Platform-specific dimensions
        dimensions = {
            'twitter': {'width': 1200, 'height': 675},
            'facebook': {'width': 1200, 'height': 630},
            'linkedin': {'width': 1200, 'height': 627},
            'instagram': {'width': 1080, 'height': 1080}
        }
        
        dim = dimensions.get(platform, dimensions['twitter'])
        verdict = result.get('verdict', 'UNVERIFIABLE')
        style = self._get_verdict_style(verdict)
        
        template_data = {
            'template_id': f'social-{platform}',
            'format': 'png',
            'dimensions': dim,
            'variables': {
                'claim_preview': self._truncate_text(result.get('claim', ''), 100),
                'verdict': verdict,
                'verdict_emoji': self._get_verdict_emoji(verdict),
                'verdict_color': style['color'],
                'confidence': f"{result.get('confidence', 0):.0f}%",
                'brand_logo': 'verity-logo.png',
                'cta_text': 'Verify claims at verity-systems.com'
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{VISME_API_URL}/projects/generate',
                    headers=self.headers,
                    json=template_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('image_url')
        except Exception as e:
            logger.error(f"Failed to create social share image: {e}")
        
        return None
    
    async def create_weekly_summary(self, stats: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Create weekly statistics infographic"""
        if not self.api_key:
            return None
        
        template_data = {
            'template_id': InfographicTemplate.WEEKLY_SUMMARY,
            'format': 'png',
            'variables': {
                # Overview stats
                'total_claims': stats.get('total_claims', 0),
                'unique_users': stats.get('unique_users', 0),
                'avg_confidence': f"{stats.get('avg_confidence', 0):.1f}%",
                
                # Verdict breakdown
                'true_count': stats.get('verdicts', {}).get('TRUE', 0),
                'false_count': stats.get('verdicts', {}).get('FALSE', 0),
                'partial_count': stats.get('verdicts', {}).get('PARTIALLY_TRUE', 0),
                'misleading_count': stats.get('verdicts', {}).get('MISLEADING', 0),
                
                # Percentages for pie chart
                'true_pct': stats.get('percentages', {}).get('TRUE', 0),
                'false_pct': stats.get('percentages', {}).get('FALSE', 0),
                'partial_pct': stats.get('percentages', {}).get('PARTIALLY_TRUE', 0),
                
                # Top topics
                'top_topics': stats.get('top_topics', []),
                
                # Trends
                'trend_direction': stats.get('trend', 'stable'),
                'week_over_week_change': stats.get('wow_change', 0),
                
                # Date range
                'start_date': stats.get('start_date', ''),
                'end_date': stats.get('end_date', '')
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{VISME_API_URL}/projects/generate',
                    headers=self.headers,
                    json=template_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'image_url': data.get('image_url'),
                            'share_url': data.get('share_url')
                        }
        except Exception as e:
            logger.error(f"Failed to create weekly summary: {e}")
        
        return None
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'
    
    def _format_sources(self, sources: List[Dict]) -> str:
        """Format source list for display"""
        names = [s.get('name', 'Unknown') for s in sources]
        return ', '.join(names) if names else 'No sources'
    
    def _calculate_source_agreement(self, sources: List[Dict]) -> float:
        """Calculate percentage of sources that agree"""
        if not sources:
            return 0
        
        verdicts = [s.get('verdict') for s in sources if s.get('verdict')]
        if not verdicts:
            return 0
        
        from collections import Counter
        most_common = Counter(verdicts).most_common(1)
        if most_common:
            return (most_common[0][1] / len(verdicts)) * 100
        return 0
    
    def _get_verdict_emoji(self, verdict: str) -> str:
        """Get emoji for verdict"""
        emojis = {
            'TRUE': '✅',
            'FALSE': '❌',
            'PARTIALLY_TRUE': '⚠️',
            'MISLEADING': '🟠',
            'UNVERIFIABLE': '❓'
        }
        return emojis.get(verdict.upper(), '❓')
    
    def _generate_embed_code(self, share_url: str) -> str:
        """Generate HTML embed code"""
        if not share_url:
            return ''
        return f'<iframe src="{share_url}" width="600" height="400" frameborder="0"></iframe>'
    
    def _generate_fallback_card(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Generate fallback when Visme API not available"""
        verdict = result.get('verdict', 'UNVERIFIABLE')
        style = self._get_verdict_style(verdict)
        
        # Return data that can be used to render client-side
        return {
            'type': 'fallback',
            'data': {
                'claim': result.get('claim', ''),
                'verdict': verdict,
                'confidence': result.get('confidence', 0),
                'style': style,
                'sources_count': len(result.get('sources', [])),
                'date': datetime.utcnow().isoformat()
            },
            'html': self._generate_fallback_html(result, style)
        }
    
    def _generate_fallback_html(self, result: Dict[str, Any], style: Dict) -> str:
        """Generate fallback HTML card"""
        verdict = result.get('verdict', 'UNVERIFIABLE')
        confidence = result.get('confidence', 0)
        claim = self._truncate_text(result.get('claim', ''), 150)
        
        return f'''
        <div style="font-family: system-ui; max-width: 500px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <div style="background: {style['bg']}; padding: 20px; text-align: center;">
                <div style="font-size: 48px;">{self._get_verdict_emoji(verdict)}</div>
                <div style="font-size: 24px; font-weight: bold; color: {style['color']};">{verdict}</div>
                <div style="font-size: 14px; color: #666;">Confidence: {confidence:.0f}%</div>
            </div>
            <div style="padding: 20px; background: white;">
                <p style="font-size: 16px; color: #333; margin: 0;">"{claim}"</p>
            </div>
            <div style="padding: 12px 20px; background: #f9fafb; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 12px; color: #666;">Verified by Verity Systems</span>
                <span style="font-size: 12px; color: {style['color']};">verity-systems.com</span>
            </div>
        </div>
        '''


# ============================================================
# API ENDPOINT INTEGRATION
# ============================================================

# FastAPI endpoint for generating reports
async def generate_shareable_report(result: Dict[str, Any], format: str = 'card'):
    """Generate shareable report from verification result"""
    generator = VismeReportGenerator()
    
    if format == 'card':
        return await generator.create_fact_check_card(result)
    elif format == 'detailed':
        return await generator.create_detailed_report(result)
    elif format == 'social':
        return await generator.create_social_share_image(result)
    else:
        return await generator.create_fact_check_card(result)


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_visme():
        generator = VismeReportGenerator()
        
        # Test with sample result
        sample_result = {
            'id': 'test-123',
            'claim': 'The Earth is approximately 4.5 billion years old, based on radiometric dating.',
            'verdict': 'TRUE',
            'confidence': 95,
            'sources': [
                {'name': 'Wikipedia', 'verdict': 'TRUE', 'confidence': 90},
                {'name': 'NASA', 'verdict': 'TRUE', 'confidence': 98},
                {'name': 'Scientific American', 'verdict': 'TRUE', 'confidence': 95}
            ],
            'providers': ['anthropic', 'groq', 'wikipedia'],
            'reasoning': 'Multiple scientific sources confirm Earth\'s age through radiometric dating.'
        }
        
        # Generate fact-check card
        card = await generator.create_fact_check_card(sample_result)
        print(f"Fact-Check Card: {card}")
        
        print("\n✅ Visme integration tested!")
    
    asyncio.run(test_visme())
