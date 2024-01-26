# 登录 获取原始数据
import requests
import os
import re
import time
import ddddocr
import urllib.parse
import config
from lxml import etree
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from binascii import a2b_hex, b2a_hex
from Crypto.Util.number import bytes_to_long
from info_parser import parse_student_info, parse_grades, calculate_gpa, get_viewstate_values, parse_class_schedule, , parse_select_class

class ZhengFangSpider:
    def __init__(self, student_id, password, student_name, base_url, class_info):
        self.grades = []
        self.is_logged_in = False
        self.grades_fetched = False
        self.student_id = student_id
        self.password = password
        self.student_name = student_name
        self.base_url = base_url
        self.class_info = class_info
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'

    #rsa加密密码部分
    @staticmethod
    def encrypt_with_modulus(content, public_exponent, modulus=None):
        e = int(public_exponent, 16)  # 指数
        n = bytes_to_long(a2b_hex(modulus))
        rsa_key = RSA.construct((n, e))  # generate/export
        # public key
        public_key = rsa_key.publickey()
        cipher = PKCS1_v1_5.new(public_key)
        content = cipher.encrypt(content)
        content = b2a_hex(content)
        return str(content)
        pass

    # 含验证码登陆部分
    def login(self):
        loginurl = self.base_url + "/default2.aspx"
        max_login_attempts = 3  # 设置最大登录尝试次数
        login_attempts = 0


        while login_attempts < max_login_attempts:
            response = self.session.get(loginurl)
            selector = etree.HTML(response.content)

            # 获取验证码的参数
            safe_key = selector.xpath('//*[@id="icode"]/@src')[0].split('=')[1]
            # 获取公钥参数
            txtKeyExponent = selector.xpath('//*[@id="txtKeyExponent"]/@value')[0]
            txtKeyModulus = selector.xpath('//*[@id="txtKeyModulus"]/@value')[0]
            # 加密密码
            encrypted_password = ZhengFangSpider.encrypt_with_modulus(
                self.password.encode('utf-8'),  # 将密码转换为字节
                txtKeyExponent,
                txtKeyModulus
            )
            cleaned_result = encrypted_password.replace("b'", "").rstrip("'")
            __VIEWSTATE = selector.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
            __VIEWSTATEGENERATOR = selector.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0]
        
            imgUrl = self.base_url + "/CheckCode.aspx?SafeKey=" + safe_key
            imgresponse = self.session.get(imgUrl, stream=True)
            image = imgresponse.content

            # 使用 ddddocr 来识别验证码
            ocr = ddddocr.DdddOcr()
            code = ocr.classification(image)
            print("识别验证码：" + code)
            RadioButtonList1 = u"学生".encode('gb2312', 'replace')
            data = {
                "__LASTFOCUS": "",
                "__VIEWSTATE": __VIEWSTATE,
                "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "txtUserName": self.student_id,
                "TextBox2": cleaned_result,
                "txtSecretCode": code,
                "RadioButtonList1": "学生",
                "Button1": "登录",
                "txtKeyExponent" : "010001",
                "txtKeyModulus": txtKeyModulus
            }
            # 登陆教务系统
            login_response = self.session.post(loginurl, data=data, allow_redirects=False)
            if login_response.status_code == 302:
                self.is_logged_in = True
                print("登录成功\n")
                return True
            else:
                print("登录失败，尝试重新登录\n")
                self.is_logged_in = False
                login_attempts += 1

        print("重试登录次数达到上限，登录失败\n")
        return False
        pass


    # 获取学生信息部分
    def get_student_info(self):
        if not self.is_logged_in:
            if not self.login():
                print("登录失败，无法获取学生信息")
                return
        
        # 设置请求头
        info_url = f"{self.base_url}/xsgrxx.aspx?xh={self.student_id}&xm={urllib.parse.quote(self.student_name)}&gnmkdm=N121501"

        # 定义请求头
        headers = {
            "Host": "xk.jwc.zjsru.edu.cn",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": f"{self.base_url}/xs_main.aspx?xh={self.student_id}",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        }

        # 发送GET请求时传入headers参数
        response = self.session.get(info_url, headers=headers)
        if response.status_code == requests.codes.ok:
            student_info = parse_student_info(response.text)
            self.student_info = student_info
        else:
            print("获取信息失败")
        pass


    # 获取学生成绩部分
    def get_student_grades(self):
        if not self.is_logged_in:
            if not self.login():
                print("登录失败，无法获取学生信息")
                return
        
        url = f"{self.base_url}/xscjcx.aspx?xh={self.student_id}&xm={urllib.parse.quote(self.student_name)}&gnmkdm=N121605"
        self.session.headers['Referer'] = self.base_url + "/xs_main.aspx?xh=" + self.student_id
        response = self.session.get(url)
        selector = etree.HTML(response.content)
        __VIEWSTATE = selector.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
        __VIEWSTATEGENERATOR = selector.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0]

        # 提交获取成绩的POST请求
        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": __VIEWSTATE,
            "__VIEWSTATEGENERATOR" : __VIEWSTATEGENERATOR,
            "ddlXN": "",  # 可根据需要设置学年
            "ddlXQ": "",  # 可根据需要设置学期
            "ddl_kcxz": "",  # 可根据需要设置课程性质
            "btn_zcj": "历年成绩"
        }
        response = self.session.post(url, data=data, headers={"Referer": url})
        if response.status_code == requests.codes.ok:
            grades = parse_grades(response.text)
            self.grades = grades
            self.grades_fetched = True  # 成功获取成绩后，设置标志为 True
        else:
            print("获取学生成绩失败")




    def calculate_and_print_gpa(self):
        # 检查是否已获取成绩
        if not self.grades_fetched:
            print("还未获取成绩，正在尝试获取...")
            self.get_student_grades()
            if not self.grades_fetched:
                print("无法获取成绩，无法计算 GPA")
                return

        # 调用 calculate_gpa 函数计算 GPA
        term_gpa, year_gpa = calculate_gpa(self.grades)

        # 打印学期 GPA
        print("学期 GPA:")
        for term, data in term_gpa.items():
            print(f"{term} - GPA: {data['gpa']:.2f}, 总学分: {data['total_credits']}, 总绩点: {data['total_points']:.2f}")

        # 打印学年 GPA
        print("\n学年 GPA:")
        for year, data in year_gpa.items():
            print(f"{year} - GPA: {data['gpa']:.2f}, 总学分: {data['total_credits']}, 总绩点: {data['total_points']:.2f}")

    # 课表
    def get_student_class(self):
        if not self.is_logged_in:
            if not self.login():
                print("登录失败，无法获取学生课表\n")
                return
        
        # 设置请求头
        class_url = f"{self.base_url}/xskb.aspx?xh={self.student_id}&xhxx={self.class_info}"

        # 定义请求头
        headers = {
            "Host": "xk.jwc.zjsru.edu.cn",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": f"{self.base_url}/xs_main.aspx?xh={self.student_id}",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        }

        # 发送GET请求时传入headers参数
        response = self.session.get(class_url, headers=headers)
        if response.status_code == requests.codes.ok:
            student_class = parse_class_schedule(response.text)
            self.student_class = student_class
            print("\n课表：\n" + self.student_class)
        else:
            print("获取课表失败\n")
        pass


    # 获取选课列表
    def get_select_class(self):
        if not self.is_logged_in:
            if not self.login():
                print("登录失败，无法获取选课列表\n")
                return

        # 进入选课界面
        url = f"{self.base_url}/xf_xsqxxxk.aspx?xh={self.student_id}&xm={urllib.parse.quote(self.student_name)}&gnmkdm=N121104"
        headers = {
            "Host": "xk.jwc.zjsru.edu.cn",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": f"{self.base_url}/xs_main.aspx?xh={self.student_id}",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        }
        response = self.session.get(url,headers=headers)
        selector = etree.HTML(response.content)
        __VIEWSTATE = selector.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
        __VIEWSTATEGENERATOR = selector.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0]        

        headers = {
            "Host": "xk.jwc.zjsru.edu.cn",
            "Proxy-Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Origin": "http://xk.jwc.zjsru.edu.cn",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": f"{self.base_url}/xf_xsqxxxk.aspx?xh={self.student_id}&xm={urllib.parse.quote(self.student_name)}&gnmkdm=N121104",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        }


        
        data = {
            "__EVENTTARGET": "dpkcmcGrid$txtPageSize",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": __VIEWSTATE,
            "__VIEWSTATEGENERATOR" : __VIEWSTATEGENERATOR,
            "ddl_kcxz": "", # 课程性质
            "ddl_ywyl": "有", # 有无余量
            "ddl_kcgs": "", # 课程归属
            "ddl_xqbs": "1",
            "ddl_sksj": "",
            "TextBox1": "",
            "dpkcmcGrid$txtChoosePage": "1", # 第一页
            "dpkcmcGrid$txtPageSize": "100", # 一页显示100个，为保证在一页显示，该数字需要大于总可选课程数
        }

        # 发送POST请求传入参数
        time.sleep(5) # 跳过三秒防刷
        response = self.session.post(url,headers=headers,data=data)
        if response.status_code == requests.codes.ok:
            select_class =parse_select_class(response.text)
            self.select_class = select_class
            print(self.select_class)
        else:
            print("获取选课列表失败\n")
        pass


    # 选课
    # 懒得改了 CTRL V
    def select_class(self):
        if not self.is_logged_in:
            if not self.login():
                print("登录失败，无法获取选课列表\n")
                return

        # 进入选课
        url = f"{self.base_url}/xf_xsqxxxk.aspx?xh={self.student_id}&xm={urllib.parse.quote(self.student_name)}&gnmkdm=N121104"
        headers = {
            "Host": "xk.jwc.zjsru.edu.cn",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": f"{self.base_url}/xs_main.aspx?xh={self.student_id}",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        }
        response = self.session.get(url,headers=headers)
        if response.status_code == requests.codes.ok:
            selector = etree.HTML(response.content)
            __VIEWSTATE = selector.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
            __VIEWSTATEGENERATOR = selector.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0]
            print("获取选课配置成功")
        else:print("获取选课配置失败")


        # 获取全部可选课程
        headers = {
            "Host": "xk.jwc.zjsru.edu.cn",
            "Proxy-Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Origin": "http://xk.jwc.zjsru.edu.cn",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": f"{self.base_url}/xf_xsqxxxk.aspx?xh={self.student_id}&xm={urllib.parse.quote(self.student_name)}&gnmkdm=N121104",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        }


        
        data = {
            "__EVENTTARGET": "dpkcmcGrid$txtPageSize",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": __VIEWSTATE,
            "__VIEWSTATEGENERATOR" : __VIEWSTATEGENERATOR,
            "ddl_kcxz": "", # 课程性质
            "ddl_ywyl": "有", # 有无余量
            "ddl_kcgs": "", # 课程归属
            "ddl_xqbs": "1",
            "ddl_sksj": "",
            "TextBox1": "",
            "dpkcmcGrid$txtChoosePage": "1", # 第一页
            "dpkcmcGrid$txtPageSize": "100", # 一页显示100个，为保证在一页显示，该数字需要大于总可选课程数
        }

        print("等待四秒")
        time.sleep(4) # 跳过三秒防刷
        response = self.session.post(url,headers=headers,data=data)
        if response.status_code == requests.codes.ok:
            selector = etree.HTML(response.content)
            __VIEWSTATE = selector.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
            __VIEWSTATEGENERATOR = selector.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0] 
            print("已进入选课界面")
        else:
            print("获取选课列表失败\n")


        # 构建提交选课请求、
        selected_courses = config.selected.split(',') # 获取要选几门课

        num = len(selected_courses)
        num_selected = 0

        print("从配置文件中检测到要选" + str(num) + "门课")
        # for循环来多次提交选课
        for course_index in selected_courses:
            checkbox_name = f"kcmcGrid$ctl{int(course_index)+1:02d}$xk"

            data = {
                "__EVENTTARGET": "dpkcmcGrid$txtPageSize",
                "__EVENTARGUMENT": "",
                "__LASTFOCUS": "",
                "__VIEWSTATE": __VIEWSTATE,
                "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
                "ddl_kcxz": "",
                "ddl_ywyl": "有",
                "ddl_kcgs": "",
                "ddl_xqbs": "1",
                "ddl_sksj": "",
                "TextBox1": "",
                checkbox_name: "on",
                "dpkcmcGrid$txtChoosePage": "1",
                "dpkcmcGrid$txtPageSize": "100",
                "Button1": " 立即提交 "
            }

            retry_count = 3 # 失败重试次数
            network_retry_count = 2  # 网络拥堵时的重试次数
            course_processed = False  # 标志当前课程是否已处理
            network_error = False  # 网络拥堵重试上限标志
            

            while retry_count > 0 and not course_processed and not network_error:

                retry = 0 

                while retry < 3: # 每门课重复提交几次
                    print("等待四秒后开始选课" + str(retry + 1) + "次选课尝试")
                    time.sleep(4)
                    response = self.session.post(url, headers=headers, data=data)
                    retry += 1

                    if retry == 3:  # 在第几次请求后检查网络和选课结果

                        if response.status_code != requests.codes.ok:
                            print(f"网络拥堵，正在重试...（剩余{network_retry_count}次）")
                            network_retry_count -= 1
                            if network_retry_count == 0:
                                print(f"网络拥堵重试次数用完，跳过 {checkbox_name} 的选课。")
                                network_error = True  # 设置网络错误标志
                                break
                            else:
                                break
                        
                        
                        
                        
                        selector = etree.HTML(response.content)
                        alert_pattern = re.compile(r"<script language='javascript'>alert\('(.+?)'\);</script>")
                        match = alert_pattern.search(response.text)

                        if match:
                            selector = etree.HTML(response.content)
                            __VIEWSTATE = selector.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
                            __VIEWSTATEGENERATOR = selector.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0]
                            num_selected += 1
                            print("第" + str(num_selected) + "门选课提交结果：" + match.group(1))
                            course_processed = True  # 标记当前课程已处理
                            break
                        else:
                            print(f"尝试选课 {checkbox_name} 失败, 正在重新提交...")
                            retry_count -= 1
                            break




