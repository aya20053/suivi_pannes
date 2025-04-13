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
    'recipients': [os.getenv('EMAIL_RECIPIENTS')] if os.getenv('EMAIL_RECIPIENTS') else []
}

NOTIFICATION_CONFIG = {
    'enabled': os.getenv('NOTIFICATION_ENABLED', 'False').lower() == 'true',
    'failed_pings_threshold': int(os.getenv('FAILED_PINGS_THRESHOLD', 1)),
    'monitoring_interval': int(os.getenv('MONITORING_INTERVAL', 60))
    # Add other notification configurations here if needed
}