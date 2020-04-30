# -*- coding: utf-8 -*-

import json
from scrapy import Request, Spider
from weibo.items import *


class WeibocnSpider(Spider):
    name = 'weibocn'
    allowed_domains = ['m.weibo.cn']
    user_url = 'https://m.weibo.cn/profile/info?uid={uid}'    #用户详情API
    follow_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_follow_-_{uid}&page={page}'   #关注列表API
    fan_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{uid}&since_id={since_id}'    #粉丝列表API
    weibo_url = 'https://m.weibo.cn/api/container/getIndex?containerid=230413{uid}_-_WEIBO_SECOND_PROFILE_WEIBO&page_type=03&page={page}' #微博列表API
    start_users = ['2032139271','1699432410','1642512402','2258727970','1265998927'] #用户ID

    def start_requests(self):
        for uid in self.start_users:
            yield Request(self.user_url.format(uid=uid),callback=self.parse_user)


    def parse_user(self, response):
        """
        解析用户信息
        :param response: Response对象
        """
        self.logger.debug(response)
        result = json.loads(response.text)
        if result.get('data').get('user'):
            user_info = result.get('data').get('user')
            user_item = UserItem()
            field_map = {
                    'id': 'id', 'name': 'screen_name', 'avatar': 'profile_image_url', 'cover': 'cover_image_phone',
                'gender': 'gender', 'description': 'description', 'fans_count': 'followers_count',
                'follows_count': 'follow_count', 'weibos_count': 'statuses_count', 'verified': 'verified',
                'verified_reason': 'verified_reason', 'verified_type': 'verified_type'
                    }
            for field,attr in field_map.items():
                user_item[field] = user_info.get(attr)
            yield user_item
            
            #关注API调用
            uid = user_info.get('id')
            yield Request(self.follow_url.format(uid=uid, page=1),callback=self.parse_follows,meta={'uid':uid,'page':1})

            #粉丝API调用
            yield Request(self.fan_url.format(uid=uid, since_id=1),callback=self.parse_fans,meta={'uid':uid,'since_id':1})

            #微博列表API调用
            yield Request(self.weibo_url.format(uid=uid, page=1),callback=self.parse_weibos,meta={'uid':uid,'page':1})


    def parse_follows(self,response):
        """"
        解析用户关注
        :param response: Response对象
        """
        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('cards') and result.get('data').get('cards')[-1].get('card_group'):
            #解析用户
            follows = result.get('data').get('cards')[-1].get('card_group')
            for follow in follows:
                if follow.get('user'):
                    #获取关注的用户UID
                    uid = follow.get('user').get('id')
                    yield Request(self.user_url.format(uid=uid),callback=self.parse_user)  #获取关注用户详情信息
                
            uid = response.meta.get('uid')
                #关注列表
            user_relation_item = UserRelationItem()
            follows = [{'id':follow.get('user').get('id'),'user_name':follow.get('user').get('screen_name')} for follow in follows]
            user_relation_item['id'] = uid
            user_relation_item['follows'] = follows
            user_relation_item['fans'] = []
            yield user_relation_item

            #下一页关注
            page = response.meta.get('page')+1
            yield Request(self.follow_url.format(uid=uid,page=page),callback=self.parse_follows,meta={'uid':uid,'page':page})

    def parse_fans(self,response):
        """
        解析用户粉丝
        :param response: Response对象
        """

        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('cards') and result.get('data').get('crads')[-1].get('card_group'):
            #解析用户
            fans = result.get('data').get('cards')[-1].get('group_crad')
            for fan in fans:
                if fan.get('user'):
                    #获取粉丝的用户ID
                    uid = fan.get('user').get('id')
                    yield Request(self.user_url.format(uid=uid),callback=self.pase_user) #获取粉丝用户详情信息
            
            uid = response.meta.get('uid')
            #粉丝列表
            fans = [{'id':fan.get('user').get('id'),'user_name':fan.get('user').get('screen_name')} for fan in fans]
            user_relation_item = UserRelationItem()
            user_relation_item['id'] = uid
            user_relation_item['fans'] = fans
            user_relation_item['follows'] = []
            yield user_relation_item

            #下一页粉丝
            since_id = response.meta.get('since_id')+1
            yield Request(self.fan_url.format(uid=uid,since_id=since_id),callback=self.parse_fans,meta={'uid':uid,'since_id':since_id})

    def parse_weibos(self, response):
        """
        解析用户微博
        :param response: Response对象
        """

        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('cards'):
            weibos = result.get('data').get('cards')
            for weibo in weibos:
                #获取微博信息
                mblog = weibo.get('mblog')
                if mblog:
                    weibo_item = WeiboItem()
                    field_map = {
                            'id': 'id', 'attitudes_count': 'attitudes_count', 'comments_count': 'comments_count',
                        'reposts_count': 'reposts_count', 'picture': 'original_pic', 'pictures': 'pics',
                        'created_at': 'created_at', 'source': 'source', 'text': 'text', 'raw_text': 'obj_ext',
                        'thumbnail': 'thumbnail_pic',
                            }
                    for field,attr in field_map.items():
                        weibo_item[field] = mblog.get(attr)
                    weibo_item['user'] = response.meta.get('uid')
                    yield weibo_item

            
            #下一页微博
            page = response.meta.get('page')+1
            uid = response.meta.get('uid')
            yield Request(self.weibo_url.format(uid=uid,page=page),callback=self.parse_weibos,meta={'uid':uid,'page':page})
