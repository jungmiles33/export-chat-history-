---
name: export-chat-history
description: 导出 Claude Code 的对话历史为可读的 Markdown 文件。支持选择项目、会话，并可选择是否包含工具调用记录。触发词：/导出聊天、/导出对话、/export、导出聊天记录、导出对话历史
license: MIT
---

# 导出聊天记录

## 触发方式
`/导出聊天`、`/导出对话`、`/export`、「导出聊天记录」、「导出对话历史」

## 适用范围
任何安装了 Claude Code 的用户都可以使用。不依赖特定项目结构。

## 核心机制
读取本地 `~/.claude/` 目录中的对话历史，让用户选择项目和会话，导出为可读的 Markdown 文件。

---

## 执行流程

### 第一步：列出所有项目
运行以下命令获取项目列表：
```bash
ls ~/.claude/projects/
```
将目录名转换为可读的项目路径（把 `-` 还原为 `/`），以编号列表展示：
```
你的 Claude Code 项目列表：
 #  项目路径                                      会话数
1  /Users/xxx/Documents/my-project               23 个会话
2  /Users/xxx/code/another-project               8 个会话
3  （全局会话 — 不属于任何项目）                    N 条记录
```
**转换规则**：目录名中的 `-` 对应原始路径中的 `/` 或 `-`。用以下逻辑还原：
- 目录名开头的 `-` 表示路径从 `/` 开始
- 连续的 `-` 中，优先匹配已知路径段（如 `Users`、`Documents`、`Library` 等）
- 无法精确还原时，直接显示目录名，让用户自己辨认

**全局会话**：`~/.claude/history.jsonl` 包含所有项目的历史摘要，作为第 3 个选项提供。

然后问用户：「请输入项目编号（如 1），或输入 all 导出所有项目」

### 第二步：列出该项目的会话
用户选择项目后，列出该项目下的所有会话文件，按时间倒序排列：
```bash
ls -lt ~/.claude/projects/<项目目录>/*.jsonl
```
对每个会话文件，提取第一条用户消息作为预览：
```bash
python3 -c "import json, sys, os
from datetime import datetime

filepath = sys.argv[1]
first_user_msg = ''
timestamp = ''
msg_count = 0

with open(filepath) as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            if obj.get('type') == 'user':
                msg_count += 1
                if not first_user_msg:
                    ts = obj.get('timestamp', '')
                    content = obj.get('message', {}).get('content', '')
                    if isinstance(content, str):
                        first_user_msg = content[:80]
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                first_user_msg = item['text'][:80]
                                break
                    timestamp = ts
        except:
            pass

# 格式化时间
date_str = timestamp[:10] if timestamp else '未知日期'
size = os.path.getsize(filepath)
size_str = f'{size // 1024}KB' if size > 1024 else f'{size}B'

print(f'{date_str} | {msg_count}轮对话 | {size_str} | {first_user_msg}')" <会话文件路径>
```
展示格式：
```
项目「xxx」的会话列表（共 23 个）：

 #   日期         轮数    大小    首条消息预览
1   2026-02-24   15轮   45KB   帮我写一个推文关于 AI 工具选择...
2   2026-02-23   8轮    22KB   整理一下财务数据...
3   2026-02-22   3轮    5KB    查看选题库...
...
```
然后问用户：
- 「请输入会话编号（如 1），多个用逗号分隔（如 1,3,5）」
- 「输入 all 导出全部，输入 recent5 导出最近 5 个」
- 「输入 big 只导出大于 10KB 的会话（过滤掉短对话）」

### 第三步：解析并导出会话
用户选择会话后，用以下 Python 脚本解析 JSONL 并生成 Markdown：

