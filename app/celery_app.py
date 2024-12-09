from celery import Celery

celery = Celery()  

def make_celery(app):
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
    )
    celery.app = app  # Tambahkan aplikasi Flask ke Celery
    print(f"Celery app linked to Flask app: {celery.app is not None}")  # Tambahkan log debug
    return celery
