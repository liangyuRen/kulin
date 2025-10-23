import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.I)
GHSA_RE = re.compile(r"GHSA-[\w\-]+", re.I)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://github.com/advisories"
}


def _text(node, default=""):
    """安全获取节点文本"""
    return node.get_text(strip=True) if node else default


def _norm_severity(s: str) -> str:
    """标准化风险等级"""
    s = (s or "").strip().title()
    if s == "Moderate": return "Medium"
    if s == "Critical": return "High"
    if s in {"High", "Medium", "Low"}: return s
    return "Low"


def parse_page(page_url, existing_ids, max_retries=3):
    """
    解析单个页面

    Args:
        page_url: 页面URL
        existing_ids: 已存在的ID集合，用于去重
        max_retries: 最大重试次数

    Returns:
        (advisory_list, has_next, new_count): 漏洞列表、是否有下一页、新漏洞数量
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            advisory_list = []
            new_count = 0

            for row in soup.select(".Box-row"):
                # 提取标题链接
                title_a = row.select_one("a.Link--primary")
                if not title_a:
                    continue

                summary = _text(title_a)
                href = title_a.get("href", "")
                detail_url = href if href.startswith("http") else f"https://github.com{href}"

                # 提取ID：优先查找 GHSA 或 CVE
                id_node = row.select_one(".text-bold")
                raw_id = _text(id_node)

                # 尝试匹配GHSA或CVE ID
                ghsa_match = GHSA_RE.search(raw_id) or GHSA_RE.search(detail_url)
                cve_match = CVE_RE.search(raw_id) or CVE_RE.search(summary) or CVE_RE.search(detail_url)

                # 优先使用GHSA ID，其次CVE ID
                if ghsa_match:
                    vuln_id = ghsa_match.group(0)
                    id_type = "GHSA"
                elif cve_match:
                    vuln_id = cve_match.group(0)
                    id_type = "CVE"
                else:
                    vuln_id = raw_id or f"GITHUB-{hash(detail_url)}"
                    id_type = "OTHER"

                # 去重检查
                if vuln_id in existing_ids:
                    continue

                existing_ids.add(vuln_id)
                new_count += 1

                # 提取严重性和日期
                severity = _norm_severity(_text(row.select_one(".Label"), "Low"))
                rt = row.select_one("relative-time")
                date = (rt.get("datetime", "")[:10]) if rt else ""

                # 构建描述信息
                description_parts = [f"GitHub Security Advisory: {summary}"]
                if id_type == "CVE":
                    description_parts.append(f"CVE编号：{vuln_id}")
                if id_type == "GHSA":
                    description_parts.append(f"GHSA编号：{vuln_id}")
                if raw_id and raw_id != vuln_id:
                    description_parts.append(f"原始ID：{raw_id}")
                description_parts.append(f"风险等级：{severity}")

                description = "，".join(description_parts)

                advisory_list.append({
                    "vulnerabilityName": summary,
                    "cveId": vuln_id,
                    "disclosureTime": date,
                    "description": description,
                    "riskLevel": severity,
                    "referenceLink": detail_url,
                    "affectsWhitelist": 0,
                    "isDelete": 0,
                })

            # 检查是否有下一页
            next_a = soup.select_one("a.next_page")
            has_next = bool(next_a and next_a.get("href") and next_a.get("aria-disabled") != "true")

            return advisory_list, has_next, new_count

        except requests.RequestException as e:
            print(f"Request error on {page_url} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                return [], False, 0
        except Exception as e:
            print(f"Parse error on {page_url}: {e}")
            return [], False, 0


def github(start_page=1, target_count=20000, max_pages=2000):
    """
    爬取GitHub安全公告

    Args:
        start_page: 起始页码
        target_count: 目标爬取数量（默认20000）
        max_pages: 最大页数限制（默认2000页）

    Returns:
        list: 漏洞数据列表
    """
    print(f"开始爬取GitHub安全公告...")
    print(f"目标数量: {target_count} 条, 最大页数: {max_pages}")

    # 使用排序参数，按发布时间倒序（最新的在前）
    base_url = "https://github.com/advisories?page={}&query=type%3Areviewed+sort%3Apublished-desc"

    page_num = start_page
    combined = []
    existing_ids = set()
    total_new = 0
    start_time = time.time()
    consecutive_no_new = 0  # 连续无新数据的页数

    while len(combined) < target_count and page_num < max_pages + start_page:
        page_url = base_url.format(page_num)

        items, has_next, new_count = parse_page(page_url, existing_ids)

        if items:
            combined.extend(items)
            total_new += new_count

        elapsed = time.time() - start_time
        print(f"[页 {page_num}] 本页: {len(items)} 条 | 新增: {new_count} 条 | "
              f"累计: {len(combined)}/{target_count} | "
              f"耗时: {elapsed:.1f}秒 | "
              f"速率: {len(combined)/elapsed:.1f}条/秒")

        # 如果连续多页没有新数据，可能是重复数据，提前结束
        if new_count == 0:
            consecutive_no_new += 1
            if consecutive_no_new >= 5:
                print(f"连续 {consecutive_no_new} 页无新数据，可能已爬取完所有新漏洞")
                break
        else:
            consecutive_no_new = 0

        # 检查是否达到目标
        if len(combined) >= target_count:
            print(f"已达到目标数量 {target_count}，停止爬取")
            break

        # 检查是否还有下一页
        if not has_next:
            print("没有更多页面了")
            break

        page_num += 1

        # 添加延迟，避免请求过快被封
        time.sleep(1.5)

    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"爬取完成!")
    print(f"总页数: {page_num - start_page + 1} 页")
    print(f"总数量: {len(combined)} 条")
    print(f"新增数量: {total_new} 条")
    print(f"去重数量: {len(items) - new_count if items else 0} 条")
    print(f"总耗时: {total_time:.1f} 秒")
    print(f"平均速率: {len(combined)/total_time:.2f} 条/秒")
    print(f"{'='*60}\n")

    # 数据验证和清理
    try:
        from web_crawler.data_validator import validate_and_clean_vulnerability_data
        combined = validate_and_clean_vulnerability_data(combined, "github")
        print(f"数据验证完成。最终数量: {len(combined)} 条")
    except ImportError:
        print("数据验证器不可用，返回原始数据")
    except Exception as e:
        print(f"数据验证时出错: {e}")

    return combined[:target_count]  # 确保不超过目标数量


if __name__ == "__main__":
    import json

    # 测试：爬取100条数据
    print("测试模式：爬取 100 条最新漏洞")
    json_data = github(start_page=1, target_count=100, max_pages=10)

    # 打印统计信息
    print(f"\n数据统计:")
    print(f"总数量: {len(json_data)}")

    # 按风险等级统计
    risk_stats = {}
    for item in json_data:
        risk = item.get('riskLevel', 'Unknown')
        risk_stats[risk] = risk_stats.get(risk, 0) + 1
    print(f"风险等级分布: {risk_stats}")

    # 打印前3条数据
    print("\n前3条数据:")
    print(json.dumps(json_data[:3], indent=2, ensure_ascii=False))

    # 保存到文件
    output_file = "github_vulnerabilities_sample.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"\n数据已保存到: {output_file}")
