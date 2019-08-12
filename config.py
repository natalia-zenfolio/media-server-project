# Usage: locust -f locustfile-exif.py --no-web -c 1 -r 1 -t 55s --only-summary --csv=output

token = None
username = 'stanley@zenfolio.com'
password = 'welcomE1234'
login_url = '/identities/v1/login'
upload_url = '/media/v1/photo'
query_url = '/media/v1/photo'
resize_url = '/media/v1/photo/resize'
dimension_url = '/media/v1/photo/dimensions'
photoinfo_url = '/media/v1/photo/info'

min_wait = 1000
max_wait = 5000

image_file = 'C:\\work\\Locust\\photos\\exif.jpg'
image_format = 'image/jpeg'

# test deployment
apim_key = 'cbecfad8f6e7406e833e0bc77a69ca27'
host = 'https://test.photobooker.com/api'
