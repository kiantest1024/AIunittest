#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI单元测试生成工具 - 图形用户界面

此文件提供了一个基于Tkinter的图形用户界面，用于:
1. 选择Python文件或输入Python代码
2. 选择AI模型
3. 生成单元测试
4. 保存测试到指定目录
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pathlib
import threading

# 尝试导入配置和函数
try:
    from config import (
        GENERATED_TESTS_DIR,
        AI_MODELS,
        TEST_CONFIG
    )
    from initial import (
        parse_python_file,
        generate_tests_with_ai,
        save_generated_test
    )
except ImportError as e:
    print(f"错误: 无法导入必要的模块或配置: {e}", file=sys.stderr)
    sys.exit(1)

class AITestGeneratorGUI:
    """AI单元测试生成工具的图形用户界面"""

    def __init__(self, root):
        """初始化GUI"""
        self.root = root
        self.root.title("AI单元测试生成工具")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)

        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))

        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建顶部控制区域
        self.create_control_area()

        # 创建代码和测试区域
        self.create_code_test_area()

        # 创建状态栏
        self.create_status_bar()

        # 初始化变量
        self.current_file = None
        self.code_snippets = []
        self.selected_snippet_index = None
        self.generated_test_code = None

        # 更新状态
        self.update_status("就绪")

    def create_control_area(self):
        """创建顶部控制区域"""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        # 文件选择区域
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Label(file_frame, text="Python文件:").pack(side=tk.LEFT, padx=5)

        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50)
        file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_button = ttk.Button(file_frame, text="浏览...", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=5)

        load_button = ttk.Button(file_frame, text="加载文件", command=self.load_file)
        load_button.pack(side=tk.LEFT, padx=5)

        # 模型选择区域
        model_frame = ttk.Frame(control_frame)
        model_frame.pack(fill=tk.X, pady=5)

        ttk.Label(model_frame, text="AI模型:").pack(side=tk.LEFT, padx=5)

        self.model_var = tk.StringVar(value=AI_MODELS["current_model"])
        model_dropdown = ttk.Combobox(model_frame, textvariable=self.model_var,
                                      values=list(AI_MODELS["models"].keys()),
                                      state="readonly", width=20)
        model_dropdown.pack(side=tk.LEFT, padx=5)

        # 目标目录选择区域
        dir_frame = ttk.Frame(control_frame)
        dir_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dir_frame, text="保存目录:").pack(side=tk.LEFT, padx=5)

        self.save_dir_var = tk.StringVar(value=str(GENERATED_TESTS_DIR))
        dir_entry = ttk.Entry(dir_frame, textvariable=self.save_dir_var, width=50)
        dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_dir_button = ttk.Button(dir_frame, text="浏览...", command=self.browse_directory)
        browse_dir_button.pack(side=tk.LEFT, padx=5)

    def create_code_test_area(self):
        """创建代码和测试区域"""
        # 创建水平分割的窗格
        paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=5)

        # 左侧代码区域
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=1)

        # 代码片段选择区域
        snippet_frame = ttk.Frame(left_frame)
        snippet_frame.pack(fill=tk.X, pady=5)

        ttk.Label(snippet_frame, text="代码片段:", style="Header.TLabel").pack(side=tk.LEFT, padx=5)

        self.snippet_var = tk.StringVar()
        self.snippet_dropdown = ttk.Combobox(snippet_frame, textvariable=self.snippet_var,
                                            state="readonly", width=40)
        self.snippet_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.snippet_dropdown.bind("<<ComboboxSelected>>", self.on_snippet_selected)

        # 代码显示区域
        code_frame = ttk.Frame(left_frame)
        code_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(code_frame, text="源代码:", style="Header.TLabel").pack(anchor=tk.W, padx=5)

        self.code_text = scrolledtext.ScrolledText(code_frame, wrap=tk.WORD, width=50, height=20)
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 右侧测试区域
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)

        # 测试生成按钮
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.generate_button = ttk.Button(button_frame, text="生成测试", command=self.generate_test)
        self.generate_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(button_frame, text="保存测试", command=self.save_test)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.save_button.config(state=tk.DISABLED)

        # 测试显示区域
        test_frame = ttk.Frame(right_frame)
        test_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(test_frame, text="生成的测试:", style="Header.TLabel").pack(anchor=tk.W, padx=5)

        self.test_text = scrolledtext.ScrolledText(test_frame, wrap=tk.WORD, width=50, height=20)
        self.test_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(2, 2, 2, 2))
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar()
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(fill=tk.X)

    def update_status(self, message):
        """更新状态栏消息"""
        self.status_var.set(message)
        self.root.update_idletasks()

    def browse_file(self):
        """浏览并选择Python文件"""
        file_path = filedialog.askopenfilename(
            title="选择Python文件",
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)

    def browse_directory(self):
        """浏览并选择保存目录"""
        dir_path = filedialog.askdirectory(
            title="选择保存目录"
        )
        if dir_path:
            self.save_dir_var.set(dir_path)

    def load_file(self):
        """加载Python文件并解析代码片段"""
        file_path = self.file_path_var.get().strip()
        if not file_path:
            messagebox.showerror("错误", "请选择一个Python文件")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return

        try:
            self.update_status(f"正在解析文件: {file_path}")
            self.current_file = file_path
            self.code_snippets = parse_python_file(file_path)

            if not self.code_snippets:
                messagebox.showinfo("信息", "未在文件中找到函数或方法")
                self.update_status("未找到代码片段")
                return

            # 更新下拉菜单
            snippet_names = []
            for snippet in self.code_snippets:
                if snippet['type'] == 'function':
                    snippet_names.append(f"函数: {snippet['name']}")
                else:
                    snippet_names.append(f"方法: {snippet['class_name']}.{snippet['name']}")

            self.snippet_dropdown['values'] = snippet_names
            self.snippet_dropdown.current(0)
            self.on_snippet_selected(None)

            self.update_status(f"已加载 {len(self.code_snippets)} 个代码片段")

        except Exception as e:
            messagebox.showerror("错误", f"解析文件时出错: {e}")
            self.update_status("文件解析失败")

    def on_snippet_selected(self, _):
        """当选择代码片段时更新显示"""
        if not self.code_snippets:
            return

        index = self.snippet_dropdown.current()
        if index < 0 or index >= len(self.code_snippets):
            return

        self.selected_snippet_index = index
        snippet = self.code_snippets[index]

        # 显示代码
        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(tk.END, snippet['code'])

        # 清除测试区域
        self.test_text.delete(1.0, tk.END)
        self.generated_test_code = None
        self.save_button.config(state=tk.DISABLED)

        # 更新状态
        if snippet['type'] == 'function':
            self.update_status(f"已选择函数: {snippet['name']}")
        else:
            self.update_status(f"已选择方法: {snippet['class_name']}.{snippet['name']}")

    def generate_test(self):
        """生成所选代码片段的测试"""
        if self.selected_snippet_index is None or not self.code_snippets:
            messagebox.showerror("错误", "请先选择一个代码片段")
            return

        snippet = self.code_snippets[self.selected_snippet_index]
        model_name = self.model_var.get()

        # 禁用按钮，防止重复点击
        self.generate_button.config(state=tk.DISABLED)
        self.update_status(f"正在使用 {model_name} 生成测试...")

        # 在后台线程中生成测试，避免UI冻结
        def generate_in_thread():
            try:
                test_code = generate_tests_with_ai(snippet, model_name)

                # 在主线程中更新UI
                self.root.after(0, lambda: self.update_test_result(test_code))
            except Exception as e:
                self.root.after(0, lambda: self.show_generation_error(str(e)))

        threading.Thread(target=generate_in_thread, daemon=True).start()

    def update_test_result(self, test_code):
        """更新测试结果"""
        self.generate_button.config(state=tk.NORMAL)

        if test_code:
            self.test_text.delete(1.0, tk.END)
            self.test_text.insert(tk.END, test_code)
            self.generated_test_code = test_code
            self.save_button.config(state=tk.NORMAL)
            self.update_status("测试生成成功")
        else:
            messagebox.showerror("错误", "生成测试失败")
            self.update_status("测试生成失败")

    def show_generation_error(self, error_message):
        """显示生成测试时的错误"""
        self.generate_button.config(state=tk.NORMAL)
        messagebox.showerror("错误", f"生成测试时出错: {error_message}")
        self.update_status("测试生成失败")

    def save_test(self):
        """保存生成的测试到指定目录"""
        if not self.generated_test_code or self.selected_snippet_index is None:
            messagebox.showerror("错误", "没有可保存的测试代码")
            return

        save_dir = self.save_dir_var.get().strip()
        if not save_dir:
            messagebox.showerror("错误", "请指定保存目录")
            return

        # 创建保存目录
        try:
            save_dir_path = pathlib.Path(save_dir)
            save_dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("错误", f"创建目录失败: {e}")
            return

        # 保存测试
        try:
            snippet = self.code_snippets[self.selected_snippet_index]

            # 临时修改全局变量GENERATED_TESTS_DIR
            global GENERATED_TESTS_DIR
            original_dir = GENERATED_TESTS_DIR
            GENERATED_TESTS_DIR = save_dir_path

            save_generated_test(self.current_file, snippet, self.generated_test_code)

            # 恢复全局变量
            GENERATED_TESTS_DIR = original_dir

            # 构建保存的文件路径用于显示
            original_file_name = pathlib.Path(self.current_file).stem
            snippet_name = snippet['name']
            class_name = snippet['class_name']
            test_file_name = f"{TEST_CONFIG['test_file_prefix']}{original_file_name}_{class_name or ''}{'_' if class_name else ''}{snippet_name}.py"
            test_file_path = save_dir_path / test_file_name

            messagebox.showinfo("成功", f"测试已保存到:\n{test_file_path}")
            self.update_status(f"测试已保存到: {test_file_path}")

        except Exception as e:
            messagebox.showerror("错误", f"保存测试失败: {e}")
            self.update_status("保存测试失败")


def main():
    """主函数"""
    root = tk.Tk()
    # 创建应用实例并启动主循环
    AITestGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
