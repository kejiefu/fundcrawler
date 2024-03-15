import scrapy

'''
scrapy runspider quotes_spider.py -o quotes.jl
该命令是使用Scrapy运行一个名为"quotes_spider.py"的爬虫，并将结果保存为一个名为"quotes.jl"的JSON Lines文件。

scrapy runspider：Scrapy的命令行工具，用于运行爬虫。
quotes_spider.py：爬虫的文件名或路径。在这个例子中，假设爬虫的代码保存在名为"quotes_spider.py"的文件中。
-o quotes.jl：选项 -o 用于指定输出文件的名称和格式。在这个例子中，quotes.jl 表示输出文件的名称为 "quotes.jl"，并使用 JSON Lines 格式进行存储。
JSON Lines (jl) 是一种存储每行为一个独立 JSON 对象的文件格式，常用于存储结构化数据。通过使用该命令，您可以运行Scrapy爬虫并将结果保存到指定的文件中，以便进一步处理和分析。
'''

# 定义一个名为QuotesSpider的爬虫类
class QuotesSpider(scrapy.Spider):
    # 设置爬虫的名称
    name = 'quotes'

    # 设置爬虫的起始URL
    start_urls = [
        'http://quotes.toscrape.com/tag/humor/',
    ]

    # 定义解析方法，用于处理响应数据
    def parse(self, response):
        # 使用CSS选择器提取每个名为quote的div元素
        for quote in response.css('div.quote'):
            yield {
                'author': quote.xpath('span/small/text()').get(),
                'text': quote.css('span.text::text').get(),
            }

        # 提取下一页的URL，并继续调用parse方法解析下一页
        next_page = response.css('li.next a::attr("href")').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)