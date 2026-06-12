#!/usr/bin/env python3
"""Generate obfuscated source tree from Original_Src/ — never modifies the original.

Reads the pristine source from Original_Src/ (created once by `task setup`) and
produces .obfuscated/ with all identifying strings replaced by random values.
"""

import os
import random
import shutil
import string
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIG_SRC = os.path.join(BASE_DIR, "Original_Src")
OBF_DIR = os.path.join(BASE_DIR, ".obfuscated")
SEED_FILE = os.path.join(OBF_DIR, ".obf_seed")

OLD_MODID = "projecte"
OLD_MODNAME = "ProjectE"
OLD_PKG = "moze_intel.projecte"
OLD_PKG_PATH = "moze_intel/projecte"
OLD_MAVEN = "moze_intel"


def random_lower(n=10):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def random_capital(n=10):
    s = random_lower(n)
    return s[0].upper() + s[1:]


def load_or_generate():
    if os.path.exists(SEED_FILE):
        with open(SEED_FILE, 'r') as f:
            data = {}
            for line in f:
                k, v = line.strip().split('=', 1)
                data[k] = v
            return data['MODID'], data['MODNAME'], data['PKG'], data['PKG_PATH'], data['MAVEN']

    random.seed(os.urandom(16))
    modid = random_lower(random.randint(8, 12))
    modname = random_capital(random.randint(8, 12))
    p1 = random.choice(string.ascii_lowercase) + random_lower(random.randint(5, 8))
    p2 = random.choice(string.ascii_lowercase) + random_lower(random.randint(5, 8))
    pkg = f"{p1}.{p2}"
    pkg_path = pkg.replace('.', '/')
    maven = p1

    os.makedirs(OBF_DIR, exist_ok=True)
    with open(SEED_FILE, 'w') as f:
        f.write(f"MODID={modid}\n")
        f.write(f"MODNAME={modname}\n")
        f.write(f"PKG={pkg}\n")
        f.write(f"PKG_PATH={pkg_path}\n")
        f.write(f"MAVEN={maven}\n")
    return modid, modname, pkg, pkg_path, maven


NEW_MODID, NEW_MODNAME, NEW_PKG, NEW_PKG_PATH, NEW_MAVEN = load_or_generate()


def replace_in_file(filepath, old, new):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    count = content.count(old)
    if count > 0:
        content = content.replace(old, new)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    return count


def collect_files(root, exts):
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if any(fn.endswith(ext) for ext in exts):
                result.append(os.path.join(dirpath, fn))
    return result


# ── Guard: Original_Src must exist ──────────────────────────────
if not os.path.exists(ORIG_SRC):
    print(f"ERROR: Original_Src/ not found. Run 'task setup' first.")
    sys.exit(1)

# ── 1. Prepare clean .obfuscated/ ───────────────────────────────
print("=" * 60)
print(f"MODID   : {OLD_MODID} -> {NEW_MODID}")
print(f"MODNAME : {OLD_MODNAME} -> {NEW_MODNAME}")
print(f"Package : {OLD_PKG} -> {NEW_PKG}")
print(f"Maven   : {OLD_MAVEN} -> {NEW_MAVEN}")
print("=" * 60)

if os.path.exists(OBF_DIR):
    for item in os.listdir(OBF_DIR):
        item_path = os.path.join(OBF_DIR, item)
        if item == ".obf_seed":
            continue
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

print(f"\n[1] Copying Original_Src/ -> .obfuscated/ ...")
shutil.copytree(ORIG_SRC, OBF_DIR, dirs_exist_ok=True)
print("    Done.")

# ── 2. Java source files ────────────────────────────────────────
MAIN_JAVA = os.path.join(OBF_DIR, "main", "java")
API_JAVA = os.path.join(OBF_DIR, "api", "java")
DATAGEN_JAVA = os.path.join(OBF_DIR, "datagen", "java")
TEST_JAVA = os.path.join(OBF_DIR, "test", "java")

all_java = []
for d in [MAIN_JAVA, API_JAVA, DATAGEN_JAVA, TEST_JAVA]:
    if os.path.exists(d):
        all_java.extend(collect_files(d, ['.java']))

print(f"\n[2] Processing {len(all_java)} Java files...")
java_count = 0
for jf in all_java:
    java_count += replace_in_file(jf, OLD_PKG, NEW_PKG)
    java_count += replace_in_file(jf, OLD_PKG_PATH, NEW_PKG_PATH)
    java_count += replace_in_file(jf, f'"{OLD_MODID}"', f'"{NEW_MODID}"')
    java_count += replace_in_file(jf, f'"{OLD_MODNAME}"', f'"{NEW_MODNAME}"')
print(f"    Replacements: {java_count}")

