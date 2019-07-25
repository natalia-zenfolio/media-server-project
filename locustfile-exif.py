import config
import sys
import requests
import os
import json
import random
import exifread
# import locust.stats
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
        global exifdata_orig
        photoId = self.upload(config.image_file, config.image_format)
        exifdata_orig = self.get_exif(config.image_file)

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
        f = open(image_file, 'rb')
        exifdata_orig = exifread.process_file(f)
        f.close()
        return exifdata_orig

    def check_response(self, response):
        if response.status_code != 200:
            data = dump.dump_response(response)
            print(data.decode('utf-8'))
            sys.exit()

    def compare_exif(self, d1, d2):
        assert (len(d1) == len(d2)), 'Expected %d tags, got %d' % (len(d1), len(d2))
        print('Has {} EXIF tags ...'.format(len(d1)))

        d1_keys = set(d1.keys())
        d2_keys = set(d2.keys())
        print(d1_keys)
        intersect_keys = d1_keys.intersection(d2_keys)
        assert (d1_keys == intersect_keys), 'EXIF tags mismatch'

        # Up to this point, the 2 Exif dictionaries have identical tags. However, their values don't necessarily match.
        # In fact, some tags are expected to be different. e.g. 'Image DateTime', 'EXIF ImageExifImageWidth', 'EXIF ExifImageLength'.
        # So, modify this routine to check only the desired tags listed in the ticket.

        # Desired EXIF tags to compare
        tags = ['Image Make', 'Image Model', 'EXIF ExifImageWidth', 'EXIF ExifImageLength', 'EXIF ExposureTime',
                'EXIF FNumber', 'EXIF ISOSpeedRatings', 'EXIF ApertureValue', 'MakerNote RecordMode',
                'Image Orientation']
        ###for tag in tags:
        ###    print('{}: {} == {}'.format(tag, d1[tag], d2[tag]))

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
            #'sizeTypeCode': '200x133'  # use "resize" to ensure resized image still has EXIF
        }
        print('Querying ' + photoId + ' ...')

        with self.client.get(url=config.query_url + '/' + photoId, params=param, headers=header,
                             name=config.query_url) as response:
            self.check_response(response)

            with open(config.image_file_dwnld, 'wb') as downloaded_image:
                for chunk in response.iter_content(chunk_size=128):
                    downloaded_image.write(chunk)

        self.compare_exif(exifdata_orig, self.get_exif(config.image_file_dwnld))

        raise StopLocust()


class MyLocust(HttpLocust):
    host = config.host
    task_set = MyTaskSet
    min_wait = config.min_wait
    max_wait = config.max_wait