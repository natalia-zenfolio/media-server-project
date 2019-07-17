# Usage: locust -f locustfileLoad-gif.py --no-web -c 1 -r 1 -t 55s --only-summary --csv=output
# gif conf file
token = None
username = 'natalia@zenfolio.com'
password = 'Nataliaminsk2019'
login_url = '/identities/v1/login'
upload_url = '/media/v1/photo'
query_url = '/media/v1/photo'
resize_url = '/media/v1/photo/resize'
dimension_url = '/media/v1/photo/dimensions'

min_wait = 1000
max_wait = 5000

image_file = 'C:\\work\\Locust\\photos\\p55709780-r0.gif'
image_format = 'image/gif'

# test deployment
apim_key = 'cbecfad8f6e7406e833e0bc77a69ca27'
host = 'https://test.zenfolio.work/api'

# perf deployment
#apim_key = 'af49f4fd45b14b0293d4be769ef47b14'
#host = 'https://performance-tests.zenfolio.work/api'
#host = 'https://zf-bnl-perf-svcfab.centralus.cloudapp.azure.com'

# local deployment
#apim_key = '44dc7c91f91d427688aadb8cacbe4a65'
#host = 'https://booking-listing.com/api'
#host = 'http://localhost:19081/api'
