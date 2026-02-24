import os
import sys
import json
import tempfile
from datetime import datetime
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.universal_export import ChatExporter, ClaudeCodeParser, GPTParser, GeminiParser, DoubaoParser


def test_claude_code_parser_find_dir():
    """测试 Claude Code 解析器是否能找到存储目录"""
    parser = ClaudeCodeParser()
    assert parser.base_dir is not None, "Claude Code 存储目录未找到"
    assert os.path.exists(parser.base_dir), f"Claude Code 存储目录不存在: {parser.base_dir}"
    print("OK Claude Code 解析器存储目录查找成功")


def test_claude_code_list_sessions():
    """测试 Claude Code 解析器是否能列出会话"""
    parser = ClaudeCodeParser()
    projects = parser.list_sessions()
    print(f"OK Claude Code 解析器找到 {len(projects)} 个项目")
    for i, project in enumerate(projects, 1):
        print(f"  项目 {i}: {project['name']} ({len(project['sessions'])} 个会话)")


def test_claude_code_parse_session():
    """测试 Claude Code 解析器是否能解析会话"""
    parser = ClaudeCodeParser()
    projects = parser.list_sessions()

    if projects:
        # 找到第一个包含会话的项目
        for project in projects:
            if project['sessions']:
                session_file = project['sessions'][0]
                print(f"OK 解析会话: {session_file}")
                messages = parser.parse_session(session_file)
                assert len(messages) > 0, "会话解析失败"
                print(f"OK 成功解析 {len(messages)} 条消息")

                user_messages = [m for m in messages if m['role'] == '🧑 用户']
                assistant_messages = [m for m in messages if m['role'] == '🤖 Claude']
                print(f"  用户消息: {len(user_messages)}, 助手消息: {len(assistant_messages)}")

                # 测试包含工具调用的解析
                messages_with_tools = parser.parse_session(session_file, include_tools=True)
                print(f"OK 包含工具调用的消息: {len(messages_with_tools)} 条")

                break
        else:
            print("WARN 未找到任何会话文件")
    else:
        print("WARN 未找到任何项目")


def test_gpt_parser():
    """测试 GPT 解析器"""
    parser = GPTParser()
    print(f"OK GPT 解析器存储目录: {parser.base_dir}")

    if parser.base_dir:
        sessions = parser.list_sessions()
        print(f"OK GPT 解析器找到 {len(sessions)} 个会话")

        if sessions:
            session = sessions[0]
            messages = parser.parse_session(session['path'])
            print(f"OK 解析会话: {len(messages)} 条消息")
    else:
        print("WARN GPT 解析器存储目录未找到")


def test_gemini_parser():
    """测试 Gemini 解析器"""
    parser = GeminiParser()
    print(f"OK Gemini 解析器存储目录: {parser.base_dir}")

    if parser.base_dir:
        sessions = parser.list_sessions()
        print(f"OK Gemini 解析器找到 {len(sessions)} 个会话")

        if sessions:
            session = sessions[0]
            messages = parser.parse_session(session['path'])
            print(f"OK 解析会话: {len(messages)} 条消息")
    else:
        print("WARN Gemini 解析器存储目录未找到")


def test_doubao_parser():
    """测试 豆包 解析器"""
    parser = DoubaoParser()
    print(f"OK 豆包 解析器存储目录: {parser.base_dir}")

    if parser.base_dir:
        sessions = parser.list_sessions()
        print(f"OK 豆包 解析器找到 {len(sessions)} 个会话")

        if sessions:
            session = sessions[0]
            messages = parser.parse_session(session['path'])
            print(f"OK 解析会话: {len(messages)} 条消息")
    else:
        print("WARN 豆包 解析器存储目录未找到")


def test_exporter_initialization():
    """测试导出器初始化"""
    chat_apps = ["claude", "gpt", "gemini", "doubao"]
    for app in chat_apps:
        try:
            exporter = ChatExporter(app)
            print(f"OK {app} 导出器初始化成功")
        except Exception as e:
            print(f"ERROR {app} 导出器初始化失败: {str(e)}")


def test_markdown_export():
    """测试 Markdown 导出功能"""
    parser = ClaudeCodeParser()
    projects = parser.list_sessions()

    if projects:
        for project in projects:
            if project['sessions']:
                session_file = project['sessions'][0]

                # 测试导出功能
                exporter = ChatExporter("claude")
                messages = exporter.parse_session(session_file)

                with tempfile.TemporaryDirectory() as temp_dir:
                    output_dir = temp_dir
                    exporter.export_to_markdown(messages, output_dir)

                    # 检查导出文件是否生成
                    exported_files = list(Path(output_dir).glob("*.md"))
                    assert len(exported_files) == 1, "未生成导出文件"

                    # 检查文件内容
                    exported_file = exported_files[0]
                    assert exported_file.stat().st_size > 0, "导出文件为空"

                    with open(exported_file, encoding='utf-8') as f:
                        content = f.read()
                        assert "# Claude Code 聊天记录" in content, "文件内容不正确"

                    print(f"OK Markdown 导出成功: {exported_file.name}")
                break
        else:
            print("WARN 未找到任何会话文件")
    else:
        print("WARN 未找到任何项目")


if __name__ == "__main__":
    print("=== 聊天记录导出工具测试 ===")
    print()

    print("1. 测试解析器功能")
    test_claude_code_parser_find_dir()
    print()

    test_claude_code_list_sessions()
    print()

    test_claude_code_parse_session()
    print()

    print("2. 测试导出器初始化")
    test_exporter_initialization()
    print()

    print("3. 测试其他解析器")
    test_gpt_parser()
    print()

    test_gemini_parser()
    print()

    test_doubao_parser()
    print()

    print("4. 测试导出功能")
    test_markdown_export()
    print()

    print("=== 所有测试完成 ===")