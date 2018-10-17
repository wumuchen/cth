from pymongo import MongoClient
import requests
from lxml import etree


class VCspider():
	'''创投圈爬虫，单线程'''

	def __init__(self):
		self.url = 'https://www.vc.cn/startups?action=index&controller=startups&page={}&type=hot'
		self.headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6756.400 QQBrowser/10.3.2473.400Name'
		}
		# 初始化MongoDB连接
		self.collec = MongoClient().vc.vc

	def get_url(self):
		url_list = []
		# 创投圈共1892页，2018-10-17
		for i in range(1, 1893):
			url_list.append(self.url.format(i))
		return url_list

	def parse(self, url):
		print(url)
		response = requests.get(url, headers=self.headers)
		return response.content.decode()

	def get_data(self, html):
		content_list = []
		elem = etree.HTML(html)
		trs = elem.xpath('//table/tbody/tr')
		for tr in trs:
			item = {}
			item['img_url'] = tr.xpath('.//td[1]/div[@class="avatar"]/a[last()]/img/@src')[0]
			item['name'] = tr.xpath('.//td[1]/div[@class="info"]/div[@class="name"]/a/text()')[0]
			item['industry'] = tr.xpath('.//td[1]/div[@class="info"]/div[@class="name"]/span/a/text()')
			item['industry'] = item['industry'][0] if len(item['industry']) > 0 else None
			item['pstn'] = tr.xpath('.//td[1]/div[@class="info"]/div[@class="pstn"]/text()')[0]
			# item['taglist']=tr.xpath('.//td[@class="cover-info"]/div[@class="info"]/div[@class="taglist"]/span/text()')
			item['round'] = tr.xpath('.//td[2]/li/a/text()')[0]
			item['province'] = tr.xpath('.//td[3]//text()')[0]
			# print(item)
			content_list.append(item)
		return content_list

	def save_data(self, content_list):
		for item in content_list:
			if self.collec.update({'name': item['name']}, {'$set': item}, True):
				print('保存到MongoDB成功', item['name'])
			else:
				print('保存到MongoDB失败...', item['name'])

	def run(self):
		# 创建请求url列表
		url_list = self.get_url()
		# 循环列表请求
		for url in url_list:
			# 获取每页的数据
			html = self.parse(url)
			# 提取需要的数据
			content_list = self.get_data(html)
			# 保存到MongoDB
			self.save_data(content_list)


if __name__ == '__main__':
	vc = VCspider()
	vc.run()
