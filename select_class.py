from zhengfang_spider import ZhengFangSpider
import config

# 实例化爬虫并运行
spider = ZhengFangSpider(config.student_id, config.password, config.student_name, config.base_url, config.class_info)


# 获取选课列表
#spider.get_select_class()

# 选课
spider.select_class()
