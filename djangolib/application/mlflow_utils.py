import mlflow
import requests
import os

def init_mlflow():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("database_access_monitoring")
    #print("Experiment:", mlflow.get_experiment_by_name("database_access_monitoring"))


# Configuration des seuils d'alerte (à ajuster selon vos besoins)
THRESHOLD_RESPONSE_TIME = 2.0  # en secondes
THRESHOLD_ERROR_RATE = 0.05  # 5%
THRESHOLD_CPU_UTILIZATION = 80  # en pourcentage
THRESHOLD_MEMORY_UTILIZATION = 80  # en pourcentage
THRESHOLD_STORAGE_UTILIZATION = 80  # en pourcentage


# Affectation des variables d'environnement
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1194197972859240549/bIM9M48OQjhzfSzbYUz58UF26pUwFAdKRqnutEqSzHzhsEwCPTnqF2NxyQziWeMkHkmc")

# Fonction d'envoi de notification sur serveur Discord
def send_alert_discord(subject, body):
    print("webhook:", DISCORD_WEBHOOK_URL, flush=True)
    payload = {
        "content": f"**{subject}**\n{body}"
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)