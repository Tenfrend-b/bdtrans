#!/data/data/com.termux/files/usr/bin/env python
import requests
import random
import json
from hashlib import md5
import argparse
import sys
import os

# Set your own appid/appkey.
appid = ''
appkey = ''

# For list of language codes, please refer to `https://api.fanyi.baidu.com/doc/21`
# Default language settings
default_from_lang = 'auto'  # 默认自动检测
default_to_lang = 'zh'      # 默认翻译为中文

endpoint = 'http://api.fanyi.baidu.com'
path = '/api/trans/vip/translate'
url = endpoint + path

def make_md5(s, encoding='utf-8'):
    return md5(s.encode(encoding)).hexdigest()

def translate_text(query, from_lang=default_from_lang, to_lang=default_to_lang):
    """翻译文本并返回结果"""
    # Check if appid and appkey are set
    if not appid or not appkey:
        print("错误: 请先在代码中设置appid和appkey", file=sys.stderr)
        return None
    
    # Generate salt and sign
    salt = random.randint(32768, 65536)
    sign = make_md5(appid + query + str(salt) + appkey)
    
    # Build request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}
    
    try:
        # Send request
        r = requests.post(url, params=payload, headers=headers)
        result = r.json()
        
        # Check for errors
        if 'error_code' in result:
            print(f"翻译错误 (错误码: {result['error_code']}): {result.get('error_msg', '未知错误')}", file=sys.stderr)
            return None
        
        # Return translated text
        if 'trans_result' in result:
            return '\n'.join([item['dst'] for item in result['trans_result']])
        else:
            print("翻译结果格式错误", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"请求失败: {e}", file=sys.stderr)
        return None

def print_help():
    """打印使用说明"""
    help_text = """
百度翻译命令行工具

使用方法:
  python bdtrans.py -h                   显示此帮助信息
  python bdtrans.py -w TEXT1 TEXT2 ...   单独翻译每个文本(多个请求)
  python bdtrans.py -s TEXT              统一翻译所有文本(单个请求)
  python bdtrans.py -f FILE_PATH         翻译文件内容

语言选项:
  -i, --input-lang LANG   指定输入语言 (默认: auto-自动检测)
  -o, --output-lang LANG  指定输出语言 (默认: zh-中文)

纯净模式:
  -p, --pure              纯净输出模式(只输出译文，适用于管道操作)
                          必须与-s或-f选项同时使用

常用语言代码:
  auto - 自动检测  en - 英语  zh - 中文  jp - 日语  kor - 韩语
  fra - 法语  spa - 西班牙语  th - 泰语  ara - 阿拉伯语  ru - 俄语
  pt - 葡萄牙语  de - 德语  it - 意大利语  el - 希腊语  nl - 荷兰语
  pl - 波兰语  bul - 保加利亚语  est - 爱沙尼亚语  dan - 丹麦语
  fin - 芬兰语  cs - 捷克语  rom - 罗马尼亚语  slo - 斯洛文尼亚语
  swe - 瑞典语  hu - 匈牙利语  cht - 繁体中文  vie - 越南语

示例:
  python bdtrans.py -w "hello" "world"
  python bdtrans.py -s "Hello world, this is a test."
  python bdtrans.py -f document.txt
  python bdtrans.py -i en -o jp -w "good morning"
  python bdtrans.py -i auto -o fra -s "This is a book"
  python bdtrans.py -p -s "This is a test"  # 纯净输出
  python bdtrans.py -p -f document.txt      # 纯净输出文件内容

管道使用示例:
  echo "Hello World" | python bdtrans.py -p -s
  cat document.txt | python bdtrans.py -p -s

注意:
  使用前请在代码中设置有效的appid和appkey
  完整语言代码列表请参考: https://api.fanyi.baidu.com/doc/21
    """
    print(help_text)

def main():
    parser = argparse.ArgumentParser(description='百度翻译命令行工具', add_help=False)
    
    # 添加语言选项
    parser.add_argument('-i', '--input-lang', default=default_from_lang, 
                       help='输入语言代码 (默认: auto)')
    parser.add_argument('-o', '--output-lang', default=default_to_lang,
                       help='输出语言代码 (默认: zh)')
    
    # 添加纯净模式选项
    parser.add_argument('-p', '--pure', action='store_true',
                       help='纯净输出模式(只输出译文，适用于管道操作)')
    
    # 添加互斥的主要功能选项
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-h', '--help', action='store_true', help='显示帮助信息')
    group.add_argument('-w', '--words', nargs='+', help='单独翻译每个单词/短语')
    group.add_argument('-s', '--sentence', nargs='+', help='统一翻译整个句子/段落')
    group.add_argument('-f', '--file', help='翻译文件内容')
    
    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        print_help()
        return
    
    args = parser.parse_args()
    
    # 检查纯净模式是否与-s或-f同时使用
    if args.pure and not (args.sentence or args.file):
        print("错误: -p 纯净模式必须与 -s 或 -f 选项同时使用", file=sys.stderr)
        sys.exit(1)
    
    if args.help:
        print_help()
    elif args.words:
        # 单独翻译每个参数
        for i, word in enumerate(args.words):
            if not args.pure:
                print(f"[{i+1}/{len(args.words)}] 原文: {word}")
            result = translate_text(word, args.input_lang, args.output_lang)
            if result:
                if args.pure:
                    # 纯净模式下，每个译文单独一行
                    print(result)
                else:
                    print(f"译文: {result}")
            if not args.pure and i < len(args.words) - 1:  # 不是最后一个条目
                print("-" * 40)
    elif args.sentence:
        # 将所有参数合并为一个字符串进行翻译
        text = ' '.join(args.sentence)
        
        # 如果没有提供参数，尝试从标准输入读取
        if not text.strip() and not sys.stdin.isatty():
            text = sys.stdin.read().strip()
            
        if not text.strip():
            print("错误: 没有提供要翻译的文本", file=sys.stderr)
            sys.exit(1)
            
        if not args.pure:
            print(f"原文: {text}")
        result = translate_text(text, args.input_lang, args.output_lang)
        if result:
            if args.pure:
                # 纯净模式下只输出译文
                print(result)
            else:
                print(f"译文: {result}")
    elif args.file:
        # 读取文件内容并翻译
        file_path = args.file
        if not os.path.exists(file_path):
            print(f"错误: 文件 '{file_path}' 不存在", file=sys.stderr)
            sys.exit(1)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print("错误: 文件内容为空", file=sys.stderr)
                sys.exit(1)
                
            if not args.pure:
                print(f"文件: {file_path}")
                print(f"原文: {content}")
            result = translate_text(content, args.input_lang, args.output_lang)
            if result:
                if args.pure:
                    # 纯净模式下只输出译文
                    print(result)
                else:
                    print(f"译文: {result}")
                
        except Exception as e:
            print(f"读取文件失败: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
