# 通用型导出聊天记录 - 技能文档

快速将多种聊天应用的对话历史导出为格式化的 Markdown 文件，支持选择性导出、工具调用记录包含，让你的对话记录变得可读且易于分享！

## 支持的聊天应用

### 当前支持
- **Claude Code**：完全支持
- **微信**：开发中
- **QQ**：开发中
- **Slack**：开发中
- **Discord**：开发中

### 即将支持
- 钉钉
- Telegram
- WhatsApp
- 企业微信

## 功能特点

### 核心功能
- **多平台支持**：支持多种聊天应用的导出功能
- **智能解析**：自动识别用户和助手消息，排除工具调用的中间状态
- **灵活选择**：支持按项目、会话、大小、时间范围筛选导出
- **格式美观**：导出为标准 Markdown 格式，完美适配 Obsidian、Notion、VS Code
- **本地存储**：所有操作在本地完成，保护隐私，不上传任何数据
- **快捷操作**：支持 `/导出聊天` 等触发词，快速启动导出流程
- **按需导出**：可选是否包含工具调用记录（默认不包含，保持对话简洁）
- **媒体支持**：可选是否包含媒体文件（图片、视频、文件）

### 快捷用法

| 用法 | 说明 |
|------|------|
| `/导出聊天记录` | 完整交互流程（选应用 → 选会话 → 导出） |
| `/导出聊天记录 Claude` | 直接导出Claude Code的对话历史 |
| `/导出聊天记录 微信` | 直接导出微信的聊天记录 |
| `/导出聊天记录 最近5个` | 导出当前项目最近 5 个会话 |
| `/导出聊天记录 全部` | 导出当前项目所有会话 |
| `/导出聊天记录 大会话` | 只导出大于 10KB 的会话 |
| `/导出聊天记录 含工具` | 导出时包含工具调用记录 |
| `/导出聊天记录 含媒体` | 导出时包含媒体文件 |
| `/导出聊天记录 所有项目` | 列出所有项目让用户选择 |

## 使用方法

### 1. 安装技能

技能已成功安装到 Claude Code 的 `skills/` 目录中，用户可以通过触发词 `/导出聊天记录`、`/导出对话历史`、`/export-chat`、「导出聊天记录」、「导出对话历史」来使用。

### 2. 导出流程

1. **选择聊天应用**：显示支持的聊天应用列表，让用户选择
2. **列出项目/会话**：根据选择的应用，显示相应的项目或会话列表
3. **选择会话**：支持多种选择方式，如单个会话、多个会话、全部会话等
4. **导出设置**：可选是否包含工具调用记录和媒体文件
5. **生成文件**：导出为 Markdown 文件，保存在用户桌面

## 安装步骤

### 方法 1：使用技能安装功能

```bash
/安装技能 https://github.com/jungmiles33/export-chat-history-.git
```

### 方法 2：手动安装

1. 下载技能文件：
   ```bash
   git clone https://github.com/jungmiles33/export-chat-history-.git
   ```

2. 安装技能：
   ```bash
   # 复制到 Claude Code 的技能目录
   cp -r export-chat-history- ~/.claude/skills/
   ```

## 技术说明

### 存储位置

不同聊天应用的对话历史存储位置不同：

- **Claude Code**：`~/.claude/` 目录下，使用 JSONL 格式（每行一个 JSON）
- **微信**：`~/Documents/WeChat Files/` 目录下，使用数据库格式
- **QQ**：`~/Library/Containers/com.tencent.qq/Data/Library/Application Support/QQ/` 目录下
- **Slack**：`~/Library/Application Support/Slack/` 目录下，使用 JSON 格式
- **Discord**：`~/Library/Application Support/discord/` 目录下，使用 JSON 格式

### 文件格式

- **原始数据**：根据聊天应用不同，格式可能为 JSONL、JSON、数据库等
- **导出格式**：Markdown 格式，包含用户和助手的消息
- **编码**：完全支持 UTF-8 编码，支持中文

### 导出路径

- 默认导出到用户桌面：`~/Desktop/聊天记录导出/`
- 文件名格式：`YYYY-MM-DD_首条消息前20字.md`

## 局限性

1. **平台限制**：不同平台的支持程度不同，部分功能正在开发中
2. **数据位置**：只能导出本地存储的对话历史
3. **工具调用**：默认不导出工具调用记录，需要用户明确选择
4. **媒体文件**：默认不导出媒体文件，需要用户明确选择
5. **文件大小**：单个会话文件超过 1MB 时，导出可能会较慢
6. **微信/QQ解析**：需要特殊权限访问数据库，当前版本暂不支持

## 安全性

1. **隐私保障**：所有操作在本地完成，不向任何外部服务器发送数据
2. **权限控制**：导出文件保存到用户桌面，权限完全受控
3. **数据保护**：对话历史不会被修改或删除，仅用于导出
4. **安全解析**：对聊天记录进行安全解析，防止数据泄露

## 贡献指南

如果你发现问题或有改进建议，请通过以下方式反馈：

### 1. 报告问题

- 在 GitHub 仓库中提交 Issue
- 提供详细的问题描述和错误信息

### 2. 提交 Pull Request

1. Fork 仓库
2. 创建新分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -am 'Add your feature'`
4. 推送到分支：`git push origin feature/your-feature`
5. 创建 Pull Request

### 3. 开发环境

```bash
# 克隆仓库
git clone https://github.com/jungmiles33/export-chat-history-.git

# 进入项目目录
cd export-chat-history-

# 测试技能 - Claude Code
python scripts/universal_export.py claude <输出目录> --tools

# 测试技能 - 微信
python scripts/universal_export.py wechat <输出目录> --media
```

## 许可证

MIT License

---

**注意**：此技能仅供个人使用，未经授权不得用于商业用途。