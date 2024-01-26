# ZhengFang-Spider-for-Zjsru
# 浙江树人学院 正方教务系统工具

该Python脚本可用于获取教务系统个人信息和成绩，以及成绩更新监控和通知。

## 使用

1. 在 `config.py` 文件中配置您的个人信息，包括学号、密码和其他必要的信息。

2. 使用以下命令安装所需的依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 功能说明


### 1. 获取信息

-  `get_student_info` 可以登录教务系统并获取学生信息。`get_student_grades`可以获取成绩信息。

### 2. 计算GPA

-  `calculate_and_print_gpa` 可以计算学期和学年GPA。

### 3. 查看课表

-  `get_student_class` 脚本可以查看当前和过去的课表。

### 4. 成绩监控

- 通过定时运行 `gradeMonitor.py` 脚本，您可以监控成绩更新，当成绩有变化时，会发送通知提醒您。

### 5. 选课
- `select_class.py`脚本可查看可选课列表以及提交选修课。具体内容可查看注释。


#### PushPlus通知配置

- 如果您需要通过PushPlus发送成绩更新的通知，可以按照以下步骤配置PushPlus Token：

   - 登录 [PushPlus](https://www.pushplus.plus/)
   - 在 [Token页面](https://www.pushplus.plus/api/open/user/token) 复制您的Token。

### 注意事项

- 由于验证码有概率识别错误，您可以通过修改`zhengfang_spider.py`中的`max_login_attempts`来自定义尝试重新登录次数。

- 如果您的教务系统登录页面包含验证码，且验证码的图片链接为 `xxxxxx/CheckCode.aspx?SafeKey=97198bdf1f2143059f3ccf570c7c10b1`，则大概率可以使用此工具。

## 许可证

这个工具基于 MIT 许可证进行分发。有关详细信息，请参阅 [LICENSE](https://github.com/gufei233/ZhengFang-Spider-for-Zjsru/blob/main/LICENSE) 文件。