# ── 3. Move source dirs to new package ──────────────────────────
for src_base in [MAIN_JAVA, API_JAVA, DATAGEN_JAVA, TEST_JAVA]:
    old_dir = os.path.join(src_base, OLD_PKG_PATH)
    new_dir = os.path.join(src_base, NEW_PKG_PATH)
    if os.path.exists(old_dir):
        os.makedirs(os.path.dirname(new_dir), exist_ok=True)
        shutil.move(old_dir, new_dir)
        old_parent = os.path.dirname(old_dir)
        if old_parent != src_base and os.path.exists(old_parent) and not os.listdir(old_parent):
            shutil.rmtree(old_parent)

# ── 4. Resource files (main resources + datagen generated) ──────
MAIN_RESOURCES = os.path.join(OBF_DIR, "main", "resources")
DATAGEN_RESOURCES = os.path.join(OBF_DIR, "datagen", "generated")

all_resources = []
for d in [MAIN_RESOURCES, DATAGEN_RESOURCES]:
    if os.path.exists(d):
        all_resources.extend(collect_files(d, ['.json', '.toml', '.cfg', '.mcmeta', '.txt']))

print(f"\n[3] Processing {len(all_resources)} resource files...")
res_count = 0
for rf in all_resources:
    res_count += replace_in_file(rf, f'{OLD_MODID}:', f'{NEW_MODID}:')
    res_count += replace_in_file(rf, f'"{OLD_MODID}"', f'"{NEW_MODID}"')
    res_count += replace_in_file(rf, f'assets/{OLD_MODID}/', f'assets/{NEW_MODID}/')
    res_count += replace_in_file(rf, f'/{OLD_MODID} ', f'/{NEW_MODID} ')
    res_count += replace_in_file(rf, f'itemGroup.{OLD_MODID}', f'itemGroup.{NEW_MODID}')
    res_count += replace_in_file(rf, f'"{OLD_MODNAME}"', f'"{NEW_MODNAME}"')
    res_count += replace_in_file(rf, f'modId="{OLD_MODID}"', f'modId="{NEW_MODID}"')
    res_count += replace_in_file(rf, f'[[dependencies.{OLD_MODID}]]', f'[[dependencies.{NEW_MODID}]]')
    res_count += replace_in_file(rf, f'displayName="{OLD_MODNAME}"', f'displayName="{NEW_MODNAME}"')
    res_count += replace_in_file(rf, OLD_PKG, NEW_PKG)
    res_count += replace_in_file(rf, OLD_PKG_PATH, NEW_PKG_PATH)
print(f"    Replacements: {res_count}")

# ── 5. Rename assets directory ──────────────────────────────────
for res_dir in [MAIN_RESOURCES, DATAGEN_RESOURCES]:
    old_assets = os.path.join(res_dir, "assets", OLD_MODID)
    new_assets = os.path.join(res_dir, "assets", NEW_MODID)
    if os.path.exists(old_assets):
        shutil.move(old_assets, new_assets)

# ── 6. Rename data directory (datagen/generated/data/projecte/) ─
old_data = os.path.join(DATAGEN_RESOURCES, "data", OLD_MODID)
new_data = os.path.join(DATAGEN_RESOURCES, "data", NEW_MODID)
if os.path.exists(old_data):
    shutil.move(old_data, new_data)
    print(f"\n[4] Data dir renamed: {OLD_MODID} -> {NEW_MODID}")

# ── 7. Patch build.gradle ───────────────────────────────────────
print(f"\n[5] Patching build.gradle...")
with open(os.path.join(BASE_DIR, "build.gradle"), 'r', encoding='utf-8') as f:
    bg = f.read()
bg_count = 0
for old, new in [
    (OLD_PKG, NEW_PKG),
    (OLD_PKG_PATH, NEW_PKG_PATH),
    (OLD_MAVEN, NEW_MAVEN),
    (f'"java.{OLD_MAVEN}"', f'"java.{NEW_MAVEN}"'),
    (f'"{OLD_MODID}"', f'"{NEW_MODID}"'),
    (f"'{OLD_MODID}'", f"'{NEW_MODID}'"),
    (OLD_MODNAME, NEW_MODNAME),
]:
    c = bg.count(old)
    if c > 0:
        bg = bg.replace(old, new)
        bg_count += c
with open(os.path.join(OBF_DIR, "build.gradle"), 'w', encoding='utf-8') as f:
    f.write(bg)
print(f"    Replacements: {bg_count}")

# ── Summary ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(".obfuscated/ ready — Original_Src/ untouched")
print("=" * 60)
print(f"MODID   : {NEW_MODID}")
print(f"MODNAME : {NEW_MODNAME}")
print(f"Package : {NEW_PKG}")
print(f"Maven   : {NEW_MAVEN}")
