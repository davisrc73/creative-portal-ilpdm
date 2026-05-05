import httpx
import base64
from pathlib import Path
from typing import Dict, List
from PIL import Image
import io

from app.config import settings
from app.models import Asset, AssetType

class AITagger:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.VISION_MODEL
    
    async def analyze_asset(self, asset: Asset) -> Dict[str, any]:
        if asset.asset_type == AssetType.VIDEO:
            return await self._analyze_video_thumbnail(asset)
        elif asset.asset_type == AssetType.IMAGE:
            return await self._analyze_image(asset)
        else:
            raise ValueError(f"Unsupported asset type: {asset.asset_type}")
    
    async def _analyze_image(self, asset: Asset) -> Dict[str, any]:
        # Se o caminho vier do banco como /Users/..., temos de convertê-lo para /nas_assets/
        original_path = asset.file_path
        if "TESTES" in original_path:
             # Pega apenas no nome do ficheiro após a pasta TESTES
             filename = original_path.split("TESTES/")[-1]
             file_path = Path("/nas_assets") / filename
        else:
             file_path = Path(original_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found in Docker: {file_path}")
        
        image_base64 = self._encode_image_to_base64(file_path)
        
        prompt = self._build_analysis_prompt()
        
        response = await self._call_vision_api(image_base64, prompt)
        
        return self._parse_ai_response(response)
    
    async def _analyze_video_thumbnail(self, asset: Asset) -> Dict[str, any]:
        if not asset.thumbnail_path:
            return {
                "tags": [],
                "description": "No thumbnail available for analysis",
                "cultural_context": None,
                "social_copy": None,
                "emotional_sentiment": None
            }
        
        thumbnail_path = Path(asset.thumbnail_path)
        if not thumbnail_path.exists():
            raise FileNotFoundError(f"Thumbnail not found: {thumbnail_path}")
        
        image_base64 = self._encode_image_to_base64(thumbnail_path)
        prompt = self._build_analysis_prompt()
        response = await self._call_vision_api(image_base64, prompt)
        
        return self._parse_ai_response(response)
    
    def _encode_image_to_base64(self, image_path: Path) -> str:
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            max_size = (1024, 1024)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            return base64.b64encode(buffer.read()).decode('utf-8')
    
    def _build_analysis_prompt(self) -> str:
        return """Analisa esta imagem para o sistema de gestão de assets do projeto @ilovepauldomar (Ilha da Madeira).
O teu objetivo é ajudar a organizar conteúdos para a diáspora paulense, focando na nostalgia e beleza da terra,
o que ajudara a criar uma ponte emocional com a diáspora paulense através de conteúdos nostálgicos e autênticos.

Responde OBRIGATORIAMENTE em Português de Portugal para os campos de texto.

Para o campo 'social_copy', escreve OBRIGATORIAMENTE uma sugestão de copy para as redes sociais (Instagram/Facebook).
Mesmo que a foto seja simples, cria uma mensagem curta e nostálgica sobre o Paul do Mar. 
NUNCA deixes este campo vazio ou apenas com aspas.
O copy deve ser empática, evocando saudades do mar, do cais, do calhau ou das tradições do Paul, 
usando expressões locais quando apropriado. Inclui 3-5 hashtags relevantes.

Identifica elementos como: o cais, o calhau, barcos de pesca, poios, a igreja, ou o pôr-do-sol, praia, estatuas, .

Formata a resposta em JSON com estas chaves:
{
  "description": "Uma descrição breve e poética do que vês",
  "cultural_context": "O contexto cultural relacionado com a faina ou tradições do Paul do Mar",
  "social_copy": "Sugestão de Copy para as Redes Sociais",
  "emotional_sentiment": "Escolhe um: nostalgia, resiliência, calma, alegria, melancolia",
  "tags": ["tag1", "tag2", "tag3", ...],
  "seasonality": "época do ano (primavera, verão, outono, inverno ou todas)",
  "target_audience": "público-alvo (diáspora, comunidade_local, geral, jovens, idosos)"
}"""
    
    async def _call_vision_api(self, image_base64: str, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
    
    def _parse_ai_response(self, response: str) -> Dict[str, any]:
        import json
        
        try:
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            data = json.loads(response_clean.strip())
            
            return {
                "tags": data.get("tags", []),
                "description": data.get("description", ""),
                "cultural_context": data.get("cultural_context"),
                "social_copy": data.get("social_copy"),
                "emotional_sentiment": data.get("emotional_sentiment"),
                "seasonality": data.get("seasonality"),
                "target_audience": data.get("target_audience")
            }
        except json.JSONDecodeError:
            return {
                "tags": [],
                "description": response,
                "cultural_context": None,
                "social_copy": None,
                "emotional_sentiment": None,
                "seasonality": None,
                "target_audience": None
            }
