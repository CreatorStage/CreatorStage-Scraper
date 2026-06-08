from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import logging
from scraper import YouTubeScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Scraper API")

class ScrapeRequest(BaseModel):
    urls: List[str]

@app.post("/scrape")
def scrape_channels(request: ScrapeRequest):
    if not request.urls:
        raise HTTPException(status_code=400, detail="Nenhuma URL fornecida")
        
    scraper = None
    try:
        logger.info(f"Recebida requisição para raspar: {request.urls}")
        scraper = YouTubeScraper()
        for url in request.urls:
            success = scraper.navigate_to_popular(url)
            if success:
                scraper.extract_videos(url)
        
        results = scraper.data
        return {"status": "success", "data": results}
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if scraper:
            scraper.close()
