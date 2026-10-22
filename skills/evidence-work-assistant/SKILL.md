---
name: evidence-work-assistant
description: Collect authorized local WeChat, Feishu and Apple Mail evidence into attributable work items, with pagination coverage, deduplication and explicit uncertainty.
---
# 聊天工作事项助手

先读 [读取方法](references/collection-methods.md)，运行 `python3 scripts/chat_work_items.py doctor`。默认最近7天，北京时间。原始数据写入用户本地数据目录，保持在Git与云同步目录之外。没有登录或读权限时明确报告缺口。

按指定窗口先采集再判断：微信枚举会话并分页读取，飞书使用用户身份和空关键词时间检索，邮件先收信、标题筛选后读相关正文。记录真实覆盖范围，关键词命中不能当作完整历史读取。

读取上下文、后续回复、取消、改期和完成。只把明确归属于用户的承诺列为个人事项；不把群通知、建议或他人任务自动分配给用户。未知负责人/时间保留空值。完成提醒不等于工作已办结。

先导出 `context` 数据，由模型解释，再写任务JSON供 `render-tasks` 检查证据；脚本本身不理解自然语言。稳定语义去重与消息去重分别处理。日历必须有确定参与安排及开始结束时间，否则留待核。

输出任务、证据ID、状态变化、覆盖限制及报告路径。网页看板仅接收用户手动导入的任务JSON，不直接连接账户或上传聊天。外部提醒、日历、发送消息及后台定时需用户明确要求；安装不自动启用定时任务。
