# Usage: locust -f locustfile-exif.py --no-web -c 1 -r 1 -t 1m --only-summary --csv=output

import config
import sys
import requests
import os
import json
import random
from PIL import Image, ExifTags
from locust import HttpLocust, task, seq_task, TaskSet, TaskSequence, exception
from requests_toolbelt.multipart.encoder import MultipartEncoder
from requests_toolbelt.utils import dump
from locust.exception import StopLocust


class MyTaskSet(TaskSet):
    photoId = None
    exifdata_orig = None

    def on_start(self):
        config.token = self.login()
        global photoId
        photoId = self.upload(config.image_file, config.image_format)

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

    def upload(self, image_file, image_format):
        auth = 'Bearer ' + config.token
        filename = os.path.basename(config.image_file)
        encoder = MultipartEncoder(
            fields={'galleryTypeCode': 'family', 'photoTypeCode': 'booking-photo',
                    'photoFile': (filename, open(image_file, 'rb'), image_format)})
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

    def get_exif(self, image_file):
        return dict(Image.open(image_file).getexif())

    def check_response(self, response):
        if response.status_code != 200:
            data = dump.dump_response(response)
            print(data.decode('utf-8'))
            sys.exit()

    def compare_exif(self, d1, d2, display):
        assert (len(d1) == len(d2)), 'Expected %d tags, got %d' % (len(d1), len(d2))
        print('Both have {} EXIF tags ...'.format(len(d1)))

        assert (d1.keys() == d2.keys()), 'EXIF tags mismatch'

        for k in d1.keys():
            assert (d1[k] == d2[k]), '{}: {} == {}'.format(k, d1[k], d2[k])
            if display:
                if ExifTags.TAGS.get(k, k) == 'GPSInfo':
                    for t in d1[k]:
                        print('{}: {} == {}'.format(ExifTags.GPSTAGS.get(t, t), d1[k][t], d2[k][t]))
                else:
                    print('{}: {} == {}'.format(ExifTags.TAGS.get(k, k), d1[k], d2[k]))

    @seq_task(1)
    @task(1)
    def pull_meta(self):

        auth = 'Bearer ' + config.token
        header = {
            'Authorization': auth,
            'Ocp-Apim-Subscription-Key': config.apim_key,
            'Content-Type': 'application/json'
        }
        print('Querying EXIF data from ' + photoId + ' ...')

        with self.client.get(url=config.photoinfo_url + '/' + photoId, headers=header) as response:
            self.check_response(response)

        self.compare_exif(self.get_exif(config.image_file), self.response, True)

        raise StopLocust()


class MyLocust(HttpLocust):
    host = config.host
    task_set = MyTaskSet
    min_wait = config.min_wait
    max_wait = config.max_wait