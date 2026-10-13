from aiokafka import AIOKafkaProducer
import json
import logging
from app.core.config import settings

KAFKA_BOOTSTRAP_SERVERS = settings.KAFKA_SERVER
TOPIC = settings.KAFKA_EMAIL_TOPIC
GROUP_ID = "email-service"

producer: AIOKafkaProducer = None
logger = logging.getLogger(__name__)

async def start_producer():
    global producer
    if not settings.FEATURE_KAFKA:
        return
    if not KAFKA_BOOTSTRAP_SERVERS:
        raise RuntimeError("KAFKA_SERVER is required when FEATURE_KAFKA=true")
    logger.info(f"Starting Kafka producer bootstrap_servers={KAFKA_BOOTSTRAP_SERVERS}")
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    await producer.start()
    logger.info("Kafka producer started")


async def stop_producer():
    if producer:
        await producer.stop()
        logger.info("Kafka producer stopped")

async def send_message(topic: str, data: dict):
    if not settings.FEATURE_EMAIL:
        return
    if not settings.FEATURE_KAFKA:
        from app.kafka.handler import handle_event_event

        await handle_event_event(data)
        return
    if producer is None:
        raise RuntimeError("Kafka producer is not started")
    try:
        message_type = data.get("type")
        logger.info(f"Sending message to topic={topic} type={message_type}")
        await producer.send_and_wait(topic, data)
        logger.info(f"Message sent to topic={topic} type={message_type}")
    except Exception:
        logger.exception(f"Failed to send message to topic={topic}")
        raise

