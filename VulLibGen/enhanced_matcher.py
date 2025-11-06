"""
改进的漏洞-组件匹配器

包含：
1. 命名实体识别（从CVE提取包名）
2. 域特定关键字权重
3. 相关包名识别
4. 综合评分机制
"""

import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class PackageNameMatcher:
    """包名匹配引擎"""

    # 常见的包名前缀/后缀映射
    PACKAGE_ALIASES = {
        # Java
        'log4j2': ['log4j', 'apache-log4j'],
        'slf4j': ['slg4j', 'simple-logging-facade-for-java'],
        'spring': ['spring-framework', 'spring-boot'],

        # Python
        'pillow': ['pil', 'image-library'],
        'pyyaml': ['yaml', 'pyyaml'],

        # JavaScript
        'lodash': ['underscore.js'],
        'moment': ['momentjs'],

        # Common
        'openssl': ['ssl', 'tls', 'boringssl', 'libressl'],
        'curl': ['libcurl'],
        'sqlite': ['sqlite3'],
    }

    # 域特定关键字 - 增强特定包的识别
    DOMAIN_KEYWORDS = {
        # 日志库
        'log4j': ['logging', 'logger', 'appender', 'logback', 'slf4j', 'log level'],
        'logback': ['logging', 'logger', 'sl4fj', 'appender'],

        # Web框架
        'spring': ['spring', 'framework', 'mvc', 'boot', 'bean', 'context', 'annotation'],
        'django': ['django', 'web', 'framework', 'orm', 'template', 'middleware'],
        'flask': ['flask', 'micro', 'framework', 'route', 'blueprint'],
        'express': ['express', 'middleware', 'route', 'handler'],

        # 数据库
        'mysql': ['database', 'sql', 'connector', 'jdbc'],
        'postgresql': ['postgres', 'database', 'sql', 'psycopg'],

        # 加密/安全
        'openssl': ['ssl', 'tls', 'encryption', 'crypto', 'certificate', 'handshake'],
        'bouncycastle': ['crypto', 'encryption', 'provider', 'security'],

        # HTTP客户端
        'requests': ['http', 'request', 'urllib', 'api', 'client'],
        'httpx': ['http', 'request', 'async', 'api'],

        # JSON处理
        'jackson': ['json', 'serialization', 'databind'],
        'gson': ['json', 'serialization', 'google'],
    }

    # 已知的版本范围易受攻击的包
    VERSION_CRITICAL_PACKAGES = {
        'log4j': [(2, 0, 0), (2, 16, 0)],  # Log4Shell: 2.0-2.15.x
        'apache-commons-text': [(1, 0, 0), (1, 10, 0)],  # CVE-2021-21330: 1.0-1.9.x
    }

    def __init__(self):
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """编译正则表达式"""
        return {
            # Java GroupId:ArtifactId
            'java_standard': re.compile(
                r'([a-z0-9]+(?:\.[a-z0-9]+)*):([a-z0-9\-]+)',
                re.IGNORECASE
            ),

            # Maven插件
            'maven_plugin': re.compile(
                r'maven-([a-z0-9\-]+)-plugin',
                re.IGNORECASE
            ),

            # Python包名（带或不带namespace）
            'python_standard': re.compile(
                r'\b([a-z0-9][\w\-]*)\b',
                re.IGNORECASE
            ),

            # NPM作用域包
            'npm_scoped': re.compile(
                r'@([a-z0-9\-]+)/([a-z0-9\-]+)',
                re.IGNORECASE
            ),

            # 版本号模式
            'version': re.compile(
                r'\b(\d+\.\d+(?:\.\d+)?(?:[-.]?[a-zA-Z0-9]+)?)\b'
            ),

            # CVE编号
            'cve': re.compile(r'CVE-(\d+-\d+)', re.IGNORECASE),

            # CVSS分数
            'cvss': re.compile(r'CVSS[:\s]+([0-9.]+)', re.IGNORECASE),
        }

    def extract_components_from_cve(self, cve_text: str, cve_id: str = "") -> List[Tuple[str, float]]:
        """
        从CVE描述中智能提取组件名称

        使用多个启发式方法：
        1. 直接包名提取（正则模式）
        2. 制造商/项目名识别
        3. 已知CVE映射

        Returns:
            [(component_name, confidence_score), ...]
        """
        extracted = {}  # {name: confidence}

        # 1. 直接模式匹配
        # 查找Java标准格式
        for match in self.patterns['java_standard'].finditer(cve_text):
            group_id, artifact_id = match.groups()
            full_name = f"{group_id}:{artifact_id}"
            extracted[full_name] = extracted.get(full_name, 0) + 0.8

        # 查找NPM作用域包
        for match in self.patterns['npm_scoped'].finditer(cve_text):
            scope, name = match.groups()
            full_name = f"@{scope}/{name}"
            extracted[full_name] = extracted.get(full_name, 0) + 0.8

        # 2. 已知映射（通过CVE ID查询已知的受影响包）
        known_mappings = self._get_known_cve_packages(cve_id)
        for pkg_name in known_mappings:
            extracted[pkg_name] = 1.0  # 最高置信度

        # 3. 常见包名启发式
        common_packages = [
            'log4j', 'spring', 'django', 'flask', 'express',
            'openssl', 'mysql', 'postgresql', 'sqlite',
            'requests', 'curl', 'wget', 'nginx',
            'apache', 'tomcat', 'jboss', 'jetty'
        ]

        text_lower = cve_text.lower()
        for pkg in common_packages:
            # 检查完整单词边界
            if re.search(rf'\b{re.escape(pkg)}\b', text_lower):
                confidence = 0.6 + (0.2 if cve_id else 0)  # CVE ID提高置信度
                extracted[pkg] = max(extracted.get(pkg, 0), confidence)

        # 4. 清理和返回
        result = []
        for name, confidence in extracted.items():
            if len(name) > 2 and not self._is_stopword(name):
                result.append((name.lower(), min(confidence, 1.0)))

        return sorted(result, key=lambda x: x[1], reverse=True)

    def _get_known_cve_packages(self, cve_id: str) -> List[str]:
        """
        查询已知的CVE-包映射

        在实际系统中，这应该从数据库查询
        """
        # CVE ID -> 受影响包映射
        known_cves = {
            'CVE-2021-44228': ['log4j', 'log4j2', 'apache:logging-log4j'],
            'CVE-2021-21330': ['commons-text', 'apache:commons-text'],
            'CVE-2021-22119': ['spring', 'spring-framework'],
            'CVE-2021-41773': ['apache', 'httpd'],
        }

        return known_cves.get(cve_id, [])

    def _is_stopword(self, word: str) -> bool:
        """检查是否是无关的词"""
        stopwords = {
            'the', 'and', 'or', 'a', 'an', 'in', 'on', 'at', 'to', 'for',
            'of', 'is', 'are', 'was', 'were', 'be', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'vulnerability', 'issue', 'cve',
            'attack', 'allow', 'could', 'may', 'affect', 'version',
            'remote', 'local', 'denial', 'service', 'execution',
        }
        return word.lower() in stopwords

    def calculate_similarity(self, component: Dict, vulnerability: Dict) -> Tuple[float, str]:
        """
        计算组件和漏洞的相似度

        Returns:
            (similarity_score: 0-1, reasoning: 说明)
        """
        comp_name = component['name'].lower()
        vuln_desc = vulnerability.get('description', '').lower()
        vuln_title = vulnerability.get('title', '').lower()

        # 构建完整的漏洞文本
        full_text = f"{vuln_title} {vuln_desc}"

        scores = []
        reasons = []

        # 1. 精确名字匹配（最高权重）
        if comp_name in full_text:
            exact_score = 1.0
            scores.append(('exact_match', exact_score, 0.4))
            reasons.append(f"完全匹配包名'{comp_name}'")

        # 2. 部分名字匹配
        parts = re.split(r'[:\-/_\.]', comp_name)
        significant_parts = [p for p in parts if len(p) > 2]

        if significant_parts:
            matched = sum(1 for p in significant_parts if p in full_text)
            partial_score = matched / len(significant_parts)
            scores.append(('partial_match', partial_score, 0.3))
            if matched > 0:
                reasons.append(f"部分匹配: {matched}/{len(significant_parts)}个组件")

        # 3. 版本号出现在漏洞中
        comp_version = component.get('version', '')
        if comp_version and comp_version in vuln_desc:
            version_score = 0.7
            scores.append(('version_match', version_score, 0.2))
            reasons.append(f"版本号'{comp_version}'在漏洞描述中")

        # 4. 域特定关键字
        keywords = self.DOMAIN_KEYWORDS.get(comp_name, [])
        if keywords:
            keyword_matched = sum(1 for kw in keywords if kw in full_text)
            keyword_score = keyword_matched / len(keywords) if keywords else 0
            scores.append(('domain_keywords', keyword_score, 0.2))
            if keyword_matched > 0:
                reasons.append(f"域关键字匹配: {keyword_matched}个")

        # 5. 别名检查
        for alias, names in self.PACKAGE_ALIASES.items():
            if comp_name == alias:
                for name in names:
                    if name in full_text:
                        alias_score = 0.6
                        scores.append(('alias_match', alias_score, 0.15))
                        reasons.append(f"别名'{name}'匹配")
                        break

        # 计算加权分数
        if scores:
            total_weighted = sum(score * weight for _, score, weight in scores)
            total_weight = sum(weight for _, _, weight in scores)
            final_score = total_weighted / total_weight if total_weight > 0 else 0
        else:
            final_score = 0
            reasons.append("无匹配特征")

        reasoning = "; ".join(reasons) if reasons else "无"

        return min(final_score, 1.0), reasoning

    def match_vulnerability(self, components: List[Dict], vulnerability: Dict) -> List[Dict]:
        """
        将漏洞匹配到所有组件

        Returns:
            匹配结果列表，按相似度排序
        """
        results = []

        # 先从CVE提取可能的包名
        cve_id = vulnerability.get('id', '')
        suspected_packages = self.extract_components_from_cve(
            vulnerability.get('description', ''),
            cve_id
        )

        for component in components:
            comp_name = component['name'].lower()

            # 1. 检查是否在suspected_packages中
            for suspected_name, suspected_conf in suspected_packages:
                if comp_name.startswith(suspected_name) or suspected_name.startswith(comp_name):
                    results.append({
                        'component_name': component['name'],
                        'vulnerability_id': vulnerability.get('id'),
                        'similarity': 0.95,  # 非常高的置信度
                        'match_type': 'named_entity_extracted',
                        'reasoning': f"从CVE描述中识别的包名匹配"
                    })
                    continue

            # 2. 通用相似度计算
            similarity, reasoning = self.calculate_similarity(component, vulnerability)

            # 只返回超过阈值的匹配
            if similarity > 0.5:
                results.append({
                    'component_name': component['name'],
                    'vulnerability_id': vulnerability.get('id'),
                    'similarity': similarity,
                    'match_type': 'similarity_based',
                    'reasoning': reasoning,
                    'confidence': 'high' if similarity > 0.75 else 'medium'
                })

        return sorted(results, key=lambda x: x['similarity'], reverse=True)


