import scrapy
from scrapy.http.request import Request
from ..items import WebscrapingItem
import requests
import re
import json

class TargetSpider(scrapy.Spider):
    name = 'target'
    allowed_domains = ['target.com']
    start_urls = ['https://www.target.com/p/apple-iphone-13-pro-max/-/A-84616123?preselect=84240109&aui=true#lnk=sametab']

    q_api_link = 'https://r2d2.target.com/ggc/Q&A/v1/question-answer?type=product&questionedId=%s&page=0&size=10&sortBy=MOST_ANSWERS&key=%s&errorTag=drax_domain_questions_api_error'


    def converter(self,element,type_convert):
        try:
            if type_convert == 'int':
                converted_element = int(element)
            elif type_convert == 'json':
                converted_element = json.loads(element)
            else:
                print("type %s not recognized for %s"%(type_convert,element))
            print("conversion to %s is completed"%type_convert)
        except Exception as e:
            print("%s conversion to %s not successfull"%(element,type_convert))
            print(e)
            return None

        return converted_element

    def get_questions(self,questions_json):
        questions_list = []
        try:
            questions = questions_json.get('results')
            for q in questions:
                question_dicts = {}
                question = q.get('text')
                print("question_text: %s"%question)
                question_dicts['question'] = question
                question_dicts['author'] = q.get('author').get('nickname')
                print("author: %s"%question_dicts['author'])
                answers = q.get('answers')
                answer_list = []
                for ans in answers:
                    answer_dicts = {}
                    answer_dicts['answer_text'] = ans.get('text')
                    answer_dicts['author'] = ans.get('author').get('nickname')
                    if ans.get('author').get('badges'):
                        answer_dicts['badge'] = ", ".join([badge for badge in ans.get('author').get('badges')])
                    answer_list.append(answer_dicts)
                    question_dicts['answers'] = answer_list
                questions_list.append(question_dicts)
        except Exception as e:
            print("questions not parsed")
            print(e)
            print(questions)

        return questions_list

    def __init__(self,*args,**kwargs):
        self.wait_at_open = 5
        self.scroll = ''


    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url,callback=self.parse)

    def parse(self, response):
        item = WebscrapingItem()

        item['title'] = response.xpath('//h1[@data-test="product-title"]//text()').get('')
        item['price'] = "".join(response.xpath('//span[@data-test="da-price--monthly-price"]/text()').getall())
        item['highlights'] = response.xpath('//div[@data-test="detailsTab"]//h3[contains(text(),"Highlights")]/following-sibling::ul/div/div//span/text()').getall()
        specs_html = response.xpath('//div[@data-test="detailsTab"]//h3[contains(text(),"Spec")]/following-sibling::div')
        print("number of specs: %d"%len(specs_html))
        specs_list = []
        for spec in specs_html:
            spec_dict = {}
            title = spec.xpath('.//b/text()').get('')
            if title:
                spec_dict[title] = spec.xpath('.//b/following-sibling::text()').get('')

            if spec_dict:
                specs_list.append(spec_dict)
        item["specs"] = specs_list
        item['description'] = ". ".join(response.xpath('//div[@data-test="item-details-description"]//text()').getall())

        product_id = response.url.split("A-")[1].split("?")[0] if response.url.split("A-")[1] else ""
        if not product_id:
            print("product_id not extracted. %s"%response.url)

        pattern = re.compile(r'"nova":{"apiKey":"(.*?)"')
        api_key = re.findall(pattern,response.text)
        print("api_key: %s"%api_key)
        print("product_id: %s"%product_id)
        if not (product_id and api_key):
            print("no productid or api key")
            item['questions'] = ""
        else:
            api_link = self.q_api_link%(product_id,api_key[0])
            print("sending request to %s"%api_link)
            questions_response = requests.get(api_link)
            questions_json = self.converter(questions_response.text,'json')
            item['questions'] = self.get_questions(questions_json)
            pagination = questions_json.get('total_pages')
            print("total number of pages: %s"%pagination)
            if pagination:
                page_num = self.converter(pagination,'int')
                if page_num:
                    for page in range(1,page_num):
                        next_api_link = api_link.replace("page=0","page=%d"%page)
                        more_questions_response = requests.get(next_api_link)
                        more_questions_json = self.converter(more_questions_response.text,'json')
                        if more_questions_json:
                            item['questions'] += self.get_questions(more_questions_json)


        item['images_url'] = response.xpath('//div[@data-test="carousel-stage-wrapper"]//a[@type="image"]//img/@src').getall()
        yield item
