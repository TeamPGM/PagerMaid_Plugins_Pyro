# Trace

### 用法

```
  Reply to a message:
    Trace      : .trace 👍👎🥰
    Untrace    : .trace
  Trace keyword: .trace kw add 👍👎🥰
  Del keyword  : .trace kw del

  List all   : .trace status
  Untrace all: .trace clean
  Keep log   : .trace log [true|false]
```

#### 踩的坑

+ 对于一些emoji的字符长度为1，在SPECIAL_EMOJI中定义，不知道有没有写完，欢迎添加。

#### 接下来可能加的东西（更有可能摆）

+ 在某一段时间内随机react
+ 优先级（keyword和user）
+ 通过id/username添加
+ 安全词（对方说了就停）
+ 历史记录react
+ big/sleep长度参数的设置
+ 定时器
+ 还有什么好玩的么？