#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题目测试脚本
用于测试不同题型的答题功能
"""

import requests
import json
import sys
import os
from datetime import datetime

# API配置
API_BASE = "http://localhost:5000"
API_KEY = ""  # 如果需要认证，请填入API密钥

# 测试题目库
TEST_QUESTIONS = {
    0: {  # 单选题
        "name": "单选题",
        "questions": [
            {
                "question": "以下哪个是Python的Web框架？",
                "options": ["Flask", "React", "Vue", "Angular"],
                "type": 0
            },
            {
                "question": "HTTP状态码200表示什么？",
                "options": ["成功", "重定向", "客户端错误", "服务器错误"],
                "type": 0
            },
            {
                "question": "以下哪个不是编程语言？",
                "options": ["HTML", "Python", "Java", "C++"],
                "type": 0
            }
        ]
    },
    1: {  # 多选题
        "name": "多选题",
        "questions": [
            {
                "question": "以下哪些是前端框架？（多选）",
                "options": ["React", "Vue", "Angular", "Django"],
                "type": 1
            },
            {
                "question": "以下哪些是数据库？（多选）",
                "options": ["MySQL", "Redis", "MongoDB", "Nginx"],
                "type": 1
            },
            {
                "question": "以下哪些是云服务提供商？（多选）",
                "options": ["AWS", "Azure", "阿里云", "GitHub"],
                "type": 1
            }
        ]
    },
    3: {  # 填空题
        "name": "填空题",
        "questions": [
            {
                "question": "Python中用于定义函数的关键字是____",
                "options": [],
                "type": 3
            },
            {
                "question": "HTTP协议默认端口号是____",
                "options": [],
                "type": 3
            },
            {
                "question": "在Git中，用于提交代码的命令是git ____",
                "options": [],
                "type": 3
            }
        ]
    },
    4: {  # 判断题
        "name": "判断题",
        "questions": [
            {
                "question": "Python是一种编译型语言",
                "options": ["正确", "错误"],
                "type": 4
            },
            {
                "question": "HTTP是一种安全的协议",
                "options": ["正确", "错误"],
                "type": 4
            },
            {
                "question": "JSON是一种数据交换格式",
                "options": ["正确", "错误"],
                "type": 4
            }
        ]
    }
}

# 带图片的测试题目
IMAGE_QUESTIONS = [
    {
        "question": "这是什么动物？",
        "options": ["猫", "狗", "兔子", "老鼠"],
        "type": 0,
        "images": ["https://example.com/cat.jpg"]
    },
    {
        "question": "图片中显示的是什么颜色？",
        "options": ["红色", "蓝色", "绿色", "黄色"],
        "type": 0,
        "images": ["https://example.com/color.jpg"]
    }
]


def print_header():
    """打印标题"""
    print("\n" + "=" * 80)
    print("🤖 OCS AI 答题测试脚本")
    print("=" * 80)


def print_menu():
    """打印菜单"""
    print("\n📝 请选择要测试的题型：")
    print("  0 - 单选题")
    print("  1 - 多选题")
    print("  3 - 填空题")
    print("  4 - 判断题")
    print("  5 - 图片题（需要多模态模型）")
    print("  6 - 自定义题目")
    print("  q - 退出")
    print("-" * 80)


def load_api_key():
    """从.secret_key文件加载API密钥"""
    global API_KEY
    
    secret_file = '.secret_key'
    if os.path.exists(secret_file):
        try:
            with open(secret_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                API_KEY = data.get('raw_key', '')
                if API_KEY:
                    print(f"✅ 已加载API密钥: {API_KEY[:8]}...")
                    return True
        except Exception as e:
            print(f"⚠️  加载API密钥失败: {e}")
    
    # 尝试从用户输入获取
    print("\n🔐 未找到API密钥文件，请输入API密钥（如果不需要认证，直接回车）：")
    key = input("API密钥: ").strip()
    if key:
        API_KEY = key
        return True
    
    return False


def call_api(question_data):
    """调用答题API"""
    url = f"{API_BASE}/api/answer"
    headers = {
        "Content-Type": "application/json"
    }
    
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    try:
        print(f"\n⏳ 正在调用AI模型...")
        start_time = datetime.now()
        
        response = requests.post(url, json=question_data, headers=headers, timeout=60)
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        if response.status_code == 200:
            result = response.json()
            return True, result, elapsed
        else:
            error_msg = response.json().get('error', '未知错误')
            return False, error_msg, elapsed
            
    except requests.exceptions.Timeout:
        return False, "请求超时（60秒）", 0
    except requests.exceptions.ConnectionError:
        return False, f"无法连接到服务器 {API_BASE}", 0
    except Exception as e:
        return False, str(e), 0


def display_result(success, result, elapsed):
    """显示结果"""
    print("\n" + "=" * 80)
    
    if success:
        print("✅ 答题成功！")
        print("-" * 80)
        print(f"📝 题目: {result.get('question', 'N/A')}")
        print(f"✨ AI答案: {result.get('answer', 'N/A')}")
        print(f"🤖 原始回答: {result.get('raw_answer', 'N/A')}")
        print(f"🎯 使用模型: {result.get('model', 'N/A')}")
        print(f"🏢 提供商: {result.get('provider', 'N/A')}")
        print(f"🧠 思考模式: {'是' if result.get('reasoning_used') else '否'}")
        print(f"⏱️  AI用时: {result.get('ai_time', 0):.2f}秒")
        print(f"⏱️  总用时: {elapsed:.2f}秒")
        
        # Token使用量
        usage = result.get('usage', {})
        if usage:
            print(f"💰 Token使用: 输入={usage.get('prompt_tokens', 0)}, "
                  f"输出={usage.get('completion_tokens', 0)}, "
                  f"总计={usage.get('total_tokens', 0)}")
    else:
        print("❌ 答题失败！")
        print("-" * 80)
        print(f"错误信息: {result}")
        print(f"用时: {elapsed:.2f}秒")
    
    print("=" * 80)


def test_question_type(type_num):
    """测试指定题型"""
    if type_num not in TEST_QUESTIONS:
        print(f"❌ 无效的题型编号: {type_num}")
        return
    
    type_data = TEST_QUESTIONS[type_num]
    print(f"\n📚 测试题型: {type_data['name']}")
    print(f"共有 {len(type_data['questions'])} 道题目")
    
    for i, question in enumerate(type_data['questions'], 1):
        print(f"\n{'=' * 80}")
        print(f"第 {i}/{len(type_data['questions'])} 题")
        print(f"{'=' * 80}")
        print(f"题目: {question['question']}")
        if question['options']:
            print(f"选项: {' | '.join(question['options'])}")
        
        # 调用API
        success, result, elapsed = call_api(question)
        display_result(success, result, elapsed)
        
        # 询问是否继续
        if i < len(type_data['questions']):
            choice = input("\n按回车继续下一题，输入 q 返回菜单: ").strip().lower()
            if choice == 'q':
                break


def test_image_questions():
    """测试图片题"""
    print(f"\n📷 测试图片题")
    print(f"共有 {len(IMAGE_QUESTIONS)} 道题目")
    print("⚠️  注意：需要配置支持多模态的模型（如豆包）")
    
    for i, question in enumerate(IMAGE_QUESTIONS, 1):
        print(f"\n{'=' * 80}")
        print(f"第 {i}/{len(IMAGE_QUESTIONS)} 题")
        print(f"{'=' * 80}")
        print(f"题目: {question['question']}")
        print(f"选项: {' | '.join(question['options'])}")
        print(f"图片: {', '.join(question['images'])}")
        
        # 调用API
        success, result, elapsed = call_api(question)
        display_result(success, result, elapsed)
        
        # 询问是否继续
        if i < len(IMAGE_QUESTIONS):
            choice = input("\n按回车继续下一题，输入 q 返回菜单: ").strip().lower()
            if choice == 'q':
                break


def test_custom_question():
    """测试自定义题目"""
    print("\n✏️  自定义题目")
    print("-" * 80)
    
    # 选择题型
    print("请选择题型：")
    print("  0 - 单选题")
    print("  1 - 多选题")
    print("  3 - 填空题")
    print("  4 - 判断题")
    
    type_input = input("题型编号: ").strip()
    try:
        type_num = int(type_input)
        if type_num not in [0, 1, 3, 4]:
            print("❌ 无效的题型编号")
            return
    except ValueError:
        print("❌ 请输入数字")
        return
    
    # 输入题目
    question_text = input("\n请输入题目: ").strip()
    if not question_text:
        print("❌ 题目不能为空")
        return
    
    # 输入选项
    options = []
    if type_num in [0, 1, 4]:  # 选择题和判断题需要选项
        print("\n请输入选项（每行一个，输入空行结束）：")
        while True:
            option = input(f"选项 {len(options) + 1}: ").strip()
            if not option:
                break
            options.append(option)
        
        if not options:
            print("❌ 选择题至少需要一个选项")
            return
    
    # 构建请求
    question_data = {
        "question": question_text,
        "options": options,
        "type": type_num
    }
    
    # 询问是否添加图片
    add_image = input("\n是否添加图片URL？(y/n): ").strip().lower()
    if add_image == 'y':
        images = []
        print("请输入图片URL（每行一个，输入空行结束）：")
        while True:
            image_url = input(f"图片 {len(images) + 1}: ").strip()
            if not image_url:
                break
            images.append(image_url)
        
        if images:
            question_data["images"] = images
    
    # 显示题目信息
    print(f"\n{'=' * 80}")
    print("题目信息：")
    print(f"题型: {TEST_QUESTIONS[type_num]['name']}")
    print(f"题目: {question_text}")
    if options:
        print(f"选项: {' | '.join(options)}")
    if question_data.get('images'):
        print(f"图片: {', '.join(question_data['images'])}")
    print(f"{'=' * 80}")
    
    # 确认提交
    confirm = input("\n确认提交？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return
    
    # 调用API
    success, result, elapsed = call_api(question_data)
    display_result(success, result, elapsed)


def main():
    """主函数"""
    print_header()
    
    # 加载API密钥
    load_api_key()
    
    # 主循环
    while True:
        print_menu()
        choice = input("请选择 (0-6/q): ").strip().lower()
        
        if choice == 'q':
            print("\n👋 再见！")
            break
        
        if choice == '5':
            test_image_questions()
        elif choice == '6':
            test_custom_question()
        elif choice in ['0', '1', '3', '4']:
            try:
                type_num = int(choice)
                test_question_type(type_num)
            except ValueError:
                print("❌ 无效的输入")
        else:
            print("❌ 无效的选择，请输入 0-6 或 q")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已中断，再见！")
        sys.exit(0)
