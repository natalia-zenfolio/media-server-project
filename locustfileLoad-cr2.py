# Usage: locust -f locustfileLoad.py --no-web -c 1 -r 1 -t 15m --only-summary --csv=output

import config
import sys
import requests
import os
import json
import random
#import locust.stats
from locust import HttpLocust, task, seq_task, TaskSet, TaskSequence, exception
from requests_toolbelt.multipart.encoder import MultipartEncoder
from requests_toolbelt.utils import dump
from locust.exception import StopLocust



class MyTaskSet(TaskSet):

    photoId = None

    def on_start(self):
        config.token = self.login()
        global photoId
        photoId = self.upload(config.image_file_cr2, config.image_format_cr2)

    def login(self):
        # login in and get access token
        header = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': config.apim_key
        }
        body = {
            'userName': config.username,
            'password': config.password
        }
        print('logging in ' + config.username + ' ...')
        with self.client.post(url=config.login_url, json=body, headers=header) as response:
            self.check_response(response)
        return response.json()['token']

    def upload(self, image_file_cr2, image_format_cr2):
        auth = 'Bearer ' + config.token
        filename = os.path.basename(config.image_file_cr2)
        encoder = MultipartEncoder(
            fields={'galleryTypeCode': 'family', 'photoTypeCode': 'booking-photo',
                    'photoFile': (filename, open(image_file_cr2, 'rb'), image_format_cr2)})
        header = {
            'Authorization': auth,
            'Ocp-Apim-Subscription-Key': config.apim_key,
            'Content-Type': encoder.content_type
        }
        print('Uploading ' + filename + ' ...')
        with self.client.post(url=config.query_url, headers=header, data=encoder) as response:
            self.check_response(response)
        print(response.json()['photoId'] + ': ' + str(response.elapsed.total_seconds()))
        return response.json()['photoId']

    def check_response(self, response):
        if response.status_code != 200:
            data = dump.dump_response(response)
            print(data.decode('utf-8'))
            sys.exit()

    @seq_task(1)
    @task(1)
    def query_image(self):
        auth = 'Bearer ' + config.token
        header = {
            'Authorization': auth,
            'Ocp-Apim-Subscription-Key': config.apim_key,
            'Content-Type': 'application/json'
        }
        param = {
            #'sizeTypeCode': '200x133'
        }
        print('Querying ' + photoId + ' ...')
        with self.client.get(url=config.query_url + '/' + photoId, params=param, headers=header, name=config.query_url) as response:
            self.check_response(response)
            downloaded_size = int(response.headers['content-length'])
            downloaded_format = response.headers['content-type']
            file_size = os.path.getsize(config.image_file_cr2)
            assert (file_size == downloaded_size), "Got %d, expected %d" % (file_size, downloaded_size)
            assert (downloaded_format == config.image_format_cr2), "Got %s, expected %s" % (downloaded_format, config.image_format_cr2)

            raise StopLocust()


class MyLocust(HttpLocust):
    host = config.host
    task_set = MyTaskSet
    min_wait = config.min_wait
    max_wait = config.max_wait
    


