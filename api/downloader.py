from flask import Flask, abort, request, jsonify,Blueprint,send_file,after_this_request,send_from_directory
from flask_restplus import Namespace, Resource, fields,reqparse,Api, Resource

from flask import Flask, Response, jsonify, request
import os
import json
import requests
import settings
from datetime import datetime
from time import time
import uuid
from db import DBConnection
import mimetypes

from rabbitmq_connection import RabbitMQ
from werkzeug.datastructures import FileStorage
from werkzeug import secure_filename

import io

api = Namespace('downloader', description='URL download UI')

post_parser = reqparse.RequestParser()
post_parser.add_argument('url',  required = True, location="form",help='enter url')

get_parser = reqparse.RequestParser()
get_parser.add_argument('id',  required = False,help='enter url')

control_parser = reqparse.RequestParser()
control_parser.add_argument('id',  required = True,help='enter url')
control_parser.add_argument('state', type=str, choices=('PAUSE', 'STOP','RESUME'))


file_download = reqparse.RequestParser()
file_download.add_argument('id',  required = True,help='enter url')


file_upload = reqparse.RequestParser()
file_upload.add_argument('file_name', location="files",type=FileStorage)


@api.route('upload')
class UploadFile(Resource):

    @api.doc('file_upload')
    @api.expect(file_upload, validate=False)
    def post(self):
        db_init = DBConnection()
        f = request.files['file_name'] if 'file_name' in request.files else None
        if f:
            path = settings.storage_path
            file_ = f.filename
            job_id = str(uuid.uuid1())
            filename, file_extension = os.path.splitext(file_)
            full_path = os.path.join(path, job_id + file_extension)
            f.save(secure_filename(full_path))
            input_dict = {}
            input_dict["job_id"] = job_id
            input_dict["status"] = "COMPLETED"
            input_dict["start_time"] = datetime.utcnow()
            input_dict["output_path"] = full_path
            input_dict["command"] = ""
            input_dict["end_time"] = datetime.utcnow()
            db_init.insert_job(input_dict)
            db_init.close()
            return jsonify(input_dict)
        else:
            db_init.close()
            return "No file found"


@api.route('download')
class DownloadFile(Resource):

    @api.doc('post_parser')
    @api.expect(post_parser, validate=False)
    def post(self):
        
        db_init = DBConnection()
        job_id = str(uuid.uuid1())

        url=request.form['url'] if 'url' in request.form else None

        input_dict={}
        input_dict["job_id"]=job_id
        input_dict["status"]="SCHEDULED"
        input_dict["start_time"]=datetime.utcnow()
        input_dict["output_path"]=job_id
        
            
        input_dict["command"]="SCHEDULED Download"
        is_exist=False

        if not url:
            input_dict["command"]="no input url found Job"
            input_dict["end_time"]=datetime.utcnow()
            is_exist=True
        else:
            input_dict["input_url"]=url
       
        db_init.insert_job(input_dict)
        if is_exist:
            db_init.close()
            return jsonify(input_dict)

        message_to_publish={}
        message_to_publish['job_id']=job_id
        message_to_publish['status']='SCHEDULED'
        message_publisher(message_to_publish)

        update_query={}
        update_query["job_id"]=job_id
        
        db_init.close()
        
        
        return jsonify(update_query)


@api.route('status')
class GetStatus(Resource):
    @api.doc('get_parser')
    @api.expect(get_parser, validate=False)
    def get(self):
        db_init = DBConnection()
        job_id = request.args.get('id', None)
        output = []
        search_query = {}
        if job_id:
            search_query["job_id"] = "job_id"

        result = db_init.get_job({'job_id': job_id})
        date_time_format = '%Y-%m-%d %H:%M:%S'
        for item in result:
            updated_time = item["updated_time"]
            start_time = item["start_time"]
            downloaded_size = item["downloaded_size"]
            total_file_size = item["total_file_size"]
            estimated_time=0
            if downloaded_size and total_file_size:
                print(updated_time, start_time)
                diff_sec = date_diff_in_s(updated_time, start_time)
                estimated_time = ((float(total_file_size) - float(downloaded_size)) / float(downloaded_size)) * diff_sec
                db_init.close()
            temp = dict(item)
            temp["estimated_time_seconds"] = round(estimated_time, 2)
            return jsonify(temp)


@api.route('control')
class ControlStatus(Resource):
    @api.doc('get_parser')
    @api.expect(control_parser, validate=False)
    def get(self):
        db_init = DBConnection()
        job_id = request.args.get('id', None)
        state = request.args.get('state', None)
        update_query = {}

        update_query["status"] = state
        update_query["job_id"] = job_id
        if state in ['PAUSE', 'STOP', 'RESUME']:

            db_init.update_job(update_query)
            update_query["message"] = 'updated download status'

            if state == 'RESUME':
                message_to_publish = {}
                message_to_publish['job_id'] = job_id
                message_to_publish['status'] = 'RESUME'
                message_publisher(message_to_publish)
        else:
            update_query["message"] = "no contol found"

        db_init.close()

        return jsonify(update_query)

@api.route('file')
class FileDownload(Resource):
    @api.doc('get_parser')
    @api.expect(file_download, validate=False)
    def get(self):
        db_init = DBConnection()
        job_id = request.args.get('id', None)
        search_query = {}
        search_query["job_id"] = job_id

        result = db_init.get_job(search_query)
        print(result)
        out_path = ""
        for item in result:
            out_path = item["output_path"]

        @after_this_request
        def add_header(r):
            """
            Add headers to both force latest IE rendering engine or Chrome Frame,
            and also to cache the rendered page for 10 minutes.
            """
            r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            r.headers["Pragma"] = "no-cache"
            r.headers["Expires"] = "0"
            r.headers['Cache-Control'] = 'public, max-age=0'
            return r

        response = send_from_directory(directory=os.path.dirname(out_path), filename=os.path.basename(out_path))
        return response


def date_diff_in_s(dt2, dt1):
  timedelta = dt2 - dt1
  return timedelta.days * 24 * 3600  + timedelta.seconds #* 1000


def message_publisher(message_dict):
    init_rabbit=RabbitMQ()
    init_rabbit.publish(message_dict)


def download_file(job_id,url, filename,already_processed):
    print(job_id,url, filename,"xxxxxxxxxxxxx")
    db_init = DBConnection()
    file_mode='wb' if already_processed==0 else 'ab'
    response = requests.get(url, stream=True)
    total = response.headers.get('content-length')
    content_type=response.headers.get('Content-Type')
    file_extension = mimetypes.guess_extension(content_type)
    write_file_path=filename+file_extension
    is_break=False
    with open(write_file_path, file_mode) as f:
        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                update_query={}
                update_query["job_id"]=job_id
                
                result=db_init.get_job({'job_id':job_id})
                if result:
                    status=result[0]['status']
                    if status in ["PAUSE","STOP"]:
                        update_query["status"]=status
                        is_break=True
                    
                if downloaded > already_processed:
                    already_processed=0
                else:
                    continue

                if is_break:
                    db_init.update_job(update_query)
                    break
                    
                f.write(data)
                done = int(50*downloaded/total)
                print(total,downloaded,)
                
                
                update_query["total_file_size"]=total
                update_query["downloaded_size"]=downloaded
                update_query["remaining_size"]=total-downloaded
                db_init.update_job(update_query)

    if not is_break:
        update_query={}
        update_query["job_id"]=job_id
        update_query["end_time"]=datetime.utcnow()
        update_query["status"]='COMPLETED'
        update_query["command"]="Finished Download"
        
    db_init.close()
