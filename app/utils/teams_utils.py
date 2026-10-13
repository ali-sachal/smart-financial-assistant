import requests
import logging
from app.core.config import settings
class TeamsWebhookService:
    def __init__(self, webhook_url: str = settings.TEAMS_WEBHOOK_URL):
        self.webhook_url = webhook_url
 
    def send(self, title: str, facts: dict, footer="Sent by Billing Worker"):
 
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "msteams": {"width": "full"},
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": title,
                                "weight": "Bolder",
                                "size": "Large",
                                "wrap": True
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": k, "value": str(v)}
                                    for k, v in facts.items()
                                ]
                            },
                            {
                                "type": "TextBlock",
                                "text": footer,
                                "wrap": True,
                                "isSubtle": True,
                                "spacing": "Medium"
                            }
                        ]
                    }
                }
            ]
        }
 
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            logging.info("Teams webhook sent successfully")
        except Exception as e:
            logging.error(f"Teams webhook failed: {str(e)}")
 
 