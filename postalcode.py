# def get_zip(url):
#     # download from web
#     response = requests.get(url)
#     # unzip the content
#     zipfile = ZipFile(BytesIO(response.content))
#     for info in zipfile.infolist():
#         print(info.filename)
#         print('\tComment:\t', info.comment)
#         print('\tModified:\t', datetime.datetime(*info.date_time))
#         print('\tSystem:\t\t', info.create_system, '(0 = Windows, 3 = Unix)')
#         print('\tZIP version:\t', info.create_version)
#         print('\tCompressed:\t', info.compress_size, 'bytes')
#         print('\tUncompressed:\t', info.file_size, 'bytes')
#     zipfile.extractall('downloads')
#     zipfile.close()


#from io import BytesIO
#from zipfile import ZipFile
#import datetime
#import requests

from bs4 import BeautifulSoup
import urllib3
import re

def fetch_postalcode():
    url = 'http://www.metatopos.eu/nederland1.html'
    http_pool = urllib3.connection_from_url(url)
    html = http_pool.urlopen('GET', url)
    soup = BeautifulSoup(html.data, 'html.parser')

    pattern = re.compile(r"^(\d)(\d)(\d)(\d)$")
    result = soup.find_all('td', text=pattern)

    for link in result:
        print(link.string)

if __name__ == '__main__':
    fetch_postalcode()