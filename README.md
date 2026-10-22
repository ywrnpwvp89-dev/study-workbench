# 知行 · 学习与工作工具箱

本地优先的五项工具与六个可独立安装的Skill。`site/`是无构建步骤的静态网站；`skills/`保留完整工作方法。

| 工具 | 网站功能 | Skill |
|---|---|---|
| 讲义与打印 | 本地PDF A4双拼、页序预览、下载 | study-handout-builder |
| 工作事项 | 导入任务JSON、状态过滤、覆盖说明、导出 | evidence-work-assistant |
| 研究访谈 | 手动问题/证据/追问编辑与Markdown导出 | research-interview-kit |
| 来源知识库 | EXTRACTED/INFERRED/UNVERIFIED来源卡 | evidence-notes |
| 周课表 | 录入课程、周次冲突、学分核算和日历 | university-course-selection-planner（1.1.1） |
| 视频剪辑 | Skill使用说明 | chatcut-event-recap |

## 运行与安装

运行 `python3 -m http.server 8080 --directory site`，打开localhost:8080。复制 `skills/` 中所需的子目录到自己的Skill目录。网页不调用模型、不访问聊天账户、不上传文件，不代表自动读取PDF内容或自动理解访谈。

聊天采集详见 `skills/evidence-work-assistant/references/collection-methods.md`。先doctor、再配置本人账户；所有原始聊天与报告留在本地数据目录，禁止提交到本仓库。

教师版实验工具独立为「格物 · 实验数据工作台」，仓库 `gewu-lab`。现有选课与个人知识库仓库保留，工具箱不是其历史版本替代。

## 开发与验证

`node tests/workbench.test.cjs` 检查周次、单双周、冲突和学分；聊天采集器的合成回归测试位于其scripts目录。不以测试结果冒充真实账号读取成功。

浏览器回归：`npm install`、`npx playwright install chromium`，启动上面的8765端口服务（或通过TEST_URL指定），运行 `npm run test:browser`。可用CHROME_BIN指定本机Chrome路径。测试使用虚构课程和自制PDF，不读取真实材料。运行时网站不需要npm依赖。

本仓库自有源码使用MIT；PDF-lib第三方许可见site/vendor。用户教材、课件、聊天、视频和配乐不包含在发布物中。
