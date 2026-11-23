from flask import Blueprint,current_app,jsonify,request

from app.faults import LedgerError
from app.job import MixingJob,VIEWS
from app.ledger.closeout import close
from app.ledger.signoff import certify
from app.receipts.packet import read_sample

api=Blueprint('palette',__name__,url_prefix='/api')


def bookshelf():
    return current_app.extensions['receipt_bookshelf']


@api.get('/trial/<sample>/<stage>')
def trial(sample,stage):
    if stage not in VIEWS:
        raise LedgerError('STAGE_ABSENT','没有这项核料工序',404)
    return jsonify(getattr(MixingJob(read_sample(sample)),stage))


@api.route('/books',methods=['GET','POST'])
def books():
    book=bookshelf()
    if request.method=='GET':
        return jsonify(books=book.listing())
    record,reused=close(book,request.get_json(silent=True))
    manifest=record['manifest']
    return jsonify(key=manifest['key'],reused=reused,manifest=manifest,totals=record['snapshot']['balance']['totals'])


@api.get('/books/<key>')
def record(key):
    item=bookshelf().require(key)
    return jsonify(manifest=item['manifest'],balance=item['snapshot']['balance'])


@api.get('/export/<key>')
def export(key):
    response=jsonify(certify(bookshelf().require(key)))
    response.headers['Content-Disposition']=f'attachment; filename="palette-{key}.json"'
    return response
