import scrapy
import json
import configparser

from transfergalaxy.helpers.DBConnection import DBConnection


class QuotesSpider(scrapy.Spider):
    name = "transfergalaxy_full"

    def __init__(self):
        # init config for DB
        self.config = configparser.ConfigParser()
        self.config.read('transfergalaxy/config/config.ini')

        # init db connection
        self.connection = DBConnection(
            self.config['DB']['host'], self.config['DB']['port'],
            self.config['DB']['user'], self.config['DB']['password'],
            self.config['DB']['database'], True)
        self.cursor = self.connection.get_cursor()
        self.result_table = self.config['TABLE']['Data']

    def start_requests(self):
        # parse available countries
        url = 'https://transfergalaxy.com/umbraco/Surface/RemittanceSurface/SetSession'
        countries = [
            # {
            #     'name': 'GBR',
            #     'currency': 'GBP'
            # },
            {
                'name': 'SWE',
                'currency': 'SEK',
            },
        ]

        for country in countries:
            params = {
                'countryAlpha3': country,
            }
            # yield scrapy.Request(url=url, callback=self.parse)
            yield scrapy.FormRequest(url, callback=self.parse, method='POST', formdata=params, meta={
                'sending_country': country['name'],
                'sending_currency': country['currency'],
            })


    def parse(self, response):
        url = 'https://transfergalaxy.com'
        yield scrapy.Request(url=url, callback=self.parse_countries, meta={
                'sending_country': response.meta['sending_country'],
                'sending_currency': response.meta['sending_currency'],
            })

        # url = 'https://transfergalaxy.com/en/destination/cameroon'
        # yield scrapy.Request(url=url, callback=self.parse_services)

        # url = 'https://transfergalaxy.com/umbraco/Surface/RemittanceSurface/GetNetworksWithCurrencyJson'
        # params = {
        #     'alpha3': 'CMR',
        #     'serviceCode': 'CSH'
        # }
        # yield scrapy.FormRequest(url, callback=self.parse_networks, method='GET', formdata=params)

        # url = 'https://transfergalaxy.com/umbraco/Surface/RemittanceSurface/InternalAoc'
        # params = {
        #     'SendingCurrency': 'GBP',
        #     'ReceivingCurrency': 'XAF',
        #     #'ReceivingCountryCode': '+237',
        #     #'CurrentPageId': '8490',
        #     'cultureInfo': 'en-US',
        #     'SendingCountryAlpha3': 'GBR',
        #     'ReceivingCountryAlpha3': 'CMR',
        #     'ServiceCode': 'CSH',
        #     'RemittanceNetworkId': '31',
        #     'SendingAmount': '100',
        # }
        # yield scrapy.FormRequest(url, callback=self.parse_form, method='POST', formdata=params)

    def parse_countries(self, response):
        # self.save_to_file(response)
        options = response.xpath('//select[@id="ReceivingCountryAlpha3"]/option[not(@disabled)]')
        destination_countries = []

        for option in options:
            country = option.xpath('./text()').extract_first()
            code = option.xpath('./@value').extract_first()
            destination = option.xpath('./@data-url').extract_first()

            if destination != '-':
                destination_countries.append({
                    'name': country,
                    'alpha3': code,
                    'data_url': destination,
                })

        # print('_____________________________________DATA________________________________________')
        # # print(data)
        # print(results)
        # print('_____________________________________DATA________________________________________')

        url = 'https://transfergalaxy.com/en/destination/cameroon'
        for destination_country in destination_countries:
            url = 'https://transfergalaxy.com{}'.format(destination_country['data_url'])
            yield scrapy.Request(url=url, callback=self.parse_services,
                                 meta={
                                     'sending_country': response.meta['sending_country'],
                                     'sending_currency': response.meta['sending_currency'],
                                     'destination_country': destination_country
                                 })


    def parse_services(self, response):
        # self.save_to_file(response)
        options = response.xpath('//select[@id="ServiceCode"]/option[not(@disabled)]')

        serviceCodes = []

        for option in options:
            service = option.xpath('./@value').extract_first()
            service_name = option.xpath('./text()').extract_first()
            if service != "":
                serviceCodes.append({
                    'name': service_name,
                    'code': service,
                })
        # print('_____________________________________serviceCodes________________________________________')
        # print(serviceCodes)
        # print('_____________________________________serviceCodes________________________________________')

        url = 'https://transfergalaxy.com/umbraco/Surface/RemittanceSurface/GetNetworksWithCurrencyJson'
        for serviceCode in serviceCodes:
            params = {
                'alpha3': response.meta['destination_country']['alpha3'],
                'serviceCode': serviceCode['code'],
            }
            yield scrapy.FormRequest(url, callback=self.parse_networks, method='GET', formdata=params,
                                     meta={
                                         'sending_country': response.meta['sending_country'],
                                         'sending_currency': response.meta['sending_currency'],
                                         'destination_country': response.meta['destination_country'],
                                         'service': serviceCode,
                                     })

    def parse_networks(self, response):
        # self.save_to_file(response)
        jsonresponse = json.loads(response.body_as_unicode())
        networks = jsonresponse['networks']
        currency = jsonresponse['currency']

        # print('_____________________________________parse_networks________________________________________')
        # print(networks)
        # print(currency)
        # print('_____________________________________parse_networks________________________________________')

        url = 'https://transfergalaxy.com/umbraco/Surface/RemittanceSurface/InternalAoc'
        for network in networks:
            networkId = network['Value']
            params = {
                'SendingCurrency': response.meta['sending_currency'],
                'ReceivingCurrency': currency,
                #'ReceivingCountryCode': '+237',
                #'CurrentPageId': '8490',
                'cultureInfo': 'en-US',
                'SendingCountryAlpha3': response.meta['sending_country'],
                'ReceivingCountryAlpha3': response.meta['destination_country']['alpha3'],
                'ServiceCode': response.meta['service']['code'],
                'RemittanceNetworkId': networkId,
                'SendingAmount': '100',
            }
            yield scrapy.FormRequest(url, callback=self.parse_form, method='POST', formdata=params,
                                     meta={
                                         'sending_country': response.meta['sending_country'],
                                         'sending_currency': response.meta['sending_currency'],
                                         'destination_country': response.meta['destination_country'],
                                         'service': response.meta['service'],
                                         'network': network,
                                     })

    def parse_form(self, response):
        # self.save_to_file(response)
        data = response.xpath('//table[@class="index-table"]/tbody/tr')
        sendAmountString = data[0].xpath('./td/text()').extract_first()
        fee = data[1].xpath('./td/text()').extract_first()
        to_pay = data[2].xpath('./td/text()').extract_first()
        receiveString = data[3].xpath('./td/text()').extract_first()

        fee = fee.split(" ")[0]
        sendAmount = sendAmountString.split(" ")[0]
        sendAmountCurrency = sendAmountString.split(" ")[1]
        receive = receiveString.split(" ")[0]
        receiveCurrency = receiveString.split(" ")[1]
        to_pay = to_pay.split(" ")[0]


        print('_____________________________________parse_networks________________________________________')
        print(sendAmount)
        print(fee)
        print(to_pay)
        print(response.meta['sending_country'])
        print(response.meta['sending_currency'])
        print(response.meta['destination_country'])
        print(response.meta['service'])
        print(response.meta['network'])
        print('_____________________________________parse_networks________________________________________')

        self.save_to_db({
            'sending_country': response.meta['sending_country'],
            'sending_currency': response.meta['sending_currency'],
            'sending_country_alpha3': response.meta['sending_country'],
            'receiving_country': response.meta['destination_country']['name'],
            'receiving_country_alpha3': response.meta['destination_country']['alpha3'],
            'service': response.meta['service']['name'],
            'service_id': response.meta['service']['code'],
            'network': response.meta['network']['Text'],
            'network_id': response.meta['network']['Value'],
            'send_amount': sendAmount,
            'send_amount_currency': sendAmountCurrency,
            'fee_amount': fee,
            'pay_amount': to_pay,
            'receive_amount': receive,
            'receive_amount_currency': receiveCurrency,
        })

    def save_to_file(self, response):
        page = response.url.split("/")[-2]
        filename = 'quotes-%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)

    def save_to_db(self, data):
        rows = ",".join(data.keys())
        values = "%(" + ")s, %(".join(data.keys()) + ")s"

        query = "INSERT INTO data ({}) VALUES ({})".format(rows, values)

        print('___________________________________QUERY___________________________________')
        print(query)

        self.cursor.execute(query, data)
