#!/usr/bin/env python3
"""
项目清理脚本
用于清理缓存文件和临时文件
"""

import os
import shutil
import glob

def clean_pycache():
    """清理Python缓存文件"""
    print("🧹 清理Python缓存文件...")
    
    # 查找所有__pycache__目录
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"删除: {pycache_path}")
            shutil.rmtree(pycache_path)
    
    # 删除.pyc文件
    pyc_files = glob.glob('**/*.pyc', recursive=True)
    for pyc_file in pyc_files:
        print(f"删除: {pyc_file}")
        os.remove(pyc_file)

def clean_logs():
    """清理日志文件"""
    print("🧹 清理日志文件...")
    
    log_patterns = [
        'logs/*.log',
        'backend/logs/*.log',
        'backend/app/logs/*.log',
        '*.log'
    ]
    
    for pattern in log_patterns:
        log_files = glob.glob(pattern, recursive=True)
        for log_file in log_files:
            print(f"清空日志: {log_file}")
            with open(log_file, 'w') as f:
                f.write("")

def clean_temp_dirs():
    """清理临时目录"""
    print("🧹 清理临时目录...")
    
    temp_dirs = [
        'backend/temp',
        'backend/cache',
        'temp'
    ]
    
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            print(f"清理目录: {temp_dir}")
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

def main():
    """主函数"""
    print("🚀 开始项目清理...")
    
    clean_pycache()
    clean_logs()
    clean_temp_dirs()
    
    print("✅ 项目清理完成！")

if __name__ == "__main__":
    main()
