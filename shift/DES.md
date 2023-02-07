自动转发频道新消息或者从零开始备份频道。

指令：,shift

# 设置转发

当收到 from_channel_id 的新消息时，自动转发到 to_channel_id。

需要加入 from_channel_id 和 to_channel_id。

`, shift set [from channel_id] [to channel_id]`

# 取消转发

`, shift del [from channel_id]`

# 备份频道

`, shift backup [from channel_id] [to channel_id]`