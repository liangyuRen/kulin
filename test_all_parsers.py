#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整测试所有 Parser 接口
"""
import requests
import json
import os
import tempfile
import time

BASE_URL = "http://127.0.0.1:5000"

print("\n" + "=" * 90)
print("Parser 接口完整测试 - 包含超时接口和未测试接口")
print("=" * 90)

# 创建小型测试项目目录
test_dir = tempfile.mkdtemp(prefix="test_parser_")
print(f"\n创建测试目录: {test_dir}")

test_results = {}

# ========== 测试 1: Java (pom_parse) ==========
print("\n" + "-" * 90)
print("Test 1: Java Parser (/parse/pom_parse)")
print("-" * 90)

java_dir = os.path.join(test_dir, "java_project")
os.makedirs(java_dir, exist_ok=True)

pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>test</artifactId>
  <version>1.0</version>
  <dependencies>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.13</version>
    </dependency>
  </dependencies>
</project>"""

with open(os.path.join(java_dir, "pom.xml"), "w") as f:
    f.write(pom_content)

try:
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/parse/pom_parse",
        params={"project_folder": java_dir},
        timeout=60
    )
    elapsed = time.time() - start

    print(f"Status: {response.status_code} | Response Time: {elapsed:.2f}s")
    result = response.json()

    # Handle both dict and list response formats
    if isinstance(result, dict):
        print(f"Message: {result.get('message')}")
        if result.get('code') == 200:
            deps = result.get('obj', [])
            print(f"Dependencies found: {len(deps)}")
            test_results['pom_parse'] = "PASS"
        else:
            print(f"Error: {str(result)[:200]}")
            test_results['pom_parse'] = "FAIL"
    elif isinstance(result, list):
        deps = result
        print(f"Dependencies found: {len(deps)}")
        test_results['pom_parse'] = "PASS"
    else:
        print(f"Unexpected response format: {type(result)}")
        test_results['pom_parse'] = "FAIL"
except requests.exceptions.Timeout:
    print(f"TIMEOUT after 60 seconds")
    test_results['pom_parse'] = "TIMEOUT"
except Exception as e:
    print(f"ERROR: {str(e)[:150]}")
    test_results['pom_parse'] = "ERROR"

# ========== 测试 2: C/C++ (c_parse) ==========
print("\n" + "-" * 90)
print("Test 2: C/C++ Parser (/parse/c_parse)")
print("-" * 90)

c_dir = os.path.join(test_dir, "c_project")
os.makedirs(c_dir, exist_ok=True)

with open(os.path.join(c_dir, "CMakeLists.txt"), "w") as f:
    f.write("""cmake_minimum_required(VERSION 3.10)
project(MyProject)

find_package(OpenSSL REQUIRED)
find_package(Boost REQUIRED)

add_executable(myapp main.c)
target_link_libraries(myapp OpenSSL::Crypto)
""")

try:
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/parse/c_parse",
        params={"project_folder": c_dir},
        timeout=60
    )
    elapsed = time.time() - start

    print(f"Status: {response.status_code} | Response Time: {elapsed:.2f}s")
    result = response.json()

    # Handle both dict and list response formats
    if isinstance(result, dict):
        print(f"Message: {result.get('message')}")
        if result.get('code') == 200:
            deps = result.get('obj', [])
            print(f"Dependencies found: {len(deps)}")
            test_results['c_parse'] = "PASS"
        else:
            print(f"Error: {str(result)[:200]}")
            test_results['c_parse'] = "FAIL"
    elif isinstance(result, list):
        deps = result
        print(f"Dependencies found: {len(deps)}")
        test_results['c_parse'] = "PASS"
    else:
        print(f"Unexpected response format: {type(result)}")
        test_results['c_parse'] = "FAIL"
except requests.exceptions.Timeout:
    print(f"TIMEOUT after 60 seconds")
    test_results['c_parse'] = "TIMEOUT"
except Exception as e:
    print(f"ERROR: {str(e)[:150]}")
    test_results['c_parse'] = "ERROR"

# ========== 测试 3: PHP (php_parse) ==========
print("\n" + "-" * 90)
print("Test 3: PHP Parser (/parse/php_parse)")
print("-" * 90)

php_dir = os.path.join(test_dir, "php_project")
os.makedirs(php_dir, exist_ok=True)

with open(os.path.join(php_dir, "composer.json"), "w") as f:
    f.write("""{
  "name": "test/project",
  "require": {
    "symfony/console": "^5.0",
    "monolog/monolog": "^2.0"
  }
}""")

try:
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/parse/php_parse",
        params={"project_folder": php_dir},
        timeout=60
    )
    elapsed = time.time() - start

    print(f"Status: {response.status_code} | Response Time: {elapsed:.2f}s")
    result = response.json()

    # Handle both dict and list response formats
    if isinstance(result, dict):
        print(f"Message: {result.get('message')}")
        if result.get('code') == 200:
            deps = result.get('obj', [])
            print(f"Dependencies found: {len(deps)}")
            test_results['php_parse'] = "PASS"
        else:
            print(f"Error: {str(result)[:200]}")
            test_results['php_parse'] = "FAIL"
    elif isinstance(result, list):
        deps = result
        print(f"Dependencies found: {len(deps)}")
        test_results['php_parse'] = "PASS"
    else:
        print(f"Unexpected response format: {type(result)}")
        test_results['php_parse'] = "FAIL"
except requests.exceptions.Timeout:
    print(f"TIMEOUT after 60 seconds")
    test_results['php_parse'] = "TIMEOUT"
