# url_downloader

DEPLOYED LINK

http://13.232.15.183:8081/api/


###### image and container for API

docker build -t api_downloader -f Dockerfile .

docker run -d --name api_download -p 8081:8080 -v /opt/crawl/downloader/worker/files:/home/files api_downloader


##### image and container for worker

docker build -t worker -f Dockerfile .

docker run -d --name worker_con  -v /opt/crawl/downloader/worker/files:/home/files worker



##### Used tools and technology:

Flask

PostgreSQL

RabbitMQ

Swagger UI

Docker