```python
import json
import sys
import os
from datetime import datetime


def extract_text(content):
    """从消息 content 中提取纯文本"""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    texts.append(item['text'].strip())
                elif item.get('type') == 'tool_use':
                    tool = item.get('name', '未知工具')
                    inp = json.dumps(item.get('input', {}), ensure_ascii=False)
                    if len(inp) > 200:
                        inp = inp[:200] + '...'
                    texts.append(f'[调用工具：{tool}]\n参数：{inp}')
                elif item.get('type') == 'tool_result':
                    result_content = item.get('content', '')
                    result_text = extract_text(result_content)
                    if len(result_text) > 500:
                        result_text = result_text[:500] + '\n...(已截断)'
                    texts.append(f'[工具返回结果]\n{result_text}')
        return '\n\n'.join(texts)
    return str(content)


def parse_session(filepath, include_tools=False):
    """解析一个会话文件，返回消息列表"""
    messages = []
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
                msg_type = obj.get('type', '')
                timestamp = obj.get('timestamp', '')
                msg = obj.get('message', {})
                role = msg.get('role', '')
                content = msg.get('content', '')

                # 只保留用户和助手的消息
                if msg_type == 'user' and role == 'user':
                    text = extract_text(content)
                    if text:
                        messages.append({
                            'role': '🧑 用户',
                            'text': text,
                            'time': timestamp
                        })
                elif msg_type == 'assistant' and role == 'assistant':
                    text = extract_text(content)
                    if text:
                        # 过滤掉纯工具调用（除非用户要求包含）
                        if not include_tools and text.startswith('[调用工具'):
                            continue
                        messages.append({
                            'role': '🤖 Claude',
                            'text': text,
                            'time': timestamp
                        })
            except:
                pass
    return messages


def main():
    if len(sys.argv) < 3:
        print('使用方法: python export_chat.py <会话文件路径> <输出目录> [--tools]')
        return

    session_file = sys.argv[1]
    output_dir = sys.argv[2]
    include_tools = '--tools' in sys.argv

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 解析会话
    messages = parse_session(session_file, include_tools)

    if not messages:
        print('该会话没有可导出的消息。')
        return

    # 获取时间范围
    first_time = messages[0].get('time', '')[:10] if messages else '未知'
    last_time = messages[-1].get('time', '')[:10] if messages else '未知'

    # 生成文件名
    first_msg = messages[0]['text'] if messages else '无标题'
    filename = f"{first_time}_{first_msg[:20].replace('/', '_').replace('\\', '_').replace(':', '').replace('*', '').replace('?', '').replace('\"', '').replace('<', '').replace('>', '').replace('|', '')}.md"
    output_file = os.path.join(output_dir, filename)

    # 生成 Markdown
    md_lines = []
    md_lines.append(f'# Claude Code 对话记录')
    md_lines.append(f'')
    md_lines.append(f'- 导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}')
    md_lines.append(f'- 对话时间：{first_time} ~ {last_time}')
    md_lines.append(f'- 消息数量：{len(messages)} 条')
    md_lines.append(f'- 源文件：`{os.path.basename(session_file)}`')
    md_lines.append(f'')
    md_lines.append(f'---')
    md_lines.append(f'')

    for msg in messages:
        time_str = msg['time'][11:16] if len(msg['time']) > 16 else ''
        md_lines.append(f'## {msg["role"]} {time_str}')
        md_lines.append(f'')
        md_lines.append(msg['text'])
        md_lines.append(f'')
        md_lines.append(f'---')
        md_lines.append(f'')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f'✅ 已导出 {len(messages)} 条消息 → {output_file}')


if __name__ == '__main__':
    main()
```

**导出路径规则**：
- 默认导出到用户桌面：`~/Desktop/Claude对话导出/`
- 文件名格式：`YYYY-MM-DD_首条消息前20字.md`
- 如果用户指定了路径，用用户指定的路径

**导出前确认**：
```
即将导出 3 个会话到 ~/Desktop/Claude对话导出/：

1. 2026-02-24_帮我写一个推文关于AI.md（预计 15 条消息）
2. 2026-02-23_整理一下财务数据.md（预计 8 条消息）
3. 2026-02-22_查看选题库.md（预计 3 条消息）

是否包含工具调用记录？（默认不包含，输入 yes 包含）
```

### 第四步：执行导出
```bash
# 创建导出目录
mkdir -p ~/Desktop/Claude对话导出/

# 对每个选中的会话执行导出脚本
python3 <上述脚本> <会话文件> <输出路径> [--tools]
```
导出完成后显示：
```
✅ 导出完成！

📁 导出位置：~/Desktop/Claude对话导出/
📄 共导出 3 个文件：
   1. 2026-02-24_帮我写一个推文关于AI.md（15 条消息，23KB）
   2. 2026-02-23_整理一下财务数据.md（8 条消息，12KB）
   3. 2026-02-22_查看选题库.md（3 条消息，4KB）

💡 提示：文件是标准 Markdown 格式，可以用 Typora、Obsidian、VS Code 等打开。
```

---

## 快捷用法
用户可以跳过交互步骤，直接指定参数：

| 用法 | 说明 |
|------|------|
| `/导出聊天` | 完整交互流程（选项目 → 选会话 → 导出） |
| `/导出聊天 最近5个` | 导出当前项目最近 5 个会话 |
| `/导出聊天 全部` | 导出当前项目所有会话 |
| `/导出聊天 大会话` | 只导出大于 10KB 的会话 |
| `/导出聊天 含工具` | 导出时包含工具调用记录 |
| `/导出聊天 所有项目` | 列出所有项目让用户选择 |

---

## 注意事项
1. **隐私安全**：所有操作都在本地完成，不上传任何数据。导出的文件保存在用户自己的桌面
2. **数据位置**：Claude Code 的对话历史存储在 `~/.claude/` 目录，这是用户主目录下的隐藏文件夹，不在 iCloud 或项目文件夹中
3. **文件格式**：会话文件是 JSONL 格式（每行一个 JSON），导出为 Markdown 方便阅读
4. **工具调用**：默认不导出工具调用记录（如文件读写、Bash 命令），因为这些通常很长且不影响对话理解。用户可以选择包含
5. **大文件处理**：如果单个会话文件超过 1MB，提醒用户导出可能较慢
6. **编码**：所有文件使用 UTF-8 编码，支持中文
7. **去重**：assistant 类型的消息可能有多条（流式输出的中间状态），只保留最后一条完整的