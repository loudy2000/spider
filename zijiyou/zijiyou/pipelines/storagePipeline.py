# -*- coding: utf-8 -*-
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html
from scrapy import log
from zijiyou.db.mongoDbApt import MongoDbApt
import re
from scrapy.exceptions import NotConfigured

class StoragePipeline(object):
#    specialDb = ["ImageDb"]
    
    def __init__(self):
        self.mongoApt=MongoDbApt()
        #self.fileApt = open("zijiyou/pipelines/test.txt","w+")
    
    def process_item(self, item, spider):
        if not item['collectionName']:
            log.msg("Item的collectionName空！请检查zijiyouItem中是否有未定义collectionName的Item！", level=log.ERROR)
            raise NotConfigured
        self.saveItem2Mongodb(item, item['collectionName'])
        
    def saveItem2File(self,item, collectionName = None):
        values = collectionName + '\n'
        value = ''
        for k,v in item.items():
            try:
                '''if v is not a dic or list will throw exception'''
                value = k+"："+("-".join("%s" % p for p in v))
                value = re.sub("[\r\n]", "", value)+"\n"
            except Exception:
                value = k+"：" + "-" + "%s" % v
            values += value
        self.fileApt.write(values+"\n")
        
    def saveItem2Mongodb(self,item, collectionName):
        values = {}
        for k,v in item.items():
            values[k] = v
        obj = self.mongoApt.saveItem(collectionName, values)
        print '++++saveItem2Mongodb++++col:%s,objectId:%s' % (collectionName ,obj)
        log.msg('++++saveItem2Mongodb++++col:%s,objectId:%s+++++++++++' % (collectionName ,obj), level = log.INFO)
        
    