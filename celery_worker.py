from app import reservation_app  # Import aplikasi Flask dari __init__.py
from app.celery_app import make_celery, celery  # Import make_celery dan celery instance

# Buat aplikasi Flask
app = reservation_app()

# Inisialisasi Celery dengan aplikasi Flask
make_celery(app)
