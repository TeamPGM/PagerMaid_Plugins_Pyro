自动转发频道新消息或者从零开始备份频道。

指令：,shift

## 使用方法

### 设置转发

当收到 from_channel_id 的新消息时，自动转发到 to_channel_id。

需要加入 from_channel_id 和 to_channel_id。

`, shift set [from channel_id] [to channel_id] (silent, all, none, all, photo, document, video)`

### 取消转发

`, shift del [from channel_id]`

### 备份频道

`, shift backup [from channel_id] [to channel_id] (silent)`

### 顯示要轉發的頻道

`, shift list`

## 选项解释

- `silent`: 禁用通知
- `all`: 全部都轉發(預設會有all)
- `none`: 轉發文字
- `photo`: 轉發圖片
- `document`: 轉發檔案
- `video`: 轉發影片