# 使用示例
if __name__ == "__main__":
    import json

    matcher = PackageNameMatcher()

    # 测试用例
    test_vulnerabilities = [
        {
            'id': 'CVE-2021-44228',
            'title': 'Apache Log4j2 RCE',
            'description': 'A critical vulnerability in Apache log4j2 versions before 2.16.0 allows remote code execution through JNDI injection'
        },
        {
            'id': 'CVE-2021-22119',
            'title': 'Spring Framework Security Issue',
            'description': 'Spring Framework versions before 5.3.9 and 5.2.13 contain a security vulnerability'
        },
    ]

    test_components = [
        {'name': 'log4j', 'version': '2.14.0', 'language': 'java'},
        {'name': 'org.apache.logging.log4j:log4j-core', 'version': '2.15.0', 'language': 'java'},
        {'name': 'spring-framework', 'version': '5.3.8', 'language': 'java'},
        {'name': 'requests', 'version': '2.28.0', 'language': 'python'},
    ]

    print("=" * 80)
    print("漏洞-组件匹配测试")
    print("=" * 80)

    for vuln in test_vulnerabilities:
        print(f"\n漏洞: {vuln['id']} - {vuln['title']}")
        matches = matcher.match_vulnerability(test_components, vuln)

        if matches:
            for match in matches[:3]:  # 仅显示前3个匹配
                print(f"  ✓ {match['component_name']}")
                print(f"    相似度: {match['similarity']:.1%}")
                print(f"    说明: {match['reasoning']}")
        else:
            print("  (无匹配)")
