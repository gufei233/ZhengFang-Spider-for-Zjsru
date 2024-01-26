# 监控成绩是否更新

import json
import os
import requests
import config
from zhengfang_spider import ZhengFangSpider


# 推送
def send_message(title, content):
    token = config.pushplus_token
    url = "http://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": title,
        "content": content
    }
    body = json.dumps(data).encode(encoding="utf-8")
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=body, headers=headers)
    return response.text

# 实例化爬虫
spider = ZhengFangSpider(config.student_id, config.password, config.student_name, config.base_url)

# 获取最新的学生成绩
spider.get_student_grades()
new_grades = spider.grades

# 检查本地是否有 grades.txt 文件
grades_file_path = 'grades.txt'
if not os.path.exists(grades_file_path):
    # 文件不存在，直接保存新成绩
    with open(grades_file_path, 'w', encoding='utf-8') as file:
        json.dump(new_grades, file, ensure_ascii=False)
        print("首次运行，已生成grades.txt")
else:
    # 文件存在，加载并对比成绩
    with open(grades_file_path, 'r', encoding='utf-8') as file:
        old_grades = json.load(file)
        print("对比成绩中")

    if new_grades != old_grades:
        # 成绩有更新，发送通知
        updated_grades = [grade for grade in new_grades if grade not in old_grades]
        update_content = json.dumps(updated_grades, ensure_ascii=False)
        send_message("成绩更新通知", update_content)
        print("有更新" + update_content)


        # 更新本地 grades.txt 文件
        with open(grades_file_path, 'w', encoding='utf-8') as file:
            json.dump(new_grades, file, ensure_ascii=False)
        print("已更新grades.txt")
    else:print("无更新")
