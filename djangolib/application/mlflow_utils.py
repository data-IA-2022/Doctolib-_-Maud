import mlflow
import requests
import os

def init_mlflow():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("database_access_monitoring")

#serveur discord
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1194197972859240549/bIM9M48OQjhzfSzbYUz58UF26pUwFAdKRqnutEqSzHzhsEwCPTnqF2NxyQziWeMkHkmc")

#fonction d'envoi de notification sur serveur Discord
def send_alert_discord(subject, body):
    try:
        payload = {
            "content": f"**{subject}**\n{body}"
        }
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print('Alert sent successfully.')
    except Exception as e:
        print(f'Error sending Discord alert: {e}')