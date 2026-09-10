#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西门子专业软件 安装助手 · 图形界面
==================================
依赖: Python 自带 tkinter，无需安装第三方库。
高分屏适配已内置（窗口按真实 DPI 渲染，字体不发虚）。
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox


def enable_hi_dpi():
    """高分屏适配：必须在创建窗口(Tk)之前调用。"""
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    except Exception:
        pass


class SiemensInstallGUI:
    def __init__(self, root):
        self.root = root
        root.title("西门子安装助手 SiemensInstallHelper")
        root.geometry("760x600")
        root.minsize(640, 460)

        self.watcher = None
        self.watching = False

        # 标题
        head = tk.Frame(root, bg="#2b5b9c")
        head.pack(fill="x")
        tk.Label(head, text="西门子安装助手", fg="white", bg="#2b5b9c",
                 font=("Microsoft YaHei", 15, "bold")).pack(pady=(10, 2))
        tk.Label(head, text="安装前清理 · 日志分析 · 授权检查 · 运行库检查 · 实时监控",
                 fg="#cfe0f5", bg="#2b5b9c", font=("Microsoft YaHei", 9)).pack(pady=(0, 10))

        # 按钮区
        btns = tk.Frame(root)
        btns.pack(fill="x", padx=10, pady=8)

        def mk(text, cmd, color, active):
            return tk.Button(btns, text=text, width=13, command=cmd,
                             bg=color, fg="white", activebackground=active)

        # 第一行
        self.btn_clean = mk("① 清理进程", lambda: self.run_task("clean"), "#3d7edb", "#2b5b9c")
        self.btn_clean.grid(row=0, column=0, padx=4)
        self.btn_log = mk("② 智能分析", lambda: self.run_task("log"), "#3d7edb", "#2b5b9c")
        self.btn_log.grid(row=0, column=1, padx=4)
        self.btn_lic = mk("③ 检查授权", lambda: self.run_task("license"), "#3d7edb", "#2b5b9c")
        self.btn_lic.grid(row=0, column=2, padx=4)
        self.btn_rt = mk("④ 运行库检查", lambda: self.run_task("runtime"), "#3d7edb", "#2b5b9c")
        self.btn_rt.grid(row=0, column=3, padx=4)

        # 第二行
        self.btn_watch = mk("⑤ 实时监控", self.toggle_watch, "#e69138", "#b06d1f")
        self.btn_watch.grid(row=1, column=0, padx=4)
        self.btn_dl = mk("⑥ 下载运行库", lambda: self.run_task("download", self._dl_done), "#e69138", "#b06d1f")
        self.btn_dl.grid(row=1, column=1, padx=4)
        self.btn_inst = mk("⑦ 安装运行库", self.install_runtime_ask, "#e69138", "#b06d1f")
        self.btn_inst.grid(row=1, column=2, padx=4)
        self.btn_rep = mk("⑧ 导出报错报告", lambda: self.run_task("report"), "#7f8c8d", "#5f6a6b")
        self.btn_rep.grid(row=1, column=3, padx=4)

        # 第三行
        self.btn_search = mk("⑨ 联网查错", lambda: self.run_task("search"), "#52a75c", "#3d7e46")
        self.btn_search.grid(row=2, column=0, padx=4)
        self.btn_find = mk("⑪ 寻找安装程序", lambda: self.run_task("find", self._find_done), "#52a75c", "#3d7e46")
        self.btn_find.grid(row=2, column=1, padx=4)
        self.btn_all = mk("⑩ 全部执行", lambda: self.run_all(), "#52a75c", "#3d7e46")
        self.btn_all.grid(row=2, column=2, columnspan=2, sticky="we", padx=4, pady=(6, 0))

        # 提示
        tk.Label(root, text="提示: ① 会结束浏览器/聊天/网盘等第三方进程，正在编辑的文档请先保存；系统与杀毒绝不碰",
                 fg="#666", font=("Microsoft YaHei", 8)).pack(anchor="w", padx=12)

        # 输出区
        self.out = scrolledtext.ScrolledText(root, wrap="word", font=("Consolas", 9),
                                             state="disabled", bg="#f8f9fa")
        self.out.pack(fill="both", expand=True, padx=10, pady=8)

        # 状态栏
        self.status = tk.Label(root, text="就绪", anchor="w", fg="#555",
                               font=("Microsoft YaHei", 9))
        self.status.pack(fill="x", padx=12, pady=(0, 8))

        self.buttons = [self.btn_clean, self.btn_log, self.btn_lic,
                        self.btn_rt, self.btn_watch, self.btn_dl,
                        self.btn_inst, self.btn_rep, self.btn_search,
                        self.btn_find, self.btn_all]

        self.write("欢迎使用西门子安装助手")
        self.write("功能：清理进程 / 智能分析(能修自动修) / 授权检查 / 运行库检查下载安装 / 实时监控 / 离线报告 / 联网查错 / 寻找安装程序")
        self.write("注意：本工具只清理第三方进程和只读分析，不修改系统设置，可放心使用。")

        # 防误报提醒：检测常见杀软，若在运行则提示（本工具为免安装单文件，可能被误报）
        try:
            import siemens_install as _si
            sec = _si.check_security_software()
            if sec:
                names = "、".join(sec)
                self.write("检测到运行中的安全软件：%s（本工具为绿色单文件，可能被其误报）" % names)
                messagebox.showwarning(
                    "防误报提醒",
                    "检测到正在运行：%s\n\n"
                    "本工具是免安装的绿色单文件（无数字签名），个别杀毒软件可能误报拦截。\n\n"
                    "如果工具被拦截/无法启动，请按顺序尝试：\n"
                    "  ① 在杀毒软件中把本工具『添加信任/白名单』（推荐，最安全）\n"
                    "  ② 或临时退出杀软后运行（装完记得重新开启）\n\n"
                    "点『确定』继续使用。" % names)
        except Exception:
            pass

    # ---------- 输出 ----------
    def write(self, text):
        self.out.config(state="normal")
        self.out.insert("end", text + "\n")
        self.out.see("end")
        self.out.config(state="disabled")

    def set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for b in self.buttons:
            b.config(state=state)
        self.status.config(text="运行中..." if busy else "就绪")
        self.root.update_idletasks()

    # ---------- 任务执行 ----------
    def run_task(self, task, callback=None):
        self.set_busy(True)
        self.write("\n" + "─" * 60)
        self.write("执行: %s" % task)
        self.write("─" * 60)

        def worker():
            import io
            import contextlib
            try:
                import siemens_install as si
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    if task == "clean":
                        si.clean_processes(confirm_callback=self._confirm_clean_sync)
                    elif task == "log":
                        si.analyze_and_fix()
                    elif task == "license":
                        si.check_license()
                    elif task == "runtime":
                        si.check_runtime()
                    elif task == "download":
                        si.download_runtime(progress_cb=self._dl_progress)
                    elif task == "install-runtime":
                        si.install_runtime()
                    elif task == "report":
                        si.export_report()
                    elif task == "search":
                        si.open_help_page()
                    elif task == "find":
                        self._find_results = si.find_installers()
                        self._find_ready = True
                for line in buf.getvalue().splitlines():
                    self.root.after(0, self.write, line)
            except Exception as e:
                self.root.after(0, self.write, "执行异常: %s" % e)
            finally:
                self.root.after(0, self.set_busy, False)
                if callback:
                    self.root.after(0, callback)

        threading.Thread(target=worker, daemon=True).start()

    def _dl_progress(self, name, done, total):
        """下载进度回调（工作线程调用，用 after 转回主线程）。"""
        if done < 0:
            self.root.after(0, self.write, "  ✓ 已存在: " + name)
            return
        if total > 0:
            pct = done * 100 // total
            mb_d = done // (1024 * 1024)
            mb_t = total // (1024 * 1024)
            self.root.after(0, self.status.config, {"text": "下载中 %s: %d%% (%d/%d MB)" % (name, pct, mb_d, mb_t)})
        else:
            self.root.after(0, self.status.config, {"text": "下载中 %s: %d MB..." % (name, done // (1024 * 1024))})

    def _dl_done(self):
        self.write("下载完成。可点『⑦ 安装运行库』静默安装（会弹 UAC 确认）。")

    def _find_done(self):
        """扫描完成后（主线程）弹出选择窗口，供用户挑选要启动的安装程序。"""
        results = getattr(self, "_find_results", None) or []
        if not results:
            self.write("未找到疑似西门子安装程序。")
            self.write("提示：把安装包放到任意磁盘（含U盘/移动硬盘/光盘），再点『⑪ 寻找安装程序』。")
            return
        self.write("请在弹出的窗口中选择要启动的安装程序：")

        win = tk.Toplevel(self.root)
        win.title("选择要启动的安装程序")
        win.geometry("680x400")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="扫描到的疑似安装程序（按匹配度排序），双击或选中后点按钮启动：",
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=10, pady=(10, 4))

        lb = tk.Listbox(win, font=("Consolas", 10))
        lb.pack(fill="both", expand=True, padx=10, pady=4)
        for _score, path in results:
            lb.insert("end", path)
        lb.bind("<Double-Button-1>", lambda e: self._launch_selected(lb, results, win))

        def do_launch():
            self._launch_selected(lb, results, win)
        tk.Button(win, text="启动选中的安装程序（提权，会弹UAC）",
                  command=do_launch, bg="#2b5b9c", fg="white",
                  font=("Microsoft YaHei", 10)).pack(pady=(4, 10))
        tk.Button(win, text="取消", command=win.destroy).pack(pady=(0, 10))

    def _launch_selected(self, lb, results, win):
        sel = lb.curselection()
        if not sel:
            messagebox.showinfo("提示", "请先选中一个安装程序", parent=win)
            return
        path = results[sel[0]][1]
        win.destroy()
        self.write("\n" + "─" * 60)
        self.write("启动安装程序: %s" % path)
        self.write("─" * 60)
        import siemens_install as si
        ok = si.launch_installer(path)
        if not ok:
            self.write("启动失败，请手动右键该程序 → 以管理员身份运行。")

    def install_runtime_ask(self):
        import os
        import siemens_install as si
        found = []
        if os.path.isdir(si.RUNTIME_DIR):
            for item in si.RUNTIME_DOWNLOADS:
                name, rtype, url, fname, args = item
                if rtype == "download" and os.path.exists(os.path.join(si.RUNTIME_DIR, fname)):
                    found.append(name)
        if not found:
            messagebox.showinfo("提示", "还没有下载可安装的运行库。\n请先点『⑥ 下载运行库』。")
            return
        ok = messagebox.askyesno(
            "安装运行库",
            "将静默安装以下运行库（需要管理员权限，会弹 UAC）：\n\n%s\n\n继续吗？" % "\n".join(found))
        if ok:
            self.write("\n" + "─" * 60)
            self.write("执行: 安装运行库（提权后自动静默安装）")
            self.write("─" * 60)
            import siemens_install as _si
            if _si.is_admin():
                self.run_task("install-runtime")
            else:
                _si.relaunch_as_admin("install-runtime")
                self.write("已请求管理员权限。请在 UAC 弹窗点“是”，安装结果请看 siemens_install.log。")

    def _confirm_clean_sync(self, targets):
        """清理确认：把弹窗请求转到主线程，并同步等待用户选择。

        （Tkinter 非线程安全，禁止在工作线程直接调 messagebox。）
        """
        ev = threading.Event()
        result = {}

        def ask():
            try:
                result["ok"] = self._confirm_clean(targets)
            except Exception:
                result["ok"] = False
            finally:
                ev.set()

        self.root.after(0, ask)
        ev.wait(timeout=300)
        return result.get("ok", False)

    def _confirm_clean(self, targets):
        """清理前的确认弹窗（在主线程显示）。"""
        names = "、".join(sorted(set(n for _, n in targets))[:10])
        more = "" if len(set(n for _, n in targets)) <= 10 else " 等"
        return messagebox.askyesno(
            "确认清理",
            "将结束以下第三方进程（系统与杀毒绝不碰）：\n\n%s%s\n\n正在编辑的文档请先保存！\n确定继续吗？" % (names, more))

    def run_all(self):
        self.write("\n" + "=" * 60)
        self.write("全部执行: 运行库检查 → 授权检查 → 清理进程")
        self.write("=" * 60)
        self.run_task("runtime", callback=lambda: self.run_task("license", callback=lambda: self.run_task("clean")))

    # ---------- 实时监控 ----------
    def toggle_watch(self):
        if self.watching:
            self.watching = False
            self.btn_watch.config(text="⑤ 实时监控")
            self.write("\n已停止监控。")
            return
        import siemens_install as si
        self.watcher = si.InstallWatcher()
        self.watcher.reset()
        self.watching = True
        self.btn_watch.config(text="⑤ 停止监控")
        if self.watcher.path:
            self.write("\n[监控已启动] 盯着日志: %s" % self.watcher.path)
        else:
            self.write("\n[监控已启动] 尚未找到安装日志，开始安装后会自动识别")
        self.write("发现错误会立即提示并给出建议。装完后点“⑤ 停止监控”。")
        self._poll_watch()

    def _poll_watch(self):
        if not self.watching:
            return
        try:
            hits = self.watcher.poll()
            for h in hits:
                self.write(h)
        except Exception as e:
            self.write("监控异常: %s" % e)
        self.root.after(5000, self._poll_watch)


def run_gui():
    enable_hi_dpi()
    root = tk.Tk()
    SiemensInstallGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
