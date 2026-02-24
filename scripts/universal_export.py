import json
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path


class ChatParser:
    """聊天记录解析器基类"""

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析会话文件，返回消息列表"""
        raise NotImplementedError("Subclasses must implement this method")

    def list_sessions(self):
        """列出所有会话"""
        raise NotImplementedError("Subclasses must implement this method")


class ClaudeCodeParser(ChatParser):
    """Claude Code 聊天记录解析器"""

    def __init__(self):
        self.base_dir = os.path.expanduser("~/.claude")

    def list_sessions(self):
        """列出所有项目和会话"""
        projects_dir = os.path.join(self.base_dir, "projects")
        if not os.path.exists(projects_dir):
            return []

        projects = []
        for project_dir in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_dir)
            if os.path.isdir(project_path):
                sessions = []
                for filename in os.listdir(project_path):
                    if filename.endswith(".jsonl"):
                        sessions.append(os.path.join(project_path, filename))

                # 还原项目路径
                readable_path = project_dir.replace("-", "/").replace("\\", "/")
                if readable_path.startswith("/"):
                    readable_path = readable_path[1:]

                projects.append({
                    "name": readable_path,
                    "path": project_path,
                    "sessions": sessions
                })

        return projects

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析Claude Code会话文件"""
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
                        text = self._extract_text(content)
                        if text:
                            messages.append({
                                'role': '🧑 用户',
                                'text': text,
                                'time': timestamp
                            })
                    elif msg_type == 'assistant' and role == 'assistant':
                        text = self._extract_text(content)
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

    def _extract_text(self, content):
        """从消息内容中提取文本"""
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
                        result_text = self._extract_text(result_content)
                        if len(result_text) > 500:
                            result_text = result_text[:500] + '\n...(已截断)'
                        texts.append(f'[工具返回结果]\n{result_text}')
            return '\n\n'.join(texts)
        return str(content)


class GPTParser(ChatParser):
    """GPT 聊天记录解析器"""

    def __init__(self):
        # 查找 GPT 聊天记录存储位置
        self.base_dir = self._find_gpt_dir()

    def _find_gpt_dir(self):
        """查找 GPT 聊天记录存储目录"""
        # 尝试常见的位置
        possible_dirs = [
            os.path.expanduser("~/Library/Application Support/OpenAI"),
            os.path.expanduser("~/.openai"),
            os.path.expanduser("~/Documents/OpenAI"),
            os.path.expanduser("~/AppData/Roaming/OpenAI")
        ]

        for d in possible_dirs:
            if os.path.exists(d):
                return d

        return None

    def list_sessions(self):
        """列出 GPT 聊天会话"""
        if not self.base_dir or not os.path.exists(self.base_dir):
            return []

        sessions = []
        for root, dirs, files in os.walk(self.base_dir):
            for filename in files:
                if filename.endswith(".json") or filename.endswith(".jsonl"):
                    sessions.append({
                        "name": filename,
                        "path": os.path.join(root, filename),
                        "sessions": []
                    })

        return sessions

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析 GPT 聊天记录"""
        messages = []
        try:
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)
                # 尝试多种可能的数据结构
                if 'messages' in data:
                    messages_data = data['messages']
                elif 'conversations' in data:
                    messages_data = data['conversations']
                else:
                    # 假设直接是消息数组
                    messages_data = data

                for msg in messages_data:
                    try:
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        timestamp = msg.get('created', '') or msg.get('timestamp', '')

                        if role == 'user':
                            messages.append({
                                'role': '🧑 用户',
                                'text': content.strip(),
                                'time': self._format_time(timestamp)
                            })
                        elif role == 'assistant' or role == 'system':
                            messages.append({
                                'role': '🤖 GPT',
                                'text': content.strip(),
                                'time': self._format_time(timestamp)
                            })
                    except:
                        pass
        except:
            # 如果解析失败，返回简单的错误信息
            messages.append({
                'role': '🧑 用户',
                'text': 'GPT聊天记录解析功能正在开发中...',
                'time': datetime.now().isoformat()
            })
            messages.append({
                'role': '🤖 系统',
                'text': 'GPT聊天记录解析需要访问特定的存储格式，当前版本暂不支持。',
                'time': datetime.now().isoformat()
            })

        return messages

    def _format_time(self, timestamp):
        """格式化时间戳"""
        if isinstance(timestamp, int) or isinstance(timestamp, float):
            return datetime.fromtimestamp(timestamp).isoformat()
        return timestamp


class GeminiParser(ChatParser):
    """Gemini 聊天记录解析器"""

    def __init__(self):
        # 查找 Gemini 聊天记录存储位置
        self.base_dir = self._find_gemini_dir()

    def _find_gemini_dir(self):
        """查找 Gemini 聊天记录存储目录"""
        possible_dirs = [
            os.path.expanduser("~/Library/Application Support/Google/Gemini"),
            os.path.expanduser("~/.gemini"),
            os.path.expanduser("~/Documents/Google/Gemini"),
            os.path.expanduser("~/AppData/Roaming/Google/Gemini")
        ]

        for d in possible_dirs:
            if os.path.exists(d):
                return d

        return None

    def list_sessions(self):
        """列出 Gemini 聊天会话"""
        if not self.base_dir or not os.path.exists(self.base_dir):
            return []

        sessions = []
        for root, dirs, files in os.walk(self.base_dir):
            for filename in files:
                if filename.endswith(".json") or filename.endswith(".jsonl"):
                    sessions.append({
                        "name": filename,
                        "path": os.path.join(root, filename),
                        "sessions": []
                    })

        return sessions

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析 Gemini 聊天记录"""
        messages = []
        try:
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)
                # 尝试多种可能的数据结构
                if 'messages' in data:
                    messages_data = data['messages']
                elif 'conversations' in data:
                    messages_data = data['conversations']
                else:
                    messages_data = data

                for msg in messages_data:
                    try:
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        timestamp = msg.get('created', '') or msg.get('timestamp', '')

                        if role == 'user':
                            messages.append({
                                'role': '🧑 用户',
                                'text': content.strip(),
                                'time': self._format_time(timestamp)
                            })
                        elif role == 'model' or role == 'assistant':
                            messages.append({
                                'role': '🤖 Gemini',
                                'text': content.strip(),
                                'time': self._format_time(timestamp)
                            })
                    except:
                        pass
        except:
            messages.append({
                'role': '🧑 用户',
                'text': 'Gemini聊天记录解析功能正在开发中...',
                'time': datetime.now().isoformat()
            })
            messages.append({
                'role': '🤖 系统',
                'text': 'Gemini聊天记录解析需要访问特定的存储格式，当前版本暂不支持。',
                'time': datetime.now().isoformat()
            })

        return messages

    def _format_time(self, timestamp):
        """格式化时间戳"""
        if isinstance(timestamp, int) or isinstance(timestamp, float):
            return datetime.fromtimestamp(timestamp).isoformat()
        return timestamp


