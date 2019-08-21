##Install Python
FROM python:3.6-alpine

#RUN apk add pip install --upgrade pip
##Install the Bash
RUN apk add --no-cache bash && apk add --no-cache g++ libxslt-dev openssh sshpass

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories

RUN apk update &&  apk add python3 postgresql-libs &&  apk add --virtual .build-deps gcc python3-dev musl-dev postgresql-dev &&  apk --purge del .build-deps && apk add postgresql-dev


##Copy the directory to container
COPY . /home/

RUN apk add libffi-dev openssl-dev git openssh
RUN pip install -r /home/requirements.txt

user root

#Run time parameter
#ENTRYPOINT ["/home/worker.py"]
CMD python /home/worker.py
