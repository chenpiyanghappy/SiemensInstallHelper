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
        root.geometry("780x700")
        root.minsize(680, 560)

        self.watcher = None
        self.watching = False

        # 标题
        head = tk.Frame(root, bg="#2b5b9c")
        head.pack(fill="x")
        tk.Label(head, text="西门子安装助手", fg="white", bg="#2b5b9c",
                 font=("Microsoft YaHei", 15, "bold")).pack(pady=(10, 2))
        tk.Label(head, text="安装前清理 · 日志分析 · 授权检查 · 运行库检查 · 实时监控 · 安装前体检",
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

        # 第四行（v1.1：反馈/体检/复制）
        self.btn_basic = mk("⑫ 复制基础信息", lambda: self.run_task("basic-info"), "#7f8c8d", "#5f6a6b")
        self.btn_basic.grid(row=3, column=0, padx=4)
        self.btn_preflight = mk("⑬ 安装前体检", lambda: self.run_task("preflight", self._preflight_done), "#e69138", "#b06d1f")
        self.btn_preflight.grid(row=3, column=1, padx=4)
        self.btn_fb = mk("⑭ 复制反馈模板", lambda: self.run_task("feedback"), "#7f8c8d", "#5f6a6b")
        self.btn_fb.grid(row=3, column=2, padx=4)
        self.btn_issue = mk("⑮ 复制Issue模板", lambda: self.run_task("issue-template"), "#7f8c8d", "#5f6a6b")
        self.btn_issue.grid(row=3, column=3, padx=4)

        # 第五行（v1.1.1：知识小贴士）
        self.btn_tips = mk("⑯ 知识小贴士", self.open_tips, "#7f8c8d", "#5f6a6b")
        self.btn_tips.grid(row=4, column=0, padx=4, pady=(6, 0))

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
                        self.btn_find, self.btn_all, self.btn_basic,
                        self.btn_preflight, self.btn_fb, self.btn_issue,
                        self.btn_tips]

        self.write("欢迎使用西门子安装助手 v1.1")
        self.write("功能：清理进程 / 智能分析(能修自动修) / 授权检查 / 运行库检查下载安装 / 实时监控 / 离线报告 / 联网查错 / 寻找安装程序 / 安装前体检 / 一键复制基础信息、反馈模板、Issue模板 / 知识小贴士")
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
                    elif task == "basic-info":
                        si.copy_basic_info_block()
                    elif task == "feedback":
                        si.copy_feedback_block()
                    elif task == "issue-template":
                        si.copy_issue_template()
                    elif task == "preflight":
                        self._preflight_items = si.check_env_preflight()
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

    def _preflight_done(self):
        """体检完成后（主线程）弹窗汇总风险项。"""
        items = getattr(self, "_preflight_items", None) or []
        if not items:
            self.write("体检完成（无结果）。")
            return
        danger = [i for i in items if i[0] == "danger"]
        warn = [i for i in items if i[0] == "warn"]
        ok = [i for i in items if i[0] == "ok"]
        lines = []
        for level, name, state, advice in items:
            mark = {"ok": "✓", "warn": "⚠", "danger": "✗", "tip": "i"}.get(level, "·")
            lines.append("%s %s：%s" % (mark, name, state))
        msg = "\n".join(lines)
        if danger:
            msg += "\n\n❗ 有 %d 项必须处理（标 ✗ 项），处理完再安装更稳" % len(danger)
        elif warn:
            msg += "\n\n⚠ 有 %d 项建议关注（标 ⚠ 项）" % len(warn)
        else:
            msg += "\n\n✓ 全部通过，可以开始安装"
        self.write("体检完成：%d 项正常，%d 项提醒，%d 项风险。" % (len(ok), len(warn), len(danger)))
        messagebox.showinfo("安装前体检", msg)

    def _find_done(self):
        """扫描完成后（主线程）弹出选择窗口，供用户挑选要启动的安装程序。"""
        results = getattr(self, "_find_results", None) or []
        if not results:
            self.write("未找到安装包入口（Setup.exe / Start.exe 这类总入口）。")
            self.write("提示：把安装包解压到任意磁盘（含U盘/移动硬盘），ISO 镜像需先挂载；已安装到电脑里的程序不算安装包。")
            return
        self.write("请在弹出的窗口中选择要启动的安装程序：")

        win = tk.Toplevel(self.root)
        win.title("选择要启动的安装程序")
        win.geometry("680x400")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="扫描到的疑似安装程序（按匹配度排序；请优先选择 Start.exe / Setup.exe 且在安装包根目录的那个），双击或选中后点按钮启动：",
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

    def open_tips(self):
        """打开知识小贴士管理窗口。"""
        try:
            TipsWindow(self.root)
        except Exception as e:
            messagebox.showerror("小贴士", "打开小贴士窗口失败: %s" % e)

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


