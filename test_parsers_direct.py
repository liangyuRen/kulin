#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
直接测试各语言的parser函数
从 D:\kuling\upload 读取已上传的项目，直接调用parser函数测试
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def test_java_parser(project_path):
    """测试Java/Maven解析器"""
    from parase.pom_parse import process_projects, find_pom_files, parse_pom_file

    print(f"\n{'='*70}")
    print(f"测试 Java/Maven 解析器")
    print(f"{'='*70}")
    print(f"项目路径: {project_path}")

    # 查找pom.xml文件
    pom_files = find_pom_files(str(project_path))

    if not pom_files:
        print("  ⊘ 未找到 pom.xml 文件")
        return {'status': 'no_files', 'dependencies': []}

    print(f"  ✓ 找到 {len(pom_files)} 个 pom.xml 文件")

    # 解析依赖（不调用LLM）
    all_deps = set()
    for pom_file in pom_files:
        deps = parse_pom_file(pom_file)
        all_deps.update(deps)
        print(f"    {Path(pom_file).name}: {len(deps)} 个依赖")

    print(f"  ✓ 总计 {len(all_deps)} 个唯一依赖")

    # 显示样本
    if all_deps:
        print(f"\n  样本依赖 (前5个):")
        for i, dep in enumerate(list(all_deps)[:5], 1):
            print(f"    [{i}] {dep}")

    return {
        'status': 'success',
        'pom_files': len(pom_files),
        'unique_dependencies': len(all_deps),
        'sample_dependencies': list(all_deps)[:10]
    }


def test_go_parser(project_path):
    """测试Go解析器"""
    from parase.go_parse import find_go_mod_files, parse_go_mod_file

    print(f"\n{'='*70}")
    print(f"测试 Go 解析器")
    print(f"{'='*70}")
    print(f"项目路径: {project_path}")

    # 查找go.mod文件
    go_mod_files = find_go_mod_files(str(project_path))

    if not go_mod_files:
        print("  ⊘ 未找到 go.mod 文件")
        return {'status': 'no_files', 'dependencies': []}

    print(f"  ✓ 找到 {len(go_mod_files)} 个 go.mod 文件")

    # 解析依赖
    all_deps = set()
    for go_mod_file in go_mod_files:
        deps = parse_go_mod_file(go_mod_file)
        all_deps.update(deps)
        print(f"    {Path(go_mod_file).name}: {len(deps)} 个依赖")

    print(f"  ✓ 总计 {len(all_deps)} 个唯一依赖")

    # 显示样本
    if all_deps:
        print(f"\n  样本依赖 (前5个):")
        for i, dep in enumerate(list(all_deps)[:5], 1):
            print(f"    [{i}] {dep}")

    return {
        'status': 'success',
        'go_mod_files': len(go_mod_files),
        'unique_dependencies': len(all_deps),
        'sample_dependencies': list(all_deps)[:10]
    }


def test_python_parser(project_path):
    """测试Python解析器"""
    from parase.python_parse import find_python_dependency_files, parse_requirements_txt, parse_pipfile, parse_setup_py

    print(f"\n{'='*70}")
    print(f"测试 Python 解析器")
    print(f"{'='*70}")
    print(f"项目路径: {project_path}")

    # 查找Python依赖文件
    dep_files = find_python_dependency_files(str(project_path))

    if not dep_files:
        print("  ⊘ 未找到 Python 依赖文件")
        return {'status': 'no_files', 'dependencies': []}

    print(f"  ✓ 找到 {len(dep_files)} 个依赖文件")

    # 解析依赖
    all_deps = set()
    for file_type, file_path in dep_files:
        print(f"    处理 {file_type}: {Path(file_path).name}")

        try:
            if file_type == 'requirements':
                deps = parse_requirements_txt(file_path)
            elif file_type == 'pipfile':
                deps = parse_pipfile(file_path)
            elif file_type == 'setup':
                deps = parse_setup_py(file_path)
            else:
                deps = []

            all_deps.update(deps)
            print(f"      → {len(deps)} 个依赖")

        except Exception as e:
            print(f"      ✗ 解析失败: {e}")

    print(f"  ✓ 总计 {len(all_deps)} 个唯一依赖")

    # 显示样本
    if all_deps:
        print(f"\n  样本依赖 (前5个):")
        for i, dep in enumerate(list(all_deps)[:5], 1):
            print(f"    [{i}] {dep}")

    return {
        'status': 'success',
        'dependency_files': len(dep_files),
        'unique_dependencies': len(all_deps),
        'sample_dependencies': list(all_deps)[:10]
    }


