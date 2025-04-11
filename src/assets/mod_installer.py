import os
import sys
import shutil
import subprocess
import re
import json  # 添加json模块导入
from pathlib import Path

def print_header(title):
    """打印标题栏"""
    print("=" * 38)
    print(f"{title:^38}")
    print("=" * 38)

def ensure_directory(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_application_path():
    """获取应用程序路径，兼容打包环境"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的环境
        application_path = os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    print(f"[调试] 应用程序路径: {application_path}")
    return application_path

def restore_mods():
    """执行还原操作"""
    print("[预处理] 正在执行还原操作...")
    
    # 使用游戏路径而不是应用程序路径
    game_path = get_game_path()
    
    # 备份目录和配置目录
    bak_dir = os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "bak")
    config_dir = os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "config")
    
    print(f"[调试] 备份目录: {bak_dir}")
    print(f"[调试] 配置目录: {config_dir}")
    
    if not os.path.exists(bak_dir):
        print("没有找到备份文件，无需还原")
        return True
    
    # 统计计数器
    restored_count = 0
    
    # 遍历备份目录中的所有文件
    for root, _, files in os.walk(bak_dir):
        for file in files:
            if file.endswith('.bak'):
                bak_file = os.path.join(root, file)
                
                # 计算原始文件路径
                rel_path = os.path.relpath(bak_file, bak_dir)
                rel_path = rel_path[:-4]  # 移除.bak后缀
                
                # 修复：检查rel_path是否包含重复路径
                if rel_path.startswith("Sultan's Game_Data/StreamingAssets/config/") or \
                   rel_path.startswith("Sultan's Game_Data\\StreamingAssets\\config\\"):
                    parts = rel_path.split('config/', 1) if '/' in rel_path else rel_path.split('config\\', 1)
                    if len(parts) > 1:
                        rel_path = parts[1]
                
                target_file = os.path.join(config_dir, rel_path)
                
                # 检查备份文件大小
                if os.path.getsize(bak_file) <= 1:
                    # 这是空备份文件，表示原始文件不存在或是ADD模式的备份，删除目标文件
                    if os.path.exists(target_file):
                        os.remove(target_file)
                        print(f"  - 删除文件: {target_file}")
                        restored_count += 1
                else:
                    # 这是其他模式的备份，恢复文件
                    target_dir = os.path.dirname(target_file)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    
                    shutil.copy2(bak_file, target_file)
                    print(f"  - 恢复文件: {target_file}")
                    restored_count += 1
                
                # 删除备份文件
                os.remove(bak_file)
    
    # 删除空目录
    for root, dirs, files in os.walk(bak_dir, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)
    
    print("=" * 38)
    print("还原完成")
    print(f"  还原: {restored_count} 个文件")
    print("=" * 38)
    
    return True

def clear_bak_files():
    """清空bak文件夹中的文件"""
    # 使用游戏路径而不是应用程序路径
    game_path = get_game_path()
    bak_dir = os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "bak")
    
    for root, _, files in os.walk(bak_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) > 0:
                os.remove(file_path)
                print(f"[清空] 删除文件: {file_path}")

def process_mod(json_file, bak_dir):
    """处理单个MOD，使用modConfig.json作为参数"""
    # 使用游戏路径而不是应用程序路径
    game_path = get_game_path()
    config_dir = os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "config")
    
    # 读取modConfig.json文件
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            mod_config = json.load(f)
        
        # 获取MOD名称
        mod_name = os.path.basename(os.path.dirname(json_file))
        print(f"====================\n[处理] MOD: {mod_name}\n====================")
        
        # 检查files字段是否存在
        if 'files' not in mod_config or not mod_config['files']:
            print(f"[警告] {mod_name} 的modConfig.json中没有files字段或为空")
            return False
        
        # 处理每个文件
        for file_info in mod_config['files']:
            if 'source' not in file_info:
                print(f"[警告] {mod_name} 的一个文件条目缺少source字段")
                continue
                
            source_file = os.path.join(os.path.dirname(json_file), file_info['source'])
            
            # 确定目标路径
            target_path = file_info.get('destination', file_info['source'])
            target_file = os.path.join(config_dir, target_path)
            
            # 确定操作模式
            mode = file_info.get('mode', 'REPLACE')
            
            # 获取可选参数
            val1 = file_info.get('val1', '')
            val2 = file_info.get('val2', '')
            
            # 确保目标目录存在
            target_dir = os.path.dirname(target_file)
            ensure_directory(target_dir)
            
            # 备份原始文件（如果存在且尚未备份）
            backup_file = os.path.join(bak_dir, target_path + '.bak')
            backup_dir = os.path.dirname(backup_file)
            ensure_directory(backup_dir)
            
            # 创建备份文件
            if not os.path.exists(backup_file):
                ensure_directory(os.path.dirname(backup_file))
                if os.path.exists(target_file):
                    # 如果目标文件存在，创建完整备份
                    shutil.copy2(target_file, backup_file)
                    print(f"[备份] {target_path}")
                else:
                    # 如果目标文件不存在，创建空备份文件
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write('')  # 写入空内容
                    print(f"[空备份] {target_path} (目标文件不存在)")
            
            # 根据模式处理文件
            if mode == 'REPLACE':
                # 完全替换模式
                shutil.copy2(source_file, target_file)
                print(f"[替换] {target_path}")
            elif mode == 'REPLACE0':
                # 查找替换文本模式
                if os.path.exists(target_file):
                    with open(target_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    with open(source_file, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                    
                    # 替换文本
                    content = content.replace(val1, new_content)
                    
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"[文本替换] {target_path}")
                else:
                    print(f"[错误] 目标文件不存在，无法执行文本替换: {target_path}")
            elif mode == 'REPLACE1':
                # 替换两个标记间内容
                if os.path.exists(target_file):
                    with open(target_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    with open(source_file, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                    
                    # 查找标记之间的内容并替换
                    start_pos = content.find(val1)
                    end_pos = content.find(val2, start_pos + len(val1))
                    
                    if start_pos != -1 and end_pos != -1:
                        new_full_content = content[:start_pos + len(val1)] + new_content + content[end_pos:]
                        
                        with open(target_file, 'w', encoding='utf-8') as f:
                            f.write(new_full_content)
                        
                        print(f"[区间替换] {target_path}")
                    else:
                        print(f"[错误] 未找到标记，无法执行区间替换: {target_path}")
                else:
                    print(f"[错误] 目标文件不存在，无法执行区间替换: {target_path}")
            elif mode == 'APPEND':
                # 末尾追加内容到倒数第val1行
                with open(source_file, 'r', encoding='utf-8') as f:
                    append_content = f.read()
                
                if os.path.exists(target_file):
                    with open(target_file, 'r+', encoding='utf-8') as f:
                        lines = f.readlines()
                        try:
                            # 将内容插入到倒数第val1行之前
                            insert_index = len(lines) - int(val1)
                            if insert_index < 0:
                                insert_index = 0
                            lines.insert(insert_index, append_content + '\n')
                            f.seek(0)
                            f.writelines(lines)
                        except ValueError:
                            print(f"[错误] val1参数无效: {val1}")
                else:
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(append_content)
                
                print(f"[追加] {target_path}")
            elif mode == 'INSERT':
                # 指定位置插入内容，从下一行开始插入
                if os.path.exists(target_file):
                    with open(target_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    with open(source_file, 'r', encoding='utf-8') as f:
                        insert_content = f.read()
                    
                    # 查找插入位置
                    insert_pos = content.find(val1)
                    
                    if insert_pos != -1:
                        # 插入内容从下一行开始
                        new_content = content[:insert_pos + len(val1)] + '\n' + insert_content + content[insert_pos + len(val1):]
                        
                        with open(target_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print(f"[插入] {target_path}")
                    else:
                        print(f"[错误] 未找到插入标记，无法执行插入: {target_path}")
                else:
                    print(f"[错误] 目标文件不存在，无法执行插入: {target_path}")
            else:
                print(f"[错误] 未知的操作模式: {mode}")
        
        return True
    except Exception as e:
        print(f"[错误] 处理MOD时出错: {str(e)}")
        return False

def install_mods():
    """安装MOD主函数"""
    # 使用游戏路径而不是应用程序路径
    game_path = get_game_path()
    script_dir = get_application_path()
    
    # 创建备份目录
    bak_dir = os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "bak")
    ensure_directory(bak_dir)
    
    # 获取Mods目录
    mods_dir = os.path.join(script_dir, "Mods")
    if not os.path.exists(mods_dir):
        print("[错误] Mods目录不存在")
        return False
    
    # 遍历Mods目录
    success_count = 0
    total_count = 0
    
    for mod_name in os.listdir(mods_dir):
        mod_dir = os.path.join(mods_dir, mod_name)
        if not os.path.isdir(mod_dir):
            continue
        
        # 查找modConfig.json文件
        mod_config_file = os.path.join(mod_dir, "modConfig.json")
        if not os.path.exists(mod_config_file):
            print(f"[跳过] {mod_name} 没有modConfig.json文件")
            continue
        
        total_count += 1
        
        # 处理MOD
        if process_mod(mod_config_file, bak_dir):
            success_count += 1
    
    print(f"\n[完成] 共处理 {total_count} 个MOD，成功 {success_count} 个")
    return True

def get_game_path():
    """获取游戏路径"""
    possible_paths = [
        r"C:\Program Files (x86)\Steam\steamapps\common\Sultan's Game",
        r"C:\Program Files\Steam\steamapps\common\Sultan's Game",
        r"D:\Program Files (x86)\Steam\steamapps\common\Sultan's Game",
        r"D:\Program Files\Steam\steamapps\common\Sultan's Game",
        r"E:\Program Files (x86)\Steam\steamapps\common\Sultan's Game",
        r"E:\Program Files\Steam\steamapps\common\Sultan's Game",
        r"C:\Games\Steam\steamapps\common\Sultan's Game",
        r"D:\Games\Steam\steamapps\common\Sultan's Game",
        r"E:\Games\Steam\steamapps\common\Sultan's Game",
        r"C:\Game\Steam\steamapps\common\Sultan's Game",
        r"D:\Game\Steam\steamapps\common\Sultan's Game",
        r"E:\Game\Steam\steamapps\common\Sultan's Game"
    ]
    possible_paths.append(get_application_path())  # 添加应用程序路径

    # 检查缓存的游戏路径
    config_file = 'game_path_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            cached_path = json.load(f).get('game_path')
            if cached_path and os.path.exists(cached_path):
                print(f"[信息] 使用缓存的游戏路径: {cached_path}")
                return cached_path

    # 检查可能的路径
    for path in possible_paths:
        if os.path.exists(path):
            print(f"[信息] 找到游戏路径: {path}")
            return path

    # 提示用户输入路径
    while True:
        user_input = input("未找到游戏路径，请输入游戏根目录（应包含'Sultan's Game'文件夹）: ").strip()
        if "Sultan's Game" in user_input:
            game_path = user_input.split("Sultan's Game")[0] + "Sultan's Game"
            if os.path.exists(game_path):
                # 缓存路径
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump({'game_path': game_path}, f, ensure_ascii=False, indent=2)
                print(f"[信息] 使用用户输入的游戏路径: {game_path}")
                return game_path
            else:
                print("[警告] 输入的路径不存在，请确认后重试。")
        else:
            confirm = input("输入的路径可能不是游戏路径，输入 '我确定这就是游戏路径' 以强制使用该路径: ").strip()
            if confirm == "我确定这就是游戏路径":
                # 缓存路径
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump({'game_path': user_input}, f, ensure_ascii=False, indent=2)
                print(f"[信息] 强制使用用户输入的游戏路径: {user_input}")
                return user_input

def check_game_update(game_path):
    """检查游戏是否更新"""
    game_exe_path = os.path.join(game_path, "Sultan's Game.exe")
    config_file = 'game_path_config.json'
    
    if not os.path.exists(game_exe_path):
        print("[错误] 找不到游戏可执行文件，无法检查更新")
        return False
    
    # 获取当前游戏文件的更新时间
    current_mod_time = os.path.getmtime(game_exe_path)
    
    # 读取配置文件中的上次更新时间
    last_mod_time = None
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            last_mod_time = config_data.get('last_mod_time')
        
    # 如果游戏文件更新时间不同，说明游戏已更新
    if last_mod_time is None:
        print("[信息] 检测到配置文件不存在，将创建新的配置文件")
        
        # 更新配置文件中的更新时间
        with open(config_file, 'w', encoding='utf-8') as f:
            config_data = {'game_path': game_path, 'last_mod_time': current_mod_time}
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        return False
    
    # 如果游戏文件更新时间不同，说明游戏已更新
    if current_mod_time != last_mod_time:
        print("[信息] 检测到游戏更新，清空bak文件夹中的文件")
        clear_bak_files(game_path)
        
        # 更新配置文件中的更新时间
        with open(config_file, 'w', encoding='utf-8') as f:
            config_data = {'game_path': game_path, 'last_mod_time': current_mod_time}
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        return True
    
    return False

def clear_bak_files(game_path):
    """清空bak文件夹中的文件"""
    bak_dir = os.path.join(game_path, "Sultan's Game_Data", "StreamingAssets", "bak")
    
    for root, _, files in os.walk(bak_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) > 0:
                os.remove(file_path)
                print(f"[清空] 删除文件: {file_path}")

def main():
    """主函数"""
    print_header("MOD安装管理工具")
    
    # 获取游戏路径
    game_path = get_game_path()
    if not game_path:
        print("无法确定游戏路径，安装中止")
        input("按任意键继续...")
        return
    
    # 检查游戏是否更新
    check_game_update(game_path)
    
    # 执行还原操作
    if not restore_mods():
        print("还原操作失败，安装中止")
        input("按任意键继续...")
        return
    
    # 安装MOD
    print("[安装阶段] 开始处理MOD文件...\n")
    install_mods()
    
    input("按任意键继续...")

if __name__ == "__main__":
    main()
