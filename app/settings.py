class Settings:
    MAIN_DOMAIN = 'example.com'
    API_DOMAIN = 'api.example.com'

    STATIC_PATH = '/static'
    STATIC_URL = f'https://{API_DOMAIN}/static'

    ORIGINS = [
        f'http://{MAIN_DOMAIN}',
        f'https://{MAIN_DOMAIN}',
        f'http://{API_DOMAIN}',
        f'https://{API_DOMAIN}'
    ]

    SMTP_SERVER = 'example.com'
    SMTP_PORT = 465

    SMTP_USER = 'noreply@example.com'
    SMTP_PASS = 'password'

    MAIL_FROM_NAME = 'FlashNest'