def test_javascript_parser(project_path):
    """测试JavaScript解析器"""
    from parase.javascript_parse import find_javascript_lock_files, parse_package_json, parse_yarn_lock, parse_package_lock_json, parse_pnpm_lock_yaml

    print(f"\n{'='*70}")
    print(f"测试 JavaScript 解析器")
    print(f"{'='*70}")
    print(f"项目路径: {project_path}")

    # 查找package.json文件
    lock_files = find_javascript_lock_files(str(project_path))

    if not lock_files:
        print("  ⊘ 未找到 package.json 或 lock 文件")
        return {'status': 'no_files', 'dependencies': []}

    print(f"  ✓ 找到 {len(lock_files)} 个依赖文件")

    # 解析依赖
    all_deps = set()
    for file_type, file_path in lock_files:
        print(f"    处理 {file_type}: {Path(file_path).name}")

        try:
            if file_type == 'npm':
                deps = parse_package_json(file_path)
            elif file_type == 'yarn':
                deps = parse_yarn_lock(file_path)
            elif file_type == 'npm_lock':
                deps = parse_package_lock_json(file_path)
            elif file_type == 'pnpm':
                deps = parse_pnpm_lock_yaml(file_path)
            else:
                deps = []

            all_deps.update(deps)
            print(f"      → {len(deps)} 个依赖")

        except Exception as e:
            print(f"      ✗ 解析失败: {e}")

    print(f"  ✓ 总计 {len(all_deps)} 个唯一依赖")

    # 显示样本
    if all_deps:
        print(f"\n  样本依赖 (前5个):")
        for i, dep in enumerate(list(all_deps)[:5], 1):
            print(f"    [{i}] {dep}")

    return {
        'status': 'success',
        'dependency_files': len(lock_files),
        'unique_dependencies': len(all_deps),
        'sample_dependencies': list(all_deps)[:10]
    }


def test_php_parser(project_path):
    """测试PHP解析器"""
    from parase.php_parse import find_composer_files, parse_composer_json, parse_composer_lock

    print(f"\n{'='*70}")
    print(f"测试 PHP 解析器")
    print(f"{'='*70}")
    print(f"项目路径: {project_path}")

    # 查找composer文件
    composer_files = find_composer_files(str(project_path))

    if not composer_files:
        print("  ⊘ 未找到 composer.json 或 composer.lock 文件")
        return {'status': 'no_files', 'dependencies': []}

    print(f"  ✓ 找到 {len(composer_files)} 个 composer 文件")

    # 解析依赖
    all_deps = set()
    for file_type, file_path in composer_files:  # 正确处理元组
        print(f"    处理 {file_type}: {Path(file_path).name}")

        try:
            if file_type == 'lock':
                deps = parse_composer_lock(file_path)
            else:
                deps = parse_composer_json(file_path)

            all_deps.update(deps)
            print(f"      → {len(deps)} 个依赖")

        except Exception as e:
            print(f"      ✗ 解析失败: {e}")

    print(f"  ✓ 总计 {len(all_deps)} 个唯一依赖")

    # 显示样本
    if all_deps:
        print(f"\n  样本依赖 (前5个):")
        for i, dep in enumerate(list(all_deps)[:5], 1):
            print(f"    [{i}] {dep}")

    return {
        'status': 'success',
        'composer_files': len(composer_files),
        'unique_dependencies': len(all_deps),
        'sample_dependencies': list(all_deps)[:10]
    }