class TipsWindow:
    """知识小贴士管理窗口：浏览 / 搜索 / 新增 / 编辑 / 删除 / 恢复默认 / 导出贡献素材。

    普通用户友好：全部用图形界面操作，不碰源码；
    想贡献的同学：一键导出 PR 贡献素材（JSON + 说明文档）。
    """

    def __init__(self, master):
        from tips import TipsManager
        self.mgr = TipsManager()
        self._all = []
        self._tips = []

        self.win = tk.Toplevel(master)
        self.win.title("知识小贴士")
        self.win.geometry("660x500")
        self.win.minsize(600, 420)
        self.win.transient(master)

        head = tk.Frame(self.win, bg="#2b5b9c")
        head.pack(fill="x")
        tk.Label(head, text="知识小贴士", fg="white", bg="#2b5b9c",
                 font=("Microsoft YaHei", 12, "bold")).pack(pady=(8, 2))
        tk.Label(head, text="安装 / 环境 / 排障 · 内置贴士只读，★=你的自定义贴士（可增删改）",
                 fg="#cfe0f5", bg="#2b5b9c", font=("Microsoft YaHei", 9)).pack(pady=(0, 8))

        # 搜索栏
        bar = tk.Frame(self.win)
        bar.pack(fill="x", padx=10, pady=6)
        self.ent_search = tk.Entry(bar, font=("Microsoft YaHei", 10))
        self.ent_search.pack(side="left", fill="x", expand=True, ipady=2)
        self.ent_search.bind("<Return>", lambda e: self._do_search())
        tk.Button(bar, text="搜索", command=self._do_search,
                  bg="#2b5b9c", fg="white", width=8).pack(side="left", padx=6)
        tk.Button(bar, text="显示全部", command=self.refresh,
                  width=10).pack(side="left")

        # 中部：左列表 + 右详情
        mid = tk.Frame(self.win)
        mid.pack(fill="both", expand=True, padx=10, pady=4)

        self.lb = tk.Listbox(mid, font=("Microsoft YaHei", 10), activestyle="dotbox")
        self.lb.pack(side="left", fill="both", expand=True)
        self.lb.bind("<<ListboxSelect>>", self._on_select)
        self.lb.bind("<Double-Button-1>", lambda e: self._edit_selected())

        sb = tk.Scrollbar(mid, orient="vertical")
        sb.pack(side="left", fill="y")
        self.lb.config(yscrollcommand=sb.set)
        sb.config(command=self.lb.yview)

        self.detail = tk.Text(mid, font=("Microsoft YaHei", 10), wrap="word",
                              state="disabled", bg="#f8f9fa", width=32)
        self.detail.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # 底部操作按钮
        ops = tk.Frame(self.win)
        ops.pack(fill="x", padx=10, pady=8)
        for text, cmd, color in [
            ("＋ 新增贴士", self._add_tip, "#2fb344"),
            ("✎ 编辑", self._edit_selected, "#e69138"),
            ("－ 删除", self._delete_selected, "#d9534f"),
            ("↺ 恢复默认", self._restore_default, "#7f8c8d"),
            ("⇪ 导出贡献素材", self._export_contribution, "#2b5b9c"),
        ]:
            tk.Button(ops, text=text, command=cmd, bg=color, fg="white",
                      font=("Microsoft YaHei", 9)).pack(side="left", padx=3)
        tk.Button(ops, text="关闭", command=self.win.destroy,
                  font=("Microsoft YaHei", 9)).pack(side="right")

        self.status = tk.Label(self.win, text="就绪", anchor="w", fg="#555",
                               font=("Microsoft YaHei", 9))
        self.status.pack(fill="x", padx=12, pady=(0, 8))

        self.refresh()

    # ---------- 数据 ----------
    def _do_search(self):
        kw = self.ent_search.get().strip()
        self.refresh(self.mgr.search(kw) if kw else None)

    def refresh(self, data=None):
        """刷新列表；data 为 None 时显示全部。"""
        if data is None:
            self._tips = self.mgr.all_tips()
        else:
            self._tips = data
        self.lb.delete(0, "end")
        for t in self._tips:
            mark = "★" if t.get("source") == "user" else "·"
            self.lb.insert("end", "[%s] %s（%s）" % (mark, t.get("title"), t.get("category")))
        self._show_detail(None)
        self.status.config(text="共 %d 条贴士（内置 %d + 自定义 %d）"
                                % (len(self._tips),
                                   len(self.mgr.builtin_tips()),
                                   len(self.mgr.load_user_tips())))

    def _current(self):
        sel = self.lb.curselection()
        if not sel:
            return None
        return self._tips[sel[0]]

    # ---------- 详情 ----------
    def _on_select(self, _evt=None):
        self._show_detail(self._current())

    def _show_detail(self, tip):
        self.detail.config(state="normal")
        self.detail.delete("1.0", "end")
        if tip:
            src = "内置（只读）" if tip.get("source") == "builtin" else "我的自定义"
            lines = [
                "标题：%s" % tip.get("title"),
                "分类：%s" % tip.get("category"),
                "来源：%s" % src,
                "标签：%s" % ("、".join(tip.get("tags", [])) or "无"),
                "",
                "内容：",
                tip.get("content", ""),
                "",
            ]
            self.detail.insert("1.0", "\n".join(lines))
            self.detail.tag_add("title", "1.0", "1.end")
            self.detail.tag_configure("title", font=("Microsoft YaHei", 10, "bold"))
        self.detail.config(state="disabled")

    # ---------- 新增 / 编辑 ----------
    def _add_tip(self):
        self._edit_dialog(None)

    def _edit_selected(self):
        tip = self._current()
        if not tip:
            messagebox.showinfo("提示", "请先在列表中选择一条贴士", parent=self.win)
            return
        if tip.get("source") == "builtin":
            messagebox.showinfo("提示", "内置贴士是随版本发布的只读内容，不能修改。\n如需扩展，点『＋ 新增贴士』添加你自己的贴士。", parent=self.win)
            return
        self._edit_dialog(tip)

    def _edit_dialog(self, tip):
        """新增(tip=None)或编辑(tip=用户贴士)子窗口。"""
        dlg = tk.Toplevel(self.win)
        dlg.title("编辑小贴士" if tip else "新增小贴士")
        dlg.geometry("480x360")
        dlg.transient(self.win)
        dlg.grab_set()

        frm = tk.Frame(dlg)
        frm.pack(fill="both", expand=True, padx=12, pady=10)

        tk.Label(frm, text="标题 *", font=("Microsoft YaHei", 9)).pack(anchor="w")
        ent_title = tk.Entry(frm, font=("Microsoft YaHei", 10))
        ent_title.pack(fill="x", ipady=2, pady=(2, 6))
        if tip:
            ent_title.insert(0, tip.get("title", ""))

        tk.Label(frm, text="分类", font=("Microsoft YaHei", 9)).pack(anchor="w")
        from tips import TIPS_CATEGORIES
        var_cat = tk.StringVar(value=(tip.get("category") if tip else "安装"))
        opt = tk.OptionMenu(frm, var_cat, *TIPS_CATEGORIES)
        opt.config(font=("Microsoft YaHei", 9))
        opt.pack(anchor="w", pady=(2, 6))

        tk.Label(frm, text="内容 *", font=("Microsoft YaHei", 9)).pack(anchor="w")
        txt_content = tk.Text(frm, font=("Microsoft YaHei", 10), height=7, wrap="word")
        txt_content.pack(fill="both", expand=True, pady=(2, 6))
        if tip:
            txt_content.insert("1.0", tip.get("content", ""))

        tk.Label(frm, text="标签（逗号分隔，可选）", font=("Microsoft YaHei", 9)).pack(anchor="w")
        ent_tags = tk.Entry(frm, font=("Microsoft YaHei", 10))
        ent_tags.pack(fill="x", ipady=2, pady=(2, 6))
        if tip:
            ent_tags.insert(0, "，".join(tip.get("tags", [])))

        def save():
            title = ent_title.get().strip()
            content = txt_content.get("1.0", "end").strip()
            if not title or not content:
                messagebox.showwarning("提示", "标题和内容不能为空", parent=dlg)
                return
            if tip:
                ok, msg = self.mgr.update_tip(tip["id"], title=title, content=content,
                                              category=var_cat.get(), tags=ent_tags.get())
            else:
                ok, msg = self.mgr.add_tip(title, content, var_cat.get(), ent_tags.get())
            if ok:
                dlg.destroy()
                self.refresh()
                self.status.config(text=msg)
            else:
                messagebox.showerror("保存失败", msg, parent=dlg)

        btns = tk.Frame(dlg)
        btns.pack(fill="x", padx=12, pady=(0, 10))
        tk.Button(btns, text="保存", command=save, bg="#2fb344", fg="white",
                  font=("Microsoft YaHei", 10)).pack(side="right")
        tk.Button(btns, text="取消", command=dlg.destroy,
                  font=("Microsoft YaHei", 10)).pack(side="right", padx=8)

    # ---------- 删除 / 恢复默认 ----------
    def _delete_selected(self):
        tip = self._current()
        if not tip:
            messagebox.showinfo("提示", "请先在列表中选择一条贴士", parent=self.win)
            return
        if tip.get("source") == "builtin":
            messagebox.showinfo("提示", "内置贴士不可删除", parent=self.win)
            return
        if messagebox.askyesno("确认删除", "确定删除贴士「%s」吗？" % tip.get("title"), parent=self.win):
            ok, msg = self.mgr.delete_tip(tip["id"])
            self.status.config(text=msg)
            self.refresh()

    def _restore_default(self):
        if not self.mgr.load_user_tips():
            messagebox.showinfo("提示", "当前没有自定义贴士，无需恢复", parent=self.win)
            return
        if messagebox.askyesno("恢复默认", "将清空全部自定义贴士（仅保留内置贴士），确定吗？", parent=self.win):
            ok, msg = self.mgr.restore_default()
            self.status.config(text=msg)
            self.refresh()

    # ---------- 导出贡献素材 ----------
    def _export_contribution(self):
        ok, msg, out_dir = self.mgr.export_contribution()
        if ok:
            self.status.config(text=msg)
            messagebox.showinfo("导出成功",
                                "%s\n\n已生成：\n  tips_contribution.json\n  CONTRIBUTING_TIPS.md\n\n"
                                "自学 Git 后按说明文档即可向仓库提交（详见文档）。" % msg,
                                parent=self.win)
        else:
            messagebox.showinfo("导出提示", msg, parent=self.win)


def run_gui():
    enable_hi_dpi()
    root = tk.Tk()
    SiemensInstallGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
