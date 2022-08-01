# PMCaptcha 代码维护指南

由于插件行数过多，为确保后续维护方便，本核心开发者 (Sam) 将在这里说明插件的基本架构。

# class (类)

## 通用

- Log: 日志类 | 负责发送验证记录
- Setting: 设置类 | 负责读写每个设置
- Command: 指令类 | 负责用户的指令处理
- Rule: 规则类 | 负责运行每个规则来判断该如何处理该

## Captcha 验证

- TheOrder: _别名封禁系统_ | 负责进行用户的封禁操作
- TheWorldEye： _别名防轰炸系统_ | 负责监控、启用和关闭防轰炸
- CaptchaTask: 负责添加用户进行Captcha验证，以及抢先一步屏蔽用户避免收到骚扰
- CaptchaChallenge: 验证系统的主类
  - MathChallenge: 计算验证
  - ImageChallenge: 图片验证
  - StickerChallenge: 贴纸验证

# listener (监听器)

- image_captcha_listener: 监听被验证用户的图像验证结果
- initiative_listener: 监听用户是否主动对话 (以此添加白名单)
- chat_listener: 监听被验证用户输入的验证结果 (文字)
- cmd_entry: 监听用户输入的指令

# functions (函数)

> 这里只记下比较有意义的函数

- resume_states： 恢复用户的验证状态
- lang, lang_full, get_lang_list: 多语言 (i18n)
- get_version: 获取 PMCaptcha 的版本号
- log: 发送 log 记录 (由于原版的函数不好用所以写了个新的)
