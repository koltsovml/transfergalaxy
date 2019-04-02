import scrapy
import json


class QuotesSpider(scrapy.Spider):
    name = "transfergalaxy"

    def start_requests(self):
        # parse available countries
        url = 'https://transfergalaxy.com/umbraco/Surface/RemittanceSurface/SetSession'
        params = {
            'countryAlpha3': 'GBR',
        }
        # yield scrapy.Request(url=url, callback=self.parse)
        yield scrapy.FormRequest(url, callback=self.parse, method='POST', formdata=params)

    def parse(self, response):
        # url = 'https://transfergalaxy.com'
        # yield scrapy.Request(url=url, callback=self.parse_countries)

        # url = 'https://transfergalaxy.com/en/destination/cameroon'
        # yield scrapy.Request(url=url, callback=self.parse_services)

        # url = 'https://transfergalaxy.com/umbraco/Surface/RemittanceSurface/GetNetworksWithCurrencyJson'
        # params = {
        #     'alpha3': 'CMR',
        #     'serviceCode': 'CSH'
        # }
        # yield scrapy.FormRequest(url, callback=self.parse_networks, method='GET', formdata=params)

        url = 'https://transfergalaxy.com/umbraco/Surface/RemittanceSurface/InternalAoc'
        params = {
            'SendingCurrency': 'GBP',
            'ReceivingCurrency': 'XAF',
            #'ReceivingCountryCode': '+237',
            #'CurrentPageId': '8490',
            'cultureInfo': 'en-US',
            'SendingCountryAlpha3': 'GBR',
            'ReceivingCountryAlpha3': 'CMR',
            'ServiceCode': 'CSH',
            'RemittanceNetworkId': '31',
            'SendingAmount': '100',
        }
        yield scrapy.FormRequest(url, callback=self.parse_form, method='POST', formdata=params)

    def parse_countries(self, response):
        self.save_to_file(response)
        options = response.xpath('//select[@id="ReceivingCountryAlpha3"]/option[not(@disabled)]')
        results = []

        for option in options:
            country = option.xpath('./text()').extract_first()
            code = option.xpath('./@value').extract_first()
            destination = option.xpath('./@data-url').extract_first()

            if destination != '-':
                results.append({
                    'name': country,
                    'alpha3': code,
                    'data_url': destination,
                })
        # print('_____________________________________DATA________________________________________')
        # # print(data)
        # print(results)
        # print('_____________________________________DATA________________________________________')

    def parse_services(self, response):
        self.save_to_file(response)
        options = response.xpath('//select[@id="ServiceCode"]/option[not(@disabled)]')

        serviceCodes = []

        for option in options:
            service = option.xpath('./@value').extract_first()

            if service != "":
                serviceCodes.append(service)
        print('_____________________________________serviceCodes________________________________________')
        # print(data)
        print(serviceCodes)
        print('_____________________________________serviceCodes________________________________________')

    def parse_networks(self, response):
        self.save_to_file(response)
        jsonresponse = json.loads(response.body_as_unicode())
        networks = jsonresponse['networks']
        currency = jsonresponse['currency']

        print('_____________________________________parse_networks________________________________________')
        print(networks)
        print(currency)
        print('_____________________________________parse_networks________________________________________')

    def parse_form(self, response):
        self.save_to_file(response)
        data = response.xpath('//table[@class="index-table"]/tbody/tr')
        sendAmount = data[0].xpath('./td/text()').extract_first()
        fee = data[1].xpath('./td/text()').extract_first()
        to_pay = data[2].xpath('./td/text()').extract_first()
        receive = data[3].xpath('./td/text()').extract_first()


        print('_____________________________________parse_networks________________________________________')
        print(sendAmount)
        print(fee)
        print(to_pay)
        print(receive)
        print('_____________________________________parse_networks________________________________________')

    def save_to_file(self, response):
        page = response.url.split("/")[-2]
        filename = 'quotes-%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)
