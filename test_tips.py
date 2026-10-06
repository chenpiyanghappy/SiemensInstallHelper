#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tips.py 功能测试：CRUD / 搜索 / 导出贡献素材 / 内置只读保护。"""
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tips

tmp = tempfile.mkdtemp(prefix="sih_tips_test_")
mgr = tips.TipsManager(base_dir=tmp)

failures = []
def check(name, cond, detail=""):
    if cond:
        print("PASS | %s" % name)
    else:
        failures.append(name)
        print("FAIL | %s %s" % (name, detail))

# 1. 内置贴士
builtin = mgr.builtin_tips()
check("内置贴士 10 条", len(builtin) == 10, "got %d" % len(builtin))
check("内置字段齐全", all({"id","title","content","category","tags","source"} <= set(t) for t in builtin))
check("内置 source=builtin", all(t["source"] == "builtin" for t in builtin))

# 2. 初始 user_tips 为空
check("初始用户贴士为空", mgr.load_user_tips() == [])

# 3. add
ok, msg = mgr.add_tip("测试贴士", "U 盘解压容易坏，先拷本地。", "安装", "U盘,解压")
check("add 成功", ok, msg)
ok2, msg2 = mgr.add_tip("空内容", "   ", "安装", None)
check("add 空内容被拒", not ok2, msg2)
tips_all = mgr.all_tips()
check("全部贴士 11 条", len(tips_all) == 11, "got %d" % len(tips_all))
user = mgr.load_user_tips()
check("用户贴士 id>=1001", user[0]["id"] >= 1001, "id=%s" % user[0]["id"])
check("用户贴士 source=user", user[0]["source"] == "user")
check("中文逗号 tags 拆分", user[0]["tags"] == ["U盘", "解压"], str(user[0]["tags"]))

# 4. 文件确实落盘
with open(os.path.join(tmp, "user_tips.json"), "r", encoding="utf-8") as f:
    disk = json.load(f)
check("user_tips.json 落盘", isinstance(disk, list) and len(disk) == 1)

# 5. search
check("搜索'U盘'命中", len(mgr.search("U盘")) >= 1)
check("搜索'不存在的词'为空", len(mgr.search("zzz_not_exist")) == 0)
check("搜索空串=全部", len(mgr.search("")) == 11)

# 6. update
uid = user[0]["id"]
ok, msg = mgr.update_tip(uid, title="改标题", tags="新标签")
check("update 成功", ok, msg)
check("update 生效", mgr.load_user_tips()[0]["title"] == "改标题")
ok, msg = mgr.update_tip(1, title="x")
check("内置不可编辑", not ok, msg)

# 7. delete
ok, msg = mgr.delete_tip(uid)
check("delete 成功", ok, msg)
check("delete 后为空", mgr.load_user_tips() == [])
ok, msg = mgr.delete_tip(1)
check("内置不可删除", not ok, msg)

# 8. restore_default
mgr.add_tip("t1", "c1", "安装", None)
mgr.add_tip("t2", "c2", "排障", None)
ok, msg = mgr.restore_default()
check("restore 成功", ok, msg)
check("restore 后为空", mgr.load_user_tips() == [])

# 9. export_contribution
mgr.add_tip("贡献贴士", "这个方案我实测过有效", "排障", "测试")
ok, msg, out = mgr.export_contribution()
check("export 成功", ok, msg)
check("export 目录生成", out and os.path.isdir(out))
if ok:
    with open(os.path.join(out, "tips_contribution.json"), "r", encoding="utf-8") as f:
        contrib = json.load(f)
    check("导出 JSON 为用户贴士", isinstance(contrib, list) and len(contrib) == 1 and contrib[0]["source"] == "user")
    with open(os.path.join(out, "CONTRIBUTING_TIPS.md"), "r", encoding="utf-8") as f:
        md = f.read()
    check("导出说明文档存在", "tips_contribution.json" in md and "Pull Request" in md)
# 无用户贴士时导出失败
mgr.restore_default()
ok, msg, out = mgr.export_contribution()
check("无贴士导出被拒", not ok, msg)

print()
if failures:
    print("== %d 项失败: %s" % (len(failures), ", ".join(failures)))
    sys.exit(1)
print("== 全部测试通过 ==")
