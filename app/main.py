import os
from pathlib import Path

from flask import Flask,jsonify

from app.api import api
from app.faults import LedgerError
from app.ledger.bookshelf import Bookshelf
from app.web import pages


def create_app(path=None):
    service=Flask(__name__)
    service.jinja_env.autoescape=True
    service.config['MAX_CONTENT_LENGTH']=5*1024*1024
    service.extensions['receipt_bookshelf']=Bookshelf(Path(path or os.getenv('PALETTE_SHELF','var/receipts')))
    service.register_blueprint(api)
    service.register_blueprint(pages)

    @service.errorhandler(LedgerError)
    def bad(error):
        return jsonify(code=error.code,message=str(error)),error.status

    @service.errorhandler(413)
    def oversized(_):
        return jsonify(code='PACKET_LIMIT',message='表单包超过 5 MiB'),413

    return service
