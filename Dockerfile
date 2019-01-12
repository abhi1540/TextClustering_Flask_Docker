


FROM continuumio/anaconda3:4.4.0
EXPOSE 8000
RUN apt-get update && apt-get install -y apache2 \
    apache2-dev \   
    vim \
 && apt-get clean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /var/www/text_cluster_api/
CMD chmod -R 777 /var/www/ 
COPY ./text_cluster_api.wsgi /var/www/text_cluster_api/text_cluster_api.wsgi
COPY ./textclustering_dockerdemo /var/www/text_cluster_api/
COPY ./nltk_data /var/www/
RUN pip install -r requirements.txt
RUN /opt/conda/bin/mod_wsgi-express install-module
RUN mod_wsgi-express setup-server text_cluster_api.wsgi --port=8000 \
    --user www-data --group www-data \
    --server-root=/etc/mod_wsgi-express-80
CMD /etc/mod_wsgi-express-80/apachectl start -D FOREGROUND
