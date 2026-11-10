"""Claude AI Service for Mercado Livre product analysis"""
import os
from typing import Optional, Dict, Any
from anthropic import Anthropic
from datetime import datetime

class ClaudeService:
    """
    Service for analyzing products and recommendations using Claude AI.
    Supports multi-turn conversations and token tracking.
    """
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model_simple = "claude-3-5-haiku-20241022"  # For simple tasks
        self.model_complex = "claude-3-5-sonnet-20241022"  # For complex analysis
    
    async def analyze_product(
        self,
        product_data: Dict[str, Any],
        tenant_id: str,
        complex: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze a Mercado Livre product for recommendations and insights.
        
        Args:
            product_data: Product information from Mercado Livre
            tenant_id: Tenant identifier for tracking
            complex: Use Sonnet (complex analysis) vs Haiku (simple)
            
        Returns:
            Analysis result with insights and recommendations
        """
        model = self.model_complex if complex else self.model_simple
        
        prompt = f"""
Analyze this Mercado Livre product and provide recommendations:

Product Data:
{product_data}

Provide:
1. Product quality assessment
2. Pricing competitiveness
3. Description optimization suggestions
4. Recommended improvements
5. Estimated performance score (1-10)

Be concise but actionable.
"""
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            
            analysis_text = response.content[0].text
            
            return {
                "success": True,
                "analysis": analysis_text,
                "model_used": model,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "tenant_id": tenant_id,
                "analyzed_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id,
            }
    
    async def ask(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        complex: bool = False,
    ) -> Dict[str, Any]:
        """
        Ask Claude a question with optional context.
        
        Args:
            question: The question to ask
            context: Optional context information
            tenant_id: Optional tenant identifier for tracking
            complex: Use Sonnet (complex) vs Haiku (simple)
            
        Returns:
            Response from Claude
        """
        model = self.model_complex if complex else self.model_simple
        
        prompt = question
        if context:
            prompt = f"Context: {context}\n\nQuestion: {question}"
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            
            return {
                "success": True,
                "response": response.content[0].text,
                "model": model,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "tenant_id": tenant_id,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id,
            }
