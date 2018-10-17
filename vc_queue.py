from pymongo import MongoClient
import requests
from lxml import etree
import threading
from queue import Queue


class VCspider():
	'''创投圈爬虫,多线程'''

	def __init__(self):
		self.url = 'https://www.vc.cn/startups?action=index&controller=startups&page={}&type=hot'
		self.headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6756.400 QQBrowser/10.3.2473.400Name'
		}
		# 初始化MongoDB连接
		self.collec = MongoClient().vc.vc_queue
		self.url_queue = Queue()
		self.html_queue = Queue()
		self.content_queue = Queue()

	def get_url(self):
		# 创投圈共1892页，2018-10-17
		for i in range(1, 1893):
			self.url_queue.put(self.url.format(i))

	def parse(self):
		while True:
			url = self.url_queue.get()
			print(url)
			response = requests.get(url, headers=self.headers)
			self.html_queue.put(response.content.decode())
			self.url_queue.task_done()

	def get_data(self):
		while True:
			html = self.html_queue.get()
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
			self.content_queue.put(content_list)
			self.html_queue.task_done()

	def save_data(self):
		while True:
			content_list = self.content_queue.get()
			for item in content_list:
				if self.collec.update({'name': item['name']}, {'$set': item}, True):
					print('保存到MongoDB成功', item['name'])
				else:
					print('保存到MongoDB失败...', item['name'])
			self.content_queue.task_done()

	def run(self):
		thread_list = []
		# 创建请求url列表
		t_url = threading.Thread(target=self.get_url)
		thread_list.append(t_url)
		# 遍历请求
		for i in range(20):
			t_parse = threading.Thread(target=self.parse)
			thread_list.append(t_parse)
		# 提取数据
		for i in range(20):
			t_html = threading.Thread(target=self.get_data)
			thread_list.append(t_html)
		# 保存数据
		t_save = threading.Thread(target=self.save_data)
		thread_list.append(t_save)

		for t in thread_list:
			t.setDaemon(True)  # 把子线程设置为守护线程，该线程不重要主线程结束，子线程结束
			t.start()

		for q in [self.url_queue, self.html_queue, self.content_queue]:
			q.join()  # 让主线程等待阻塞，等待队列的任务完成之后再完成

		print('主线程结束')


if __name__ == '__main__':
	vc = VCspider()
	vc.run()
# 发送请求过多会报错误状态码429，ip被封，可以换ip，以及增加请求时间间隔
