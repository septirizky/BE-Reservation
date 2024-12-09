from flask import Flask
from flask_cors import CORS
from .config import Config
from .celery_app import make_celery  # Pastikan ini di-import
from grist_api import GristDocAPI

from .controllers.grist.branch import branch_controller
from .controllers.grist.itemMenu import itemMenu_controller
from .controllers.grist.categoryItemMenu import categoryItemMenu_controller
from .controllers.grist.itemOption import itemOption_controller
from .controllers.grist.itemPackage import itemPackage_controller
from .controllers.grist.option import option_controller
from .controllers.grist.table import table_controller
from .controllers.mongodb.customer import customer_controller
from .controllers.mongodb.reservation import reservation_controller
from .controllers.mongodb.reservation_dashboard import reservation_dashboard_controller
from .controllers.mongodb.invoice import invoice_controller
from .controllers.mongodb.user import user_controller
from .controllers.mongodb.refund import refund_controller
from .controllers.mongodb.disbursement import disbursement_controller


def reservation_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Inisialisasi API Grist
    app.api = GristDocAPI(
        server=app.config['SERVER'],
        doc_id=app.config['DOC_ID'],
        api_key=app.config['API_KEY'],
    )

    # Database MongoDB
    app.config['db'] = Config().db

    # Inisialisasi Celery
    make_celery(app)

    # Daftarkan semua blueprint
    app.register_blueprint(branch_controller)
    app.register_blueprint(itemMenu_controller)
    app.register_blueprint(categoryItemMenu_controller)
    app.register_blueprint(itemOption_controller)
    app.register_blueprint(itemPackage_controller)
    app.register_blueprint(option_controller)
    app.register_blueprint(table_controller)

    app.register_blueprint(customer_controller)
    app.register_blueprint(reservation_controller)
    app.register_blueprint(reservation_dashboard_controller)
    app.register_blueprint(invoice_controller)
    app.register_blueprint(user_controller)
    app.register_blueprint(refund_controller)
    app.register_blueprint(disbursement_controller)

    return app