class DoubaoParser(ChatParser):
    """豆包聊天记录解析器"""

    def __init__(self):
        # 查找豆包聊天记录存储位置
        self.base_dir = self._find_doubao_dir()

    def _find_doubao_dir(self):
        """查找豆包聊天记录存储目录"""
        possible_dirs = [
            os.path.expanduser("~/Library/Application Support/Doubao"),
            os.path.expanduser("~/.doubao"),
            os.path.expanduser("~/Documents/Doubao"),
            os.path.expanduser("~/AppData/Roaming/Doubao")
        ]

        for d in possible_dirs:
            if os.path.exists(d):
                return d

        return None

    def list_sessions(self):
        """列出豆包聊天会话"""
        if not self.base_dir or not os.path.exists(self.base_dir):
            return []

        sessions = []
        for root, dirs, files in os.walk(self.base_dir):
            for filename in files:
                if filename.endswith(".json") or filename.endswith(".jsonl"):
                    sessions.append({
                        "name": filename,
                        "path": os.path.join(root, filename),
                        "sessions": []
                    })

        return sessions

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析豆包聊天记录"""
        messages = []
        try:
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)
                # 尝试多种可能的数据结构
                if 'messages' in data:
                    messages_data = data['messages']
                elif 'conversations' in data:
                    messages_data = data['conversations']
                else:
                    messages_data = data

                for msg in messages_data:
                    try:
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        timestamp = msg.get('created', '') or msg.get('timestamp', '')

                        if role == 'user':
                            messages.append({
                                'role': '🧑 用户',
                                'text': content.strip(),
                                'time': self._format_time(timestamp)
                            })
                        elif role == 'assistant' or role == 'model':
                            messages.append({
                                'role': '🤖 豆包',
                                'text': content.strip(),
                                'time': self._format_time(timestamp)
                            })
                    except:
                        pass
        except:
            messages.append({
                'role': '🧑 用户',
                'text': '豆包聊天记录解析功能正在开发中...',
                'time': datetime.now().isoformat()
            })
            messages.append({
                'role': '🤖 系统',
                'text': '豆包聊天记录解析需要访问特定的存储格式，当前版本暂不支持。',
                'time': datetime.now().isoformat()
            })

        return messages

    def _format_time(self, timestamp):
        """格式化时间戳"""
        if isinstance(timestamp, int) or isinstance(timestamp, float):
            return datetime.fromtimestamp(timestamp).isoformat()
        return timestamp


class WeChatParser(ChatParser):
    """微信聊天记录解析器"""

    def __init__(self):
        self.base_dir = os.path.expanduser("~/Documents/WeChat Files")

    def list_sessions(self):
        """列出微信聊天会话"""
        if not os.path.exists(self.base_dir):
            return []

        # 简单实现 - 需要根据微信实际存储结构调整
        sessions = []
        for filename in os.listdir(self.base_dir):
            file_path = os.path.join(self.base_dir, filename)
            if os.path.isdir(file_path):
                sessions.append({
                    "name": filename,
                    "path": file_path,
                    "sessions": []
                })

        return sessions

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析微信聊天记录"""
        # 微信聊天记录解析实现（需要根据微信实际存储格式调整）
        # 微信使用数据库存储，需要特殊处理
        messages = []
        messages.append({
            'role': '🧑 用户',
            'text': '微信聊天记录解析功能正在开发中...',
            'time': datetime.now().isoformat()
        })
        messages.append({
            'role': '🤖 系统',
            'text': '微信聊天记录解析需要访问微信数据库，当前版本暂不支持。',
            'time': datetime.now().isoformat()
        })

        return messages