def test_ruby_parser(project_path):
    """测试Ruby解析器"""
    from parase.ruby_parse import find_gemfiles, parse_gemfile, parse_gemfile_lock

    print(f"\n{'='*70}")
    print(f"测试 Ruby 解析器")
    print(f"{'='*70}")
    print(f"项目路径: {project_path}")

    # 查找Gemfile
    gemfiles = find_gemfiles(str(project_path))

    if not gemfiles:
        print("  ⊘ 未找到 Gemfile 或 Gemfile.lock 文件")
        return {'status': 'no_files', 'dependencies': []}

    print(f"  ✓ 找到 {len(gemfiles)} 个 Gemfile")

    # 解析依赖
    all_deps = set()
    for file_type, file_path in gemfiles:
        print(f"    处理 {file_type}: {Path(file_path).name}")

        try:
            if file_type == 'lock':
                deps = parse_gemfile_lock(file_path)
            else:
                deps = parse_gemfile(file_path)

            all_deps.update(deps)
            print(f"      → {len(deps)} 个依赖")

        except Exception as e:
            print(f"      ✗ 解析失败: {e}")

    print(f"  ✓ 总计 {len(all_deps)} 个唯一依赖")

    # 显示样本
    if all_deps:
        print(f"\n  样本依赖 (前5个):")
        for i, dep in enumerate(list(all_deps)[:5], 1):
            print(f"    [{i}] {dep}")

    return {
        'status': 'success',
        'gemfiles': len(gemfiles),
        'unique_dependencies': len(all_deps),
        'sample_dependencies': list(all_deps)[:10]
    }


def test_rust_parser(project_path):
    """测试Rust解析器"""
    from parase.rust_parse import find_cargo_files, parse_cargo_toml, parse_cargo_lock

    print(f"\n{'='*70}")
    print(f"测试 Rust 解析器")
    print(f"{'='*70}")
    print(f"项目路径: {project_path}")

    # 查找Cargo文件
    cargo_files = find_cargo_files(str(project_path))

    if not cargo_files:
        print("  ⊘ 未找到 Cargo.toml 或 Cargo.lock 文件")
        return {'status': 'no_files', 'dependencies': []}

    print(f"  ✓ 找到 {len(cargo_files)} 个 Cargo 文件")

    # 解析依赖
    all_deps = set()
    for file_type, file_path in cargo_files:
        print(f"    处理 {file_type}: {Path(file_path).name}")

        try:
            if file_type == 'lock':
                deps = parse_cargo_lock(file_path)
            else:
                deps = parse_cargo_toml(file_path)

            all_deps.update(deps)
            print(f"      → {len(deps)} 个依赖")

        except Exception as e:
            print(f"      ✗ 解析失败: {e}")

    print(f"  ✓ 总计 {len(all_deps)} 个唯一依赖")

    # 显示样本
    if all_deps:
        print(f"\n  样本依赖 (前5个):")
        for i, dep in enumerate(list(all_deps)[:5], 1):
            print(f"    [{i}] {dep}")

    return {
        'status': 'success',
        'cargo_files': len(cargo_files),
        'unique_dependencies': len(all_deps),
        'sample_dependencies': list(all_deps)[:10]
    }


def test_erlang_parser(project_path):
    """测试Erlang解析器"""
    from parase.erlang_parse import find_rebar_files, parse_rebar_config, parse_rebar_lock

    print(f"\n{'='*70}")
    print(f"测试 Erlang 解析器")
    print(f"{'='*70}")
    print(f"项目路径: {project_path}")

    # 查找rebar文件
    rebar_files = find_rebar_files(str(project_path))

    if not rebar_files:
        print("  ⊘ 未找到 rebar.config 或 rebar.lock 文件")
        return {'status': 'no_files', 'dependencies': []}

    print(f"  ✓ 找到 {len(rebar_files)} 个 rebar 文件")

    # 解析依赖
    all_deps = set()
    for file_type, file_path in rebar_files:
        print(f"    处理 {file_type}: {Path(file_path).name}")

        try:
            if file_type == 'lock':
                deps = parse_rebar_lock(file_path)
            else:
                deps = parse_rebar_config(file_path)

            all_deps.update(deps)
            print(f"      → {len(deps)} 个依赖")

        except Exception as e:
            print(f"      ✗ 解析失败: {e}")

    print(f"  ✓ 总计 {len(all_deps)} 个唯一依赖")

    # 显示样本
    if all_deps:
        print(f"\n  样本依赖 (前5个):")
        for i, dep in enumerate(list(all_deps)[:5], 1):
            print(f"    [{i}] {dep}")

    return {
        'status': 'success',
        'rebar_files': len(rebar_files),
        'unique_dependencies': len(all_deps),
        'sample_dependencies': list(all_deps)[:10]
    }


