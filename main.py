import sys
import logging
from tqdm import tqdm
import config
from scraper import YouTubeScraper

# Configura o logger do arquivo principal
logger = logging.getLogger(__name__)

def main():
    from scraper import setup_logging
    setup_logging()

    logger.info("==========================================")
    logger.info(" Iniciando Coleta de Vídeos do YouTube")
    logger.info("==========================================")
    
    if not config.CHANNELS:
        logger.error("A lista de canais em config.py está vazia. Abortando.")
        sys.exit(1)

    scraper = None
    try:
        scraper = YouTubeScraper()
        
        # tqdm para a barra de progresso visual no terminal
        logger.info(f"Serão processados {len(config.CHANNELS)} canais.")
        
        for url in tqdm(config.CHANNELS, desc="Processando Canais", unit="canal"):
            logger.info(f"--- Processando: {url!r} ---")
            
            # Navega até o canal e acessa a aba Em Alta
            success = scraper.navigate_to_popular(url)
            
            if success:
                # Extrai os dados se a navegação foi bem sucedida
                scraper.extract_videos(url)
            else:
                logger.error(f"Pulando extração para {url!r} devido a falha na navegação.")
                
    except Exception:
        logger.exception("Erro fatal durante a execução principal")
    
    finally:
        if scraper:
            scraper.export_data()
            scraper.close()
            
    logger.info("==========================================")
    logger.info(" Processo Finalizado")
    logger.info("==========================================")

if __name__ == "__main__":
    main()
