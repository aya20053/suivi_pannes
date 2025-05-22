import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_CONFIG = {
    'enabled': os.getenv('EMAIL_ENABLED', 'True').lower() == 'true',
    'server': os.getenv('EMAIL_SERVER'),
    'port': int(os.getenv('EMAIL_PORT', 465)),
    'username': os.getenv('EMAIL_USERNAME'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'sender': os.getenv('EMAIL_SENDER'),

    # Configuration de la base de données
    'db': {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }
}

NOTIFICATION_CONFIG = {
    'enabled': os.getenv('NOTIFICATION_ENABLED', 'False').lower() == 'true',
    'failed_pings_threshold': int(os.getenv('FAILED_PINGS_THRESHOLD', 1)),
    'monitoring_interval': int(os.getenv('MONITORING_INTERVAL', 60))
}
