import os
import json
from groq import Groq
from typing import Dict, Any, Optional, List
from app.config import settings

class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.preferred_models: List[str] = [
            settings.GROQ_MODEL,
            "groq/compound-mini",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b"
        ]
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to initialize Groq client: {e}")

    def generate_explanation(
        self,
        question: str,
        intent: str,
        entities: dict,
        evidence: list,
        deterministic_answer: str
    ) -> Optional[str]:
        if not self.client:
            return None

        prompt = f"""You are the conversational AI Infrastructure Copilot for the ROADSense AI Platform (Government of India / MoRTH / NHAI Standard Compliant).
Your role is to explain verified road surface distress records, RDD2022 computer vision detections, Road Condition Index (RCI) scores, repair budgets, and municipal crew dispatch plans to civil engineers and inspectors.

STRICT GROUNDING DIRECTIVES:
1. Ground your answer ONLY in the verified SQL backend data and evidence provided below.
2. Never hallucinate facts, defect counts, costs, damage codes, or GPS coordinates.
3. Be professional, direct, concise, and structured (use bold text and bullet points where appropriate).
4. Clearly state verified facts first, then provide your engineering interpretation or recommended action.

Context:
User Question: "{question}"
Detected Intent: {intent}
Extracted Entities: {json.dumps(entities)}

Verified Backend Evidence & Facts:
{json.dumps(evidence, indent=2)}

Authoritative Base Answer:
{deterministic_answer}

Formulate a refined, highly professional engineering response:"""

        for model_name in self.preferred_models:
            if not model_name:
                continue
            try:
                response = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are the autonomous AI Infrastructure Copilot for ROADSense AI. Provide precise, grounded civil engineering road inspection answers."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    model=model_name,
                    temperature=0.2,
                    max_tokens=600,
                    timeout=8.0
                )
                content = response.choices[0].message.content
                if content and len(content.strip()) > 10:
                    return content.strip()
            except Exception as e:
                print(f"Groq API model '{model_name}' attempt failed: {e}")
                continue

        return None

groq_service = GroqService()
