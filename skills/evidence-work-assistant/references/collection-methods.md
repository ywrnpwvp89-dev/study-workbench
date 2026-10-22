# 采集与读取方法：可复现说明

## 边界与数据位置

本包提供只读采集器与方法文档；不附聊天数据库、真实消息、登录凭据、解密材料、私人排除名单或定时服务。默认本地目录 `~/.local/share/chat-work-items/`；可用 `CHAT_WORK_ITEMS_HOME` 指定另一个本地目录。不要设在Git或iCloud下。文件创建使用私有权限；共享前检查报告内容。

采集器仅兼容已验证的CLI结果结构，后端升级需要重新验证。doctor通过只证明工具/认证检查通过，不能证明当天消息已读。

## 微信：本地授权数据源

依赖 GreenBubbles（历史验证版本0.10.0）。先按工具自己的安装/授权文档建立有权访问的本机数据源，然后运行 `greenbubbles source status --profile YOUR_PROFILE`。数据源必须对应本人日常账号的原始容器，独立克隆账号的数据不能当作日常历史。不要通过更换bundle ID假设密钥或历史可复用。

执行：

```sh
python3 scripts/chat_work_items.py collect-wechat --profile YOUR_PROFILE --account local-owner --days 7
```

内部读取顺序：先 `source status`，再 `chats --limit 500` 跟随会话cursor；对每个未排除会话调用 `messages list --json --conversation ID --limit 500 --since UNIX --until UNIX`，跟随消息cursor，保存每页及coverage.json。必须检查会话遗漏、数据库分片warning、分页上限、附件占位和撤回消息。

本地 `wechat-summary-exclusions.json` 可以排除指定会话；示例结构与版本见采集器 `load_wechat_exclusions`。名单仅本地保存。不要将排除内容导入摘要，即使旧数据库已有消息。

### 本机历史初始化经验与限制

此前本机验证表明，修改正式微信签名可能导致启动失败；独立克隆使用不同容器与密钥，也无法代表原日常数据库。一次性实验在用户授权和登录下使用临时程序副本、匹配原容器、校验数据库salt与密钥对应关系，最后恢复正式程序。该经验依赖特定应用版本，不能视为跨版本安装流程。

公开包不包含临时调试/捕获密钥脚本，不自动修改应用签名、系统安全设置或重新采集密钥。已有可验证的本地凭据应复用，不输出到终端、模型或报告；密钥失效则停下重新评估，必要时退回用户导出或原生界面读取。

## 飞书：官方CLI用户身份

依赖官方 `lark-cli`，默认路径 `~/.local/bin/lark-cli`。完成自己的用户授权，仅申请读取/搜索消息所需权限；每个租户单独核对，不能用机器人身份冒充个人历史。

```sh
python3 scripts/chat_work_items.py collect-feishu --days 7
```

内部调用 `lark-cli im +messages-search --as user --query '' --start START --end END --page-size 50 --format json --no-reactions`，逐页跟随page_token。持续使用同一开始和结束时间，避免分页期间滚动窗口变化。中断续读使用保存的cursor和原始边界：

```sh
python3 scripts/chat_work_items.py collect-feishu --start START --end END --cursor CURSOR
```

只有搜索结果完整遍历可标为complete_search_results；服务端可见范围、租户限制、附件和已撤回消息仍是覆盖限制。不得解释为“读取全平台全部聊天”。

## Apple Mail：先收信再筛选

macOS自带Mail，本人已配置账户，并授予终端对Mail自动化访问权限。读取器先启动Mail，向全部账户请求收新邮件并等20秒，再列标题。等待不证明全部账户同步完成。

```sh
python3 scripts/read_apple_mail.py list --days 7
python3 scripts/read_apple_mail.py read --selector ACCOUNT:MAILBOX:MESSAGE_ID
```

只读取工作相关正文；不发送、不移动、不删除、不主动标记已读。跳过草稿、废纸篓、垃圾邮件；不解码附件。选择器由本次list结果取得，不能沿用未知旧编号。离线、登录失败、权限不足要写入报告。

## 原生界面回退

使用受支持的Computer Use工具打开指定应用，先核实账号与聊天标题。按会话逐页向前读取，页面间保留重叠，直到时间窗口边界。AX不足时读取截图；不能从侧边预览推断完整聊天，也不能把白屏当无消息。输入搜索前确认焦点不是消息发送框。

保存观察文本、页面/截图定位与字面时间。日期不确定用 `at:null` 和 `time_label`。使用 `import-ui` 导入；没有原生消息ID时生成派生ID，不能伪造。

## 从证据到事项

```sh
python3 scripts/chat_work_items.py context --days 7 --output LOCAL_PATH/context.json
python3 scripts/chat_work_items.py render-tasks LOCAL_PATH/items.json --output LOCAL_PATH/report.md
```

模型须读完输出分块及相关后续回复，任务格式含 `title, owner, due, status, evidence_ids, rationale`。状态为pending/in_progress/done/cancelled/needs_confirmation。render-tasks拒绝不存在或已撤回的证据；该校验不证明语言解释正确。

区分消息原生ID去重、同文不同时间消息、跨来源同事项语义去重。改期与取消需要记录证据链。最终报告列出实际时间窗口、会话/页数、排除数、分页缺口、未读附件、失败来源；不能只报告总条数。

定时采集和外部写入是另外的功能：使用者需明确配置调度器、目的账户、去重策略和权限。本包默认不创建日历、提醒或自动发送摘要。