class QQParser(ChatParser):
    """QQ聊天记录解析器"""

    def __init__(self):
        self.base_dir = os.path.expanduser("~/Library/Containers/com.tencent.qq/Data/Library/Application Support/QQ")

    def list_sessions(self):
        """列出QQ聊天会话"""
        if not os.path.exists(self.base_dir):
            return []

        sessions = []
        for filename in os.listdir(self.base_dir):
            file_path = os.path.join(self.base_dir, filename)
            if os.path.isdir(file_path):
                sessions.append({
                    "name": filename,
                    "path": file_path,
                    "sessions": []
                })

        return sessions

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析QQ聊天记录"""
        # QQ聊天记录解析实现（需要根据QQ实际存储格式调整）
        messages = []
        messages.append({
            'role': '🧑 用户',
            'text': 'QQ聊天记录解析功能正在开发中...',
            'time': datetime.now().isoformat()
        })
        messages.append({
            'role': '🤖 系统',
            'text': 'QQ聊天记录解析需要访问QQ数据库，当前版本暂不支持。',
            'time': datetime.now().isoformat()
        })

        return messages


class SlackParser(ChatParser):
    """Slack聊天记录解析器"""

    def __init__(self):
        self.base_dir = os.path.expanduser("~/Library/Application Support/Slack")

    def list_sessions(self):
        """列出Slack聊天会话"""
        if not os.path.exists(self.base_dir):
            return []

        sessions = []
        for filename in os.listdir(self.base_dir):
            file_path = os.path.join(self.base_dir, filename)
            if os.path.isdir(file_path):
                sessions.append({
                    "name": filename,
                    "path": file_path,
                    "sessions": []
                })

        return sessions

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析Slack聊天记录"""
        # Slack聊天记录解析实现
        messages = []
        messages.append({
            'role': '🧑 用户',
            'text': 'Slack聊天记录解析功能正在开发中...',
            'time': datetime.now().isoformat()
        })
        messages.append({
            'role': '🤖 系统',
            'text': 'Slack聊天记录解析需要访问Slack API，当前版本暂不支持。',
            'time': datetime.now().isoformat()
        })

        return messages


