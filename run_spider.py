# 获取信息 获取成绩 计算gpa
from zhengfang_spider import ZhengFangSpider
import config

def pretty_print_student_info(student_info):
    print("学生信息:")
    for key, value in student_info.items():
        print(f"{key}: {value}")

def pretty_print_student_grades(grades):
    print("学生成绩:")
    for grade in grades:
        print(f"年度: {grade['year']}, 学期: {grade['term']}, 课程名称: {grade['name']}, 课程类型: {grade['type']}, 学分: {grade['credit']}, 绩点: {grade['gradePoint'].strip()}, 成绩: {grade['grade']}")

# 实例化爬虫并运行
spider = ZhengFangSpider(config.student_id, config.password, config.student_name, config.base_url, config.class_info)

# 获取学生信息 若不需要则注释下行代码
spider.get_student_info()

# 获取学生成绩 若不需要则注释下行代码
spider.get_student_grades()

# 优化打印信息
pretty_print_student_info(spider.student_info)  # 美观打印学生信息 若不需要则注释
pretty_print_student_grades(spider.grades)     # 美观打印学生成绩 若不需要则注释

# 计算gpa并打印 若不需要则注释下行代码
spider.calculate_and_print_gpa()

# 课表
#spider.get_student_class()
