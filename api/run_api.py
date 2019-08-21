from flask import Flask
from flask_cors import CORS

from flask import Blueprint
from downloader import api as download
from flask_restplus import Api
from celery import Celery


blueprint = Blueprint('api', __name__)

api = Api(blueprint,title='File downloader',
    version='1.0',
    description='Downloader'
    )

api.add_namespace(download,path='/')
#print(dir(google_ocr_topline))



app = Flask(__name__)
##app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
##app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
##celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
##celery.conf.update(app.config)

CORS(app)
app.register_blueprint(blueprint, url_prefix='/api')



def create_app():
    return app


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080,debug=True)
