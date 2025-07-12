#! /usr/bin/env python3

import os
import argparse
from PIL import Image
import sys

def convert_images_to_webp(directory, quality, delete_source):
    """
    将指定目录中的 PNG 图片批量转换为 WebP 格式。

    :param directory: 目标目录
    :param quality: WebP 压缩质量 (0-100)
    :param delete_source: 是否删除源文件
    """
    # 确保目标目录真实存在
    if not os.path.isdir(directory):
        print(f"错误：目录 '{directory}' 不存在或不是一个有效的目录。")
        sys.exit(1)

    # 打印将要执行的操作
    print("--- 开始图片转换任务 ---")
    print(f"目标目录: {os.path.abspath(directory)}")
    print(f"压缩质量: {quality}")
    print(f"删除源文件: {'是' if delete_source else '否'}")
    if delete_source:
        print("\n警告：已启用源文件删除功能。转换成功后，原始 PNG 文件将被永久删除。\n")
    print("-" * 28)

    # 遍历目录中的所有文件
    found_png = False
    for filename in os.listdir(directory):
        # 检查文件是否以 .png 结尾（不区分大小写）
        if filename.lower().endswith('.png'):
            found_png = True
            png_path = os.path.join(directory, filename)
            # 生成 .webp 文件名
            webp_path = os.path.splitext(png_path)[0] + '.webp'

            try:
                # 打开 PNG 图片
                with Image.open(png_path) as img:
                    # 转换并保存为 WebP
                    # RGBA 模式的 PNG 会被正确处理
                    img.save(webp_path, 'webp', quality=quality)
                
                print(f"✓ 成功: {filename}  ->  {os.path.basename(webp_path)}")

                # 如果设置了删除标志，则删除原始 PNG 文件
                if delete_source:
                    os.remove(png_path)
                    print(f"  └─ 已删除源文件: {filename}")

            except Exception as e:
                print(f"✗ 失败: {filename} | 错误: {e}")
    
    if not found_png:
        print("未在目标目录中找到任何 PNG 文件。")

    print("\n--- 任务完成 ---")


if __name__ == "__main__":
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(
        description="一个用于将 PNG 图片批量转换为 WebP 格式的脚本，可用于优化博客图片。",
        formatter_class=argparse.RawTextHelpFormatter  # 美化 help 信息格式
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='要处理的图片目录路径。\n(默认: 当前目录)'
    )

    parser.add_argument(
        '-q', '--quality',
        type=int,
        default=80,
        metavar='[0-100]',
        help='WebP 的压缩质量 (范围: 0-100)。\n数值越小，文件越小，但画质越低。\n(默认: 80, 这是一个在质量和大小之间很好的平衡点)'
    )

    parser.add_argument(
        '-d', '--delete',
        action='store_true',
        help='转换成功后删除原始的 PNG 文件。\n!!! 这是一个危险操作，请在确认备份或不再需要源文件时使用。'
    )

    args = parser.parse_args()

    # 执行转换函数
    convert_images_to_webp(args.directory, args.quality, args.delete)