def test_all_parsers():
    """测试所有上传项目的解析器"""
    upload_dir = Path(r"D:\kuling\upload")

    print("="*70)
    print("测试各语言Parser函数")
    print("="*70)
    print(f"上传目录: {upload_dir}")
    print(f"测试模式: 直接测试parser函数（不调用LLM）")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 检查上传目录
    if not upload_dir.exists():
        print(f"✗ 错误: 上传目录不存在: {upload_dir}")
        return

    # 查找所有项目
    projects = [d for d in upload_dir.iterdir() if d.is_dir()]

    if not projects:
        print(f"✗ 上传目录中没有找到项目文件夹")
        return

    print(f"找到 {len(projects)} 个项目")

    # 定义parser测试函数
    parser_tests = {
        'java': (test_java_parser, ['pom.xml']),
        'go': (test_go_parser, ['go.mod']),
        'python': (test_python_parser, ['requirements.txt', 'setup.py', 'pyproject.toml']),
        'javascript': (test_javascript_parser, ['package.json']),
        'php': (test_php_parser, ['composer.json']),
        'ruby': (test_ruby_parser, ['Gemfile', 'Gemfile.lock']),
        'rust': (test_rust_parser, ['Cargo.toml', 'Cargo.lock']),
        'erlang': (test_erlang_parser, ['rebar.config', 'rebar.lock']),
    }

    all_results = []

    # 测试每个项目
    for i, project_path in enumerate(projects, 1):
        project_name = project_path.name

        print(f"\n\n{'#'*70}")
        print(f"# 项目 [{i}/{len(projects)}]: {project_name}")
        print(f"{'#'*70}")

        project_result = {
            'project_name': project_name,
            'project_path': str(project_path),
            'parsers_tested': {}
        }

        # 检测项目包含哪些语言
        detected_langs = []
        for lang, (test_func, marker_files) in parser_tests.items():
            for marker in marker_files:
                if any(project_path.rglob(marker)):
                    detected_langs.append(lang)
                    break

        if not detected_langs:
            print(f"  ⊘ 未检测到支持的语言标识文件")
            continue

        print(f"  检测到语言: {', '.join(detected_langs)}")

        # 测试每种检测到的语言
        for lang in detected_langs:
            test_func, _ = parser_tests[lang]

            try:
                result = test_func(project_path)
                project_result['parsers_tested'][lang] = result
            except Exception as e:
                print(f"\n  ✗ {lang} parser测试失败: {e}")
                import traceback
                traceback.print_exc()
                project_result['parsers_tested'][lang] = {
                    'status': 'error',
                    'error': str(e)
                }

        all_results.append(project_result)

    # 生成摘要
    print(f"\n\n{'='*70}")
    print("测试摘要")
    print(f"{'='*70}")

    # 统计
    lang_stats = {}
    for result in all_results:
        for lang, parser_result in result.get('parsers_tested', {}).items():
            if lang not in lang_stats:
                lang_stats[lang] = {
                    'projects': 0,
                    'total_deps': 0,
                    'success': 0,
                    'failed': 0
                }

            lang_stats[lang]['projects'] += 1

            if parser_result.get('status') == 'success':
                lang_stats[lang]['success'] += 1
                lang_stats[lang]['total_deps'] += parser_result.get('unique_dependencies', 0)
            else:
                lang_stats[lang]['failed'] += 1

    print(f"\n按语言统计:")
    print(f"{'语言':<12} {'项目数':<8} {'成功':<8} {'失败':<8} {'总依赖数'}")
    print("-" * 70)
    for lang, stats in sorted(lang_stats.items()):
        print(f"{lang:<12} {stats['projects']:<8} {stats['success']:<8} {stats['failed']:<8} {stats['total_deps']}")

    # 详细结果
    print(f"\n详细结果:")
    for result in all_results:
        print(f"\n{result['project_name']}:")
        for lang, parser_result in result.get('parsers_tested', {}).items():
            status = parser_result.get('status', 'unknown')
            deps = parser_result.get('unique_dependencies', 0)
            symbol = "✓" if status == 'success' else ("⊘" if status == 'no_files' else "✗")
            print(f"  {symbol} {lang}: {deps} 个依赖")

    # 保存报告
    report_path = Path(__file__).parent / "test_parsers_direct_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'upload_dir': str(upload_dir),
            'test_mode': 'direct_parser_test',
            'language_stats': lang_stats,
            'results': all_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n\n报告已保存至: {report_path}")
    print(f"\n✓ 测试完成!")


if __name__ == "__main__":
    try:
        test_all_parsers()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