except Exception as e:
    print(f"ERROR: {str(e)[:150]}")
    test_results['php_parse'] = "ERROR"

# ========== 测试 4: Ruby (ruby_parse) ==========
print("\n" + "-" * 90)
print("Test 4: Ruby Parser (/parse/ruby_parse)")
print("-" * 90)

ruby_dir = os.path.join(test_dir, "ruby_project")
os.makedirs(ruby_dir, exist_ok=True)

with open(os.path.join(ruby_dir, "Gemfile"), "w") as f:
    f.write("""source 'https://rubygems.org'

gem 'rails', '~> 6.0'
gem 'sqlite3'
gem 'puma'
""")

try:
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/parse/ruby_parse",
        params={"project_folder": ruby_dir},
        timeout=60
    )
    elapsed = time.time() - start

    print(f"Status: {response.status_code} | Response Time: {elapsed:.2f}s")
    result = response.json()

    # Handle both dict and list response formats
    if isinstance(result, dict):
        print(f"Message: {result.get('message')}")
        if result.get('code') == 200:
            deps = result.get('obj', [])
            print(f"Dependencies found: {len(deps)}")
            test_results['ruby_parse'] = "PASS"
        else:
            print(f"Error: {str(result)[:200]}")
            test_results['ruby_parse'] = "FAIL"
    elif isinstance(result, list):
        deps = result
        print(f"Dependencies found: {len(deps)}")
        test_results['ruby_parse'] = "PASS"
    else:
        print(f"Unexpected response format: {type(result)}")
        test_results['ruby_parse'] = "FAIL"
except requests.exceptions.Timeout:
    print(f"TIMEOUT after 60 seconds")
    test_results['ruby_parse'] = "TIMEOUT"
except Exception as e:
    print(f"ERROR: {str(e)[:150]}")
    test_results['ruby_parse'] = "ERROR"

# ========== 测试 5: Rust (rust_parse) ==========
print("\n" + "-" * 90)
print("Test 5: Rust Parser (/parse/rust_parse)")
print("-" * 90)

rust_dir = os.path.join(test_dir, "rust_project")
os.makedirs(rust_dir, exist_ok=True)

with open(os.path.join(rust_dir, "Cargo.toml"), "w") as f:
    f.write("""[package]
name = "myapp"
version = "0.1.0"

[dependencies]
serde = "1.0"
tokio = "1.0"
""")

try:
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/parse/rust_parse",
        params={"project_folder": rust_dir},
        timeout=60
    )
    elapsed = time.time() - start

    print(f"Status: {response.status_code} | Response Time: {elapsed:.2f}s")
    result = response.json()

    # Handle both dict and list response formats
    if isinstance(result, dict):
        print(f"Message: {result.get('message')}")
        if result.get('code') == 200:
            deps = result.get('obj', [])
            print(f"Dependencies found: {len(deps)}")
            test_results['rust_parse'] = "PASS"
        else:
            print(f"Error: {str(result)[:200]}")
            test_results['rust_parse'] = "FAIL"
    elif isinstance(result, list):
        deps = result
        print(f"Dependencies found: {len(deps)}")
        test_results['rust_parse'] = "PASS"
    else:
        print(f"Unexpected response format: {type(result)}")
        test_results['rust_parse'] = "FAIL"
except requests.exceptions.Timeout:
    print(f"TIMEOUT after 60 seconds")
    test_results['rust_parse'] = "TIMEOUT"
except Exception as e:
    print(f"ERROR: {str(e)[:150]}")
    test_results['rust_parse'] = "ERROR"

# ========== 测试 6: Erlang (erlang_parse) ==========
print("\n" + "-" * 90)
print("Test 6: Erlang Parser (/parse/erlang_parse)")
print("-" * 90)

erlang_dir = os.path.join(test_dir, "erlang_project")
os.makedirs(erlang_dir, exist_ok=True)

with open(os.path.join(erlang_dir, "rebar.config"), "w") as f:
    f.write("""{deps, [
  {cowboy, "2.9.0"},
  {jiffy, "1.0.8"}
]}.
""")

try:
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/parse/erlang_parse",
        params={"project_folder": erlang_dir},
        timeout=60
    )
    elapsed = time.time() - start

    print(f"Status: {response.status_code} | Response Time: {elapsed:.2f}s")
    result = response.json()

    # Handle both dict and list response formats
    if isinstance(result, dict):
        print(f"Message: {result.get('message')}")
        if result.get('code') == 200:
            deps = result.get('obj', [])
            print(f"Dependencies found: {len(deps)}")
            test_results['erlang_parse'] = "PASS"
        else:
            print(f"Error: {str(result)[:200]}")
            test_results['erlang_parse'] = "FAIL"
    elif isinstance(result, list):
        deps = result
        print(f"Dependencies found: {len(deps)}")
        test_results['erlang_parse'] = "PASS"
    else:
        print(f"Unexpected response format: {type(result)}")
        test_results['erlang_parse'] = "FAIL"
except requests.exceptions.Timeout:
    print(f"TIMEOUT after 60 seconds")
    test_results['erlang_parse'] = "TIMEOUT"
except Exception as e:
    print(f"ERROR: {str(e)[:150]}")
    test_results['erlang_parse'] = "ERROR"

# ========== 生成总结 ==========
print("\n" + "=" * 90)
print("测试结果汇总")
print("=" * 90)

for parser, result in test_results.items():
    status_icon = "OK" if result == "PASS" else "FAIL" if result == "FAIL" else "TIMEOUT" if result == "TIMEOUT" else "ERROR"
    print(f"[{status_icon}] {parser:20s} : {result:10s}")

print("\n" + "=" * 90)
