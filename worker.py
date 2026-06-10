import pika
import json
import logging
import os
import time
from scraper import YouTubeScraper

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

REQUESTS_QUEUE = "youtube.scrape.requests"
RESULTS_QUEUE = "youtube.scrape.results"

def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    
    last_error = None
    # Retry logic if RabbitMQ isn't ready
    for i in range(10):
        try:
            logger.info(f"Tentando conectar ao RabbitMQ em {RABBITMQ_HOST}:{RABBITMQ_PORT} (tentativa {i+1}/10)...")
            connection = pika.BlockingConnection(parameters)
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            last_error = e
            logger.warning(f"Erro de conexão com RabbitMQ: {e!r}. Aguardando 5 segundos...")
            time.sleep(5)
    raise RuntimeError("Não foi possível conectar ao RabbitMQ.") from last_error

def process_message(ch, method, properties, body):
    logger.info(f"Mensagem de request recebida: {body.decode('utf-8')}")
    
    try:
        data = json.loads(body.decode('utf-8'))
        channel_id = data.get("channelId")
        source_channel_url = data.get("sourceChannelUrl")
        source_channel_name = data.get("sourceChannelName")
        
        if not source_channel_url:
            logger.error("URL do canal de origem ausente na mensagem.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        logger.info(f"Iniciando raspagem para URL: {source_channel_url}")
        
        scraper = YouTubeScraper()
        success = False
        videos = []
        error_msg = None
        
        try:
            success = scraper.navigate_to_popular(source_channel_url)
            if success:
                scraper.extract_videos(source_channel_url)
                videos = scraper.data
                logger.info(f"Raspagem concluída com sucesso. {len(videos)} vídeos extraídos.")
            else:
                error_msg = "Falha ao navegar até a página de vídeos populares do canal."
                logger.error(error_msg)
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Erro interno no scraper ao processar {source_channel_url!r}")
        finally:
            scraper.close()
            
        # Publica o resultado
        response_payload = {
            "channelId": channel_id,
            "sourceChannelUrl": source_channel_url,
            "sourceChannelName": source_channel_name,
            "status": "success" if (success and not error_msg) else "failed",
            "videos": videos,
            "error": error_msg
        }
        
        ch.basic_publish(
            exchange='',
            routing_key=RESULTS_QUEUE,
            body=json.dumps(response_payload),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2  # persistent
            )
        )
        logger.info(f"Resultado publicado na fila {RESULTS_QUEUE} com status: {response_payload['status']}")
        
    except Exception:
        logger.exception("Erro grave no processamento da mensagem")
        
    # Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    from scraper import setup_logging
    setup_logging()

    logger.info("Iniciando Worker Python do YouTube Scraper...")
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    
    # Declarar filas para garantir que existem
    channel.queue_declare(queue=REQUESTS_QUEUE, durable=True)
    channel.queue_declare(queue=RESULTS_QUEUE, durable=True)
    
    # Configurar prefetch limit (consome 1 mensagem por vez)
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(queue=REQUESTS_QUEUE, on_message_callback=process_message)
    
    logger.info(f"Escutando a fila {REQUESTS_QUEUE}...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Worker parado pelo usuário.")
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