class DiscordParser(ChatParser):
    """Discord聊天记录解析器"""

    def __init__(self):
        self.base_dir = os.path.expanduser("~/Library/Application Support/discord")

    def list_sessions(self):
        """列出Discord聊天会话"""
        if not os.path.exists(self.base_dir):
            return []

        sessions = []
        for filename in os.listdir(self.base_dir):
            file_path = os.path.join(self.base_dir, filename)
            if os.path.isdir(file_path):
                sessions.append({
                    "name": filename,
                    "path": file_path,
                    "sessions": []
                })

        return sessions

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析Discord聊天记录"""
        # Discord聊天记录解析实现
        messages = []
        messages.append({
            'role': '🧑 用户',
            'text': 'Discord聊天记录解析功能正在开发中...',
            'time': datetime.now().isoformat()
        })
        messages.append({
            'role': '🤖 系统',
            'text': 'Discord聊天记录解析需要访问Discord API，当前版本暂不支持。',
            'time': datetime.now().isoformat()
        })

        return messages


class ChatExporter:
    """聊天记录导出器"""

    def __init__(self, chat_app):
        # 根据聊天应用选择解析器
        parsers = {
            "claude": ClaudeCodeParser,
            "wechat": WeChatParser,
            "qq": QQParser,
            "slack": SlackParser,
            "discord": DiscordParser,
            "gpt": GPTParser,
            "gemini": GeminiParser,
            "doubao": DoubaoParser
        }

        if chat_app.lower() not in parsers:
            raise ValueError(f"不支持的聊天应用: {chat_app}")

        self.parser = parsers[chat_app.lower()]()
        self.chat_app = chat_app.lower()

    def list_sessions(self):
        """列出所有会话"""
        return self.parser.list_sessions()

    def parse_session(self, filepath, include_tools=False, include_media=False):
        """解析会话文件"""
        return self.parser.parse_session(filepath, include_tools, include_media)

    def export_to_markdown(self, messages, output_dir, include_tools=False, include_media=False):
        """导出为Markdown格式"""
        if not messages:
            print("没有可导出的消息。")
            return

        # 获取时间范围
        first_time = messages[0].get('time', '')[:10] if messages else '未知'
        last_time = messages[-1].get('time', '')[:10] if messages else '未知'

        # 生成文件名
        first_msg = messages[0]['text'] if messages else '无标题'
        safe_first_msg = first_msg[:20].replace('/', '_').replace('\\', '_').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
        filename = f"{first_time}_{safe_first_msg}.md"
        output_file = os.path.join(output_dir, filename)

        # 生成Markdown
        md_lines = []
        md_lines.append(f'# {self.get_chat_app_name()} 聊天记录')
        md_lines.append('')
        md_lines.append(f'- 导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}')
        md_lines.append(f'- 对话时间：{first_time} ~ {last_time}')
        md_lines.append(f'- 消息数量：{len(messages)} 条')
        md_lines.append('')
        md_lines.append('---')
        md_lines.append('')

        for msg in messages:
            time_str = msg['time'][11:16] if len(msg['time']) > 16 else ''
            md_lines.append(f'## {msg["role"]} {time_str}')
            md_lines.append('')
            md_lines.append(msg['text'])
            md_lines.append('')
            md_lines.append('---')
            md_lines.append('')

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        print('OK 已导出 {} 条消息 -> {}'.format(len(messages), output_file))

    def get_chat_app_name(self):
        """获取聊天应用的中文名称"""
        names = {
            "claude": "Claude Code",
            "wechat": "微信",
            "qq": "QQ",
            "slack": "Slack",
            "discord": "Discord",
            "gpt": "GPT",
            "gemini": "Gemini",
            "doubao": "豆包"
        }
        return names.get(self.chat_app, self.chat_app)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='通用型聊天记录导出工具')
    parser.add_argument('chat_app', help='聊天应用名称 (claude/wechat/qq/slack/discord)')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--tools', action='store_true', help='包含工具调用记录')
    parser.add_argument('--media', action='store_true', help='包含媒体文件')
    parser.add_argument('--session', help='特定会话文件路径')

    args = parser.parse_args()

    try:
        # 创建导出器
        exporter = ChatExporter(args.chat_app)

        # 如果指定了特定会话文件
        if args.session:
            messages = exporter.parse_session(args.session, args.tools, args.media)
            exporter.export_to_markdown(messages, args.output_dir, args.tools, args.media)
        else:
            # 列出所有会话
            sessions = exporter.list_sessions()

            if not sessions:
                print("未找到任何会话。")
                return

            # 显示会话列表
            print(f'您的 {exporter.get_chat_app_name()} 会话列表：')
            for i, project in enumerate(sessions):
                print(f'{i+1}. {project["name"]}')
                print(f'   会话数：{len(project["sessions"])}')
                print()

            # 让用户选择会话
            try:
                choice = int(input("请输入要导出的项目编号（如 1）：")) - 1
                if choice < 0 or choice >= len(sessions):
                    print("无效的选择。")
                    return

                selected_project = sessions[choice]

                # 导出该项目的所有会话
                for session_file in selected_project["sessions"]:
                    messages = exporter.parse_session(session_file, args.tools, args.media)
                    exporter.export_to_markdown(messages, args.output_dir, args.tools, args.media)

                print(f'\n✅ 导出完成！共导出 {len(selected_project["sessions"])} 个会话')

            except ValueError:
                print("请输入有效的数字。")
            except KeyboardInterrupt:
                print("\n导出已取消。")

    except Exception as e:
        print(f"导出过程中出错：{str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()