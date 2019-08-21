import pika
import sys
import json
import uuid
from db import DBConnection
import mimetypes
import requests
from datetime import datetime
import time
import os
import settings

def download_file(db_init,job_id,url,already_processed):

    update_query={}
    update_query["job_id"]=job_id
    update_query["start_time"]=datetime.utcnow()
    update_query["status"]='STARTED'
    update_query["command"]="STARTED Download"

    file_mode = 'wb' if already_processed == 0 else 'ab'
    response = requests.get(url, stream=True)
    total = response.headers.get('content-length')
    content_type = response.headers.get('Content-Type')
    file_extension = mimetypes.guess_extension(content_type)
    
    write_file_path=os.path.join(settings.storage_path,job_id+file_extension)
    update_query["output_path"]=write_file_path
    
    db_init.update_job(update_query)
    
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
                #time.sleep(5)

    if not is_break:
        update_query={}
        update_query["job_id"]=job_id
        update_query["end_time"]=datetime.utcnow()
        update_query["status"]='COMPLETED'
        update_query["command"]="Finished Download"
        db_init.update_job(update_query)

        
class Worker(object):
    worker_id = ""

    def do_the_job(self, data):
        job_id = data["job_id"]
        status = data["status"]
        self.db_init = DBConnection()
        
        search_query={}
        search_query["job_id"]=job_id
        result=self.db_init.get_job({'job_id':job_id})
        if result:
            data=result[0]
            url=data["input_url"]
            already_processed=data["downloaded_size"] if status=="RESUME" else 0
            download_file(self.db_init,job_id,url,already_processed)
            
        self.db_init.close()

    def __init__(self,):
        self.queue_name = 'urls'
        self.exchange_name = 'info'
        self.host = settings.RABBITMQ_HOST
        self.user = settings.RABBITMQ_USER
        self.password = settings.RABBITMQ_PASS

        self.credentials = pika.PlainCredentials(self.user, self.password)

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=5672,
                                                                            credentials=self.credentials))

        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name)


    def callback(self, ch, method, properties, body):

        if body is not None or body != '':
            data = json.loads(body.decode())
            if 'job_id' in data and 'status' in data:
                try:
                    self.do_the_job(data)
                except Exception as e:
                    print(str(e))

            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("done with the job by worker - ", self.worker_id)

if __name__ == '__main__':
    worker = Worker()
    worker.channel.basic_qos(prefetch_count=1)
    worker.channel.basic_consume(worker.callback, queue='urls')
    worker.channel.start_consuming()
