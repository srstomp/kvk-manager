import requests
import pymongo
import json
import logging
from bs4 import (
    BeautifulSoup,
    NavigableString,
    Tag
)
import re
from urllib.parse import quote

# l7xx2cca3b2798df458a8a8d49e8e0a4478e
# l7xx6752e2e19e9c4f80afc28352c2a3cec8
#"nextLink": "https://api.kvk.nl/api/v2/search/companies?q=1013XC&user_key=l7xx6752e2e19e9c4f80afc28352c2a3cec8&startPage=2"

class KVKClient():
    MONGO_URL = 'mongodb://localhost:27017/'
    POSTAL_CODE_URL = 'http://www.metatopos.eu/nederland2.html'
    KVK_URL = ''
    BASE_URL = 'https://api.kvk.nl/api/v2/search/companies?'
    DATABASE = 'kvk'
    COLLECTION = 'search'

    def __init__(self):
        # init logger
        self.logger = self.configure_logging()
        self.logger.info('KVK Client initialized without credentials')

    def set_api_credentials(self, api_key, mongo_url, database, collection):
        self.api_key = api_key
        self.client = pymongo.MongoClient(mongo_url)
        self.db = self.client[database]
        self.collection = self.db[collection]
        # init logger
        self.logger = self.configure_logging()
        self.logger.info('Set API credentials | '
                         'API Key: {} | '
                         'MongoDB: {} | '
                         'Database: {} | '
                         'Collection: {}'.format(api_key, mongo_url, database, collection))

    def fetch_items_from_api(self, url):
        with open(url) as read_file:
            data = json.load(read_file)
            items = data['data']['items'] if 'items' in data['data'] else [None]
            nextLink = data['data']['nextLink'] if 'nextLink' in data['data'] else ''

            return({'items': items, 'nextLink': nextLink})

    def populate_database_with_items(self, items):
        self.collection.insert_many(items)

    def empty_database(self):
        self.collection.delete_many({})
        self.logger.info('Succesfully emptied the database')

    def fetch_postalcodes(self):
        self.logger.info('Fetching postal codes from {}'.format(self.POSTAL_CODE_URL))

        # fetch html data
        request = requests.get(self.POSTAL_CODE_URL)
        soup = BeautifulSoup(request.text, 'html.parser')

        # find all postal codes via regex
        pattern = re.compile(r"^(\d)(\d)(\d)(\d)$")
        result = soup.find_all('td', text=pattern)

        postalcodes = []

        # add all unique postal codes to an array
        for item in result:
            if not item in postalcodes:
                postalcodes.append(item.string)

        self.logger.info('Succesfully fetched {} postal codes'.format(len(postalcodes)))
        return postalcodes

    # todo - fix search string with '&'
    def search_company(self, company_name='', kvk='', street='', postal_code='', house_number='', city=''):
        companies = []

        # search the kvk website for a company and then parse the address from it
        urlencodedString = quote(company_name)

        website = 'https://zoeken.kvk.nl/search.ashx?handelsnaam=' + urlencodedString + \
                  '&kvknummer=' + kvk + \
                  '&straat=' + street + \
                  '&postcode=' + postal_code + \
                  '&huisnummer=' + house_number + \
                  '&plaats=' + city + \
                  '&hoofdvestiging=1&rechtspersoon=1&nevenvestiging=1&zoekvervallen=0&zoekuitgeschreven=1&start=0&searchfield=uitgebreidzoeken'
        # fetch html data
        print(website)
        request = requests.get(website)
        soup = BeautifulSoup(request.text, 'html.parser')

        if soup.find('ul', class_='results') == None:
            return {}

        # loop through results
        for item in soup.find('ul', class_='results').children:
            # check if item is a NavigableString. If so skip it else parse it
            if isinstance(item, NavigableString):
                continue
            if isinstance(item, Tag):
                company = self.parse_kvk_search_result(item)

                if company != None:
                    companies.append(company)

        return companies

    def parse_kvk_search_result(self, item):
        company = {}

        # extract business name tag
        businessNameTag = item.find('div', class_='more-search-info')

        # if a tag with the class more-search-info can't be found, exit
        if businessNameTag == None:
            return None

        # parse business names
        businessNames = businessNameTag.p.text.split(' | ')

        # fill the company json object with trade name(s) data
        company['tradeNames'] = {}
        company['tradeNames']['businessName'] = businessNames[0]
        company['tradeNames']['currentTradeNames'] = businessNames

        # parse kvk data
        kvkMetaTag = item.find('ul', class_='kvk-meta')

        # set KVK number
        kvkPattern = re.compile(r"^KVK.*")
        company['kvkNumber'] = kvkMetaTag.find('li', text=kvkPattern).text[4:]

        # set Branch number
        branchPattern = re.compile(r"^Vestigingsnr.*")
        company['branchNumber'] = kvkMetaTag.find('li', text=branchPattern).text.split(' ')[1]

        # set address data (splitted)
        streetPattern = re.compile(r"((?:\d+[\s;a-zA-Z-]*)$|(?:\d+[\s-]))")
        # (?:\d+[\s;a-zA-Z-]*)$
        address = self.kvkMetaHelper(kvkMetaTag, 3)
        houseNumber = streetPattern.search(address) if streetPattern.search(address) != None else ""
        houseNumberAdditionPattern = re.compile(r"([a-zA-z]|(?:-[0-9])|(?:\s[0-9]$))")
        houseNumberAddition = houseNumberAdditionPattern.search(
            houseNumber.group()).group() if houseNumberAdditionPattern.search(
            houseNumber.group()) != None else ""

        company['street'] = address[:houseNumber.start(1) - 1]  # address.replace(' ' + houseNumber.group(), '')
        company['houseNumber'] = houseNumber.group().replace(houseNumberAddition, '')
        company['houseNumberAddition'] = houseNumberAddition.replace((' |-'), '')

        # set postal Code
        postalCodePattern = re.compile(r"(^[1-9][0-9]{3}[A-Za-z]{2}|^[1-9][0-9]{3}[\s][A-Za-z]{2})")
        postalCode = self.kvkMetaHelper(kvkMetaTag, 4)
        company['postalCode'] = postalCodePattern.match(postalCode).group() if postalCodePattern.match(
            postalCode) else ""

        # set city
        company['city'] = self.kvkMetaHelper(kvkMetaTag, 5)

        return company

    def kvkMetaHelper(self, tag, index):
        return tag.select('li:nth-of-type(' + str(index) + ')')[0].text if tag.select(
            'li:nth-of-type(' + str(index) + ')') != None else ""

    def configure_logging(self):
        # configure logger to store in a local file
        logging.basicConfig(filename="info.log",
                            level=logging.INFO,
                            format="%(asctime)s:%(levelname)s:%(message)s")
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # output logs to the console
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[%(asctime)s %(levelname)s %(module)s]: %(message)s'))
        logger.addHandler(handler)
        return logger

if __name__ == '__main__':
    #client = KVKClient('', MONGO_URL, DATABASE, COLLECTION)
    #print(client.fetch_postalcodes())
    #result = client.fetch_items_from_url(KVK_URL)
    #client.populate_database_with_items(result['items'])
    #fetcher.collection.insert_many(result['items'])
    #client.populate_database_with_items(client.search_company('n=5'))
    client = KVKClient()
    print(client.search_company('', '63706903'))

#https://zoeken.kvk.nl/search.ashx?handelsnaam=&kvknummer=63706903&straat=&postcode=&huisnummer=&plaats=&hoofdvestiging=1&rechtspersoon=1&nevenvestiging=1&zoekvervallen=0&zoekuitgeschreven=1&start=0&searchfield=uitgebreidzoeken&_=1552821341672