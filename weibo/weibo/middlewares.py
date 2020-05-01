# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import requests
import logging

class ProxyMiddleware:

	def __init__(self, proxy_url):
		self.logger = logging.getLogger(__name__)
		self.proxy_url = proxy_url

	def get_proxy(self):
		try:
			r = requests.get(self.proxy_url)
			if r.status_code == 200:
				proxy = r.text
				proxy = 'http://{proxy}'.format(proxy=proxy)
				return proxy
		except requests.ConnectionError:
			return False
	
	def process_request(self, request, spider):
		if request.meta.get('retry_times'):
			proxy = self.get_proxy()
			if proxy:
				self.logger.debug('使用代理' + proxy)
				request.meta['proxy'] = proxy
		
	@classmethod
	def from_crawler(cls, crawler):
		settings = crawler.settings
		return cls(
			proxy_url = settings.get('PROXY_URL')
		)