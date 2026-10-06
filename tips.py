#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识小贴士体系（Knowledge Tips）
================================
双文件架构：
  - tips.json        官方内置贴士（随版本发布，只读，程序不修改）
  - user_tips.json   用户自定义贴士（图形界面增删改查，仅本地生效，不碰源码）

高阶能力：
  - export_contribution() 一键导出「用户自定义贴士」为 PR 贡献素材
    （JSON 片段 + 提交说明文档），供自学 Git 后向仓库提交。

与 siemens_install.py 解耦：本模块可独立导入、独立测试、独立打包。
"""

import os
import sys
import json
import datetime

TIPS_FILE = "tips.json"            # 官方内置（只读）
USER_TIPS_FILE = "user_tips.json"  # 用户自定义（可读写）

# 贴士分类（与 FEATURE_PLAN 5.1 知识库分类风格一致）
TIPS_CATEGORIES = ["安装", "环境", "排障", "工程", "学习"]

# ---------------------------------------------------------------------
# 官方内置贴士（只读，随版本发布）
# 注意：内置贴士不能增删改，只能通过 user_tips.json 扩展
# ---------------------------------------------------------------------
TIPS_BUILTIN = [
    {
        "id": 1,
        "title": "安装路径建议：别带中文和空格",
        "content": "TIA Portal 建议安装到纯英文路径（如 D:\\TIA_Portal\\V20）。"
                   "路径含中文、空格或特殊符号可能引发组件安装失败；"
                   "很多同学的失败案例都出在这。",
        "category": "安装",
        "tags": ["路径", "安装", "失败"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
    {
        "id": 2,
        "title": "安装顺序：先基础包，后选件",
        "content": "用安装包根目录的 Start.exe / Setup.exe 总入口安装，"
                   "先装基础包，再单独安装选件（如 WinCC、PLCSIM）。"
                   "跳步安装容易触发组件依赖报错。",
        "category": "安装",
        "tags": ["顺序", "Start.exe", "组件"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
    {
        "id": 3,
        "title": "U 盘解压安装包容易损坏",
        "content": "压缩包在 U 盘上直接解压容易出错（慢且容易中断），"
                   "报错 0x80070570「文件或目录损坏」时，"
                   "先把压缩包拷到本地磁盘再解压，解压后核对文件大小。",
        "category": "安装",
        "tags": ["U盘", "解压", "损坏", "0x80070570"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
    {
        "id": 4,
        "title": "杀软白名单：绿色单文件可能被误报",
        "content": "本工具是免安装单文件（无数字签名），个别杀毒软件可能误报拦截。"
                   "安装 TIA 时也可能被拦截组件进程，建议安装前把安装包目录加入杀软信任区，"
                   "或临时退出杀软（装完记得恢复）。",
        "category": "环境",
        "tags": ["杀软", "白名单", "误报", "拦截"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
    {
        "id": 5,
        "title": "磁盘空间：C 盘至少留 20~30GB",
        "content": "TIA Portal 完整安装占用较大（20GB 起步），"
                   "且安装过程会在 C 盘写临时文件。"
                   "安装前确认 C 盘剩余空间足够，报错 0x80070070 就是空间不足。",
        "category": "环境",
        "tags": ["磁盘", "空间", "0x80070070"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
    {
        "id": 6,
        "title": ".NET Framework 3.5 需要手动启用",
        "content": "TIA 部分组件依赖 .NET Framework 3.5（Win10/11 默认不启用）。"
                   "控制面板 → 程序 → 启用或关闭 Windows 功能 → "
                   "勾选「.NET Framework 3.5（包括 2.0 和 3.0）」→ 确定。",
        "category": "环境",
        "tags": [".NET", "3.5", "功能", "0x800F0900"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
    {
        "id": 7,
        "title": "VC++ 运行库新旧版本冲突",
        "content": "VC++ 2015-2022 运行库是 TIA 的常见依赖，旧版本残留可能导致组件失败"
                   "（报错 1925 / 1935）。可先装最新的 VC++ 运行库，再重试安装。",
        "category": "环境",
        "tags": ["VC++", "运行库", "1925", "1935"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
    {
        "id": 8,
        "title": "安装日志在哪？SIA_*.log",
        "content": "TIA 安装日志一般在 %TEMP%\\SIA_*.log 和 C:\\Windows\\Temp 下。"
                   "报错时把日志一并提交，能大幅提高排查效率——"
                   "这也是本工具「智能分析日志」和「导出报错报告」做的事。",
        "category": "排障",
        "tags": ["日志", "SIA", "排障"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
    {
        "id": 9,
        "title": "待重启标记会让安装直接失败",
        "content": "系统有「待重启」残留标记时，安装程序可能直接报错。"
                   "重启电脑即可解决；本工具的「安装前体检」会自动检测这个标记。",
        "category": "排障",
        "tags": ["重启", "待重启", "体检"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
    {
        "id": 10,
        "title": "授权服务 ALM 异常：先查服务",
        "content": "Automation License Manager（almservice）不启动会导致授权类报错。"
                   "可先运行本工具「检查授权」自动启动；"
                   "若仍异常，打开 services.msc 确认 almservice 为自动并启动。",
        "category": "排障",
        "tags": ["授权", "ALM", "服务", "license"],
        "source": "builtin",
        "created_at": "2026-10-06",
    },
]


class TipsManager:
    """小贴士管理器：内置只读 + 用户自定义读写。"""

    def __init__(self, base_dir=None):
        if base_dir is None:
            if getattr(sys, "frozen", False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = base_dir
        self.tips_path = os.path.join(base_dir, TIPS_FILE)
        self.user_tips_path = os.path.join(base_dir, USER_TIPS_FILE)
        self._user_tips = None  # 惰性加载

    # ---------------- 数据加载 ----------------
    def _load_json(self, path, default):
        """读 JSON 文件；不存在或损坏时返回 default（不抛异常）。"""
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get("tips"), list):
                return data["tips"]
        except Exception:
            pass
        return default

    def _save_user_tips(self, tips):
        """写 user_tips.json（UTF-8，带缩进，可人工阅读）。"""
        try:
            with open(self.user_tips_path, "w", encoding="utf-8") as f:
                json.dump(tips, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def load_user_tips(self):
        """加载用户贴士（惰性缓存）。"""
        if self._user_tips is None:
            self._user_tips = self._load_json(self.user_tips_path, [])
        return self._user_tips

    def builtin_tips(self):
        """内置贴士：优先读外部 tips.json（源码模式，仓库随版本发布），
        读不到或内容异常时用内置常量兜底（exe 单文件模式无外部文件，走常量）。
        """
        ext = self._load_json(self.tips_path, None)
        if isinstance(ext, list) and ext:
            if all(isinstance(t, dict) and t.get("source") == "builtin" for t in ext):
                return ext
        return list(TIPS_BUILTIN)

    def all_tips(self):
        """全部贴士：内置 + 用户（用户条目排在后面）。"""
        return self.builtin_tips() + self.load_user_tips()

    # ---------------- 增删改查 ----------------
    def _next_user_id(self):
        """用户贴士 id 从 1001 开始，避免与内置 id 冲突。"""
        tips = self.load_user_tips()
        ids = [t.get("id", 0) for t in tips] + [1000]
        return max(ids) + 1

    def add_tip(self, title, content, category="安装", tags=None):
        """新增用户贴士，返回 (ok, msg)。"""
        title = (title or "").strip()
        content = (content or "").strip()
        if not title or not content:
            return False, "标题和内容不能为空"
        if category not in TIPS_CATEGORIES:
            category = "安装"
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.replace("，", ",").split(",") if t.strip()]
        tips = self.load_user_tips()
        tips.append({
            "id": self._next_user_id(),
            "title": title,
            "content": content,
            "category": category,
            "tags": list(tags or []),
            "source": "user",
            "created_at": datetime.date.today().isoformat(),
        })
        if self._save_user_tips(tips):
            return True, "已新增"
        return False, "写入 user_tips.json 失败（目录可能无写权限）"

    def update_tip(self, tip_id, title=None, content=None, category=None, tags=None):
        """编辑用户贴士；内置贴士不可编辑。返回 (ok, msg)。"""
        tips = self.load_user_tips()
        for t in tips:
            if t.get("id") == tip_id:
                if t.get("source") != "user":
                    return False, "内置贴士不可编辑"
                if title is not None:
                    t["title"] = title.strip()
                if content is not None:
                    t["content"] = content.strip()
                if category is not None and category in TIPS_CATEGORIES:
                    t["category"] = category
                if tags is not None:
                    if isinstance(tags, str):
                        tags = [x.strip() for x in tags.replace("，", ",").split(",") if x.strip()]
                    t["tags"] = list(tags)
                if self._save_user_tips(tips):
                    return True, "已保存"
                return False, "写入 user_tips.json 失败"
        return False, "未找到该贴士"

    def delete_tip(self, tip_id):
        """删除用户贴士；内置贴士不可删除。返回 (ok, msg)。"""
        tips = self.load_user_tips()
        for i, t in enumerate(tips):
            if t.get("id") == tip_id:
                if t.get("source") != "user":
                    return False, "内置贴士不可删除"
                del tips[i]
                if self._save_user_tips(tips):
                    return True, "已删除"
                return False, "写入 user_tips.json 失败"
        return False, "未找到该贴士"

    def restore_default(self):
        """恢复默认：清空全部用户自定义贴士。返回 (ok, msg)。"""
        if self._save_user_tips([]):
            self._user_tips = []
            return True, "已恢复默认（仅保留内置贴士）"
        return False, "写入失败"

    def search(self, keyword):
        """按关键词搜索：匹配标题 / 内容 / 标签 / 分类。空关键词返回全部。"""
        keyword = (keyword or "").strip().lower()
        if not keyword:
            return self.all_tips()
        hits = []
        for t in self.all_tips():
            haystack = " ".join([
                str(t.get("title", "")),
                str(t.get("content", "")),
                str(t.get("category", "")),
                " ".join(t.get("tags", [])),
            ]).lower()
            if keyword in haystack:
                hits.append(t)
        return hits

    # ---------------- 高阶：导出 PR 贡献素材 ----------------
    def export_contribution(self, out_dir=None):
        """导出用户自定义贴士为 PR 贡献素材。

        生成两个文件：
          tips_contribution.json   JSON 片段（用户贴士数组）
          CONTRIBUTING_TIPS.md     提交说明（格式规范 + 提交流程）
        返回 (ok, msg, out_dir)。
        """
        tips = self.load_user_tips()
        if not tips:
            return False, "暂无用户自定义贴士可导出", None
        if out_dir is None:
            out_dir = os.path.join(self.base_dir, "贡献素材")
        try:
            os.makedirs(out_dir, exist_ok=True)
            json_path = os.path.join(out_dir, "tips_contribution.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(tips, f, ensure_ascii=False, indent=2)

            md_path = os.path.join(out_dir, "CONTRIBUTING_TIPS.md")
            lines = [
                "# 小贴士贡献说明（Knowledge Tips Contribution）",
                "",
                "感谢你愿意向「西门子安装助手」贡献小贴士！",
                "下面这份素材由工具自动导出，按以下步骤即可提交：",
                "",
                "## 1. 素材内容",
                "- 文件：`tips_contribution.json`（本次导出的用户自定义贴士，共 %d 条）" % len(tips),
                "- 每条贴士字段：`id` / `title` / `content` / `category` / `tags` / `source` / `created_at`",
                "- 分类取值范围：%s" % "、".join(TIPS_CATEGORIES),
                "",
                "## 2. 提交方式（需先自学 Git / GitHub 基础）",
                "1. Fork 本仓库（GitHub: chenpiyanghappy/SiemensInstallHelper，或 CNB 镜像）",
                "2. 把你自己的贴士条目合并进仓库根目录的 `tips.json`（追加到文件末尾数组）",
                "3. 注意：`id` 改成仓库中当前最大 id + 1；`source` 改为 `builtin`",
                "4. 提交 Pull Request / 合并请求，标题示例：`tips: add 2 new tips`",
                "",
                "## 3. 注意事项",
                "- 内容请基于自己真实遇到并验证过的场景；",
                "- 禁止包含破解、授权、密钥相关内容；",
                "- 管理员（AI 初审 + 人工复核）审核通过后会并入正式贴士库。",
                "",
                "## 4. 反馈渠道",
                "- GitHub Issues / CNB Issues；也可用工具内「复制反馈模板」直接反馈。",
                "",
            ]
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True, "已导出 %d 条贴士的贡献素材" % len(tips), out_dir
        except Exception as e:
            return False, "导出失败: %s" % e, None


# ---------------------------------------------------------------------
# CLI：python tips.py list|add|delete|search|export [参数]
# ---------------------------------------------------------------------
def _cli_usage():
    print("用法: python tips.py <命令> [参数]")
    print("  list                    列出全部贴士")
    print("  search <关键词>          搜索贴士")
    print("  add --title <标题> --content <内容> [--category 安装] [--tags a,b]")
    print("  delete <id>             删除用户贴士")
    print("  restore                 恢复默认（清空用户贴士）")
    print("  export [输出目录]        导出 PR 贡献素材")


def tips_cli(argv):
    """tips 子命令入口（供 siemens_install.py 的 main 调用）。"""
    mgr = TipsManager()
    if not argv:
        _cli_usage()
        return
    cmd = argv[0].lower()
    if cmd == "list":
        for t in mgr.all_tips():
            mark = "★" if t.get("source") == "user" else "·"
            print("[%s] %s #%s (%s)" % (mark, t.get("title"), t.get("id"), t.get("category")))
    elif cmd == "search":
        kw = argv[1] if len(argv) > 1 else ""
        hits = mgr.search(kw)
        print("命中 %d 条:" % len(hits))
        for t in hits:
            mark = "★" if t.get("source") == "user" else "·"
            print("[%s] %s #%s (%s)" % (mark, t.get("title"), t.get("id"), t.get("category")))
    elif cmd == "add":
        title = content = category = tags = None
        i = 1
        while i < len(argv):
            a = argv[i]
            if a == "--title" and i + 1 < len(argv):
                title, i = argv[i + 1], i + 2
            elif a == "--content" and i + 1 < len(argv):
                content, i = argv[i + 1], i + 2
            elif a == "--category" and i + 1 < len(argv):
                category, i = argv[i + 1], i + 2
            elif a == "--tags" and i + 1 < len(argv):
                tags, i = argv[i + 1], i + 2
            else:
                i += 1
        ok, msg = mgr.add_tip(title or "", content or "", category or "安装", tags or "")
        print(msg)
        if ok:
            print("新增成功，可用 list 查看。")
    elif cmd == "delete":
        if len(argv) < 2 or not argv[1].isdigit():
            print("用法: tips delete <id>")
            return
        ok, msg = mgr.delete_tip(int(argv[1]))
        print(msg)
    elif cmd == "restore":
        ok, msg = mgr.restore_default()
        print(msg)
    elif cmd == "export":
        out_dir = argv[1] if len(argv) > 1 else None
        ok, msg, path = mgr.export_contribution(out_dir)
        print(msg)
        if ok:
            print("输出目录: %s" % path)
    else:
        _cli_usage()


if __name__ == "__main__":
    import sys
    tips_cli(sys.argv[1:])
