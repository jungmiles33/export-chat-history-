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
    # 处理文件名中的特殊字符
    safe_first_msg = first_msg[:20].replace('/', '_').replace('\\', '_').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
    filename = f"{first_time}_{safe_first_msg}.md"
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

    print('OK 已导出 {} 条消息 -> {}'.format(len(messages), output_file))


if __name__ == '__main__':
    main()