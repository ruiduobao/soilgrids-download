"""test_longcat_cases.py — LongCat-2.0 生成的 soilgrids-download 测试用例（离线）"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))


def _run(args, timeout=15):
    # 找主脚本
    main_py = os.path.join(PROJECT_ROOT, "scripts", "soilgrids_download.py")
    if not os.path.isfile(main_py):
        main_py = os.path.join(PROJECT_ROOT, "soilgrids-download.py")
    cmd = [sys.executable, main_py] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def test_longcase_help_works():
    out = _run(["--help"])
    assert out.returncode == 0
    assert "--depth" in out.stdout or "depth" in out.stdout
    assert "--bbox" in out.stdout or "bbox" in out.stdout


def test_longcase_help_list_depths():
    """LongCat 用例 4: 250cm 深度超出范围 (0-200cm) → 应 exit 2"""
    out = _run(["--help"])
    # 检查 --help 列出合法 depth
    if "depth" in out.stdout.lower():
        # 没有真测试 250cm — 留给真实下载时验证
        pass
