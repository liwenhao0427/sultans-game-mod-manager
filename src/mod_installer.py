import os
import sys
import shutil
import subprocess
import re
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
    
    # 获取应用程序路径
    script_dir = get_application_path()
    
    # 备份目录和配置目录
    bak_dir = os.path.join(script_dir, "Sultan's Game_Data", "StreamingAssets", "bak")
    config_dir = os.path.join(script_dir, "Sultan's Game_Data", "StreamingAssets", "config")
    
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
                    # 这是ADD模式的备份，删除目标文件
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

def process_mod(json_file, config_file, bak_dir):
    """处理单个MOD"""
    script_dir = get_application_path()
    config_dir = os.path.join(script_dir, "Sultan's Game_Data", "StreamingAssets", "config")
    
    # 读取配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 确保至少有两行
        if len(lines) < 2:
            print(f"  X 配置文件格式错误: {config_file}")
            return 2
        
        mode = lines[0].strip()
        target_path = lines[1].strip()
        val1 = lines[2].strip() if len(lines) > 2 else ""
        val2 = lines[3].strip() if len(lines) > 3 else ""
        
        # 打印原始目标路径
        print(f"  - 原始目标路径: {target_path}")
        
        # 修复：检查target_path是否已经包含了config路径前缀
        if target_path.startswith("Sultan's Game_Data/StreamingAssets/config/") or \
           target_path.startswith("Sultan's Game_Data\\StreamingAssets\\config\\"):
            # 如果包含前缀，则从target_path中提取相对路径
            parts = target_path.split('config/', 1) if '/' in target_path else target_path.split('config\\', 1)
            if len(parts) > 1:
                target_path = parts[1]
        
        # 设置目标文件完整路径
        target_file = os.path.join(config_dir, target_path)
        print(f"  - 处理后目标路径: {target_file}")
        
        # 为备份创建目录结构
        bak_file = os.path.join(bak_dir, f"{target_path}.bak")
        ensure_directory(os.path.dirname(bak_file))
        
        # 统一处理逻辑：不再区分ADD和REPLACE模式
        if mode == "ADD" or mode == "REPLACE":
            # 检查目标文件是否存在
            if not os.path.exists(target_file):
                print("  - 模式: 新增文件")
                
                # 确保目标目录存在
                ensure_directory(os.path.dirname(target_file))
                
                # 创建一个1字节的备份文件表示这是新增模式
                with open(bak_file, 'w') as f:
                    f.write("")
                
                # 复制文件
                shutil.copy2(json_file, target_file)
                print(f"  √ 新增文件: {target_file}")
            else:
                print("  - 模式: 替换文件")
                
                # 创建备份(如果不存在)
                if not os.path.exists(bak_file):
                    shutil.copy2(target_file, bak_file)
                    print(f"  + 创建备份: {bak_file}")
                
                # 复制文件
                shutil.copy2(json_file, target_file)
                print(f"  √ 替换文件: {target_file}")
            
            return 0
        
        # 其他模式需要目标文件存在
        if not os.path.exists(target_file):
            print(f"  X 目标文件不存在: {target_file}")
            return 2
        
        # 创建备份(如果不存在)
        if not os.path.exists(bak_file):
            shutil.copy2(target_file, bak_file)
            print(f"  + 创建备份: {bak_file}")
        
        # 根据不同模式执行操作
        if mode == "REPLACE0":
            print("  - 模式: 替换标记行")
            # 读取源文件内容
            with open(json_file, 'r', encoding='utf-8') as f:
                source_content = f.read()
            
            # 读取目标文件
            with open(target_file, 'r', encoding='utf-8') as f:
                target_content = f.readlines()
            
            # 替换包含val1的行
            new_content = []
            for line in target_content:
                if val1 in line:
                    new_content.append(source_content + '\n')
                else:
                    new_content.append(line)
            
            # 写回文件
            with open(target_file, 'w', encoding='utf-8') as f:
                f.writelines(new_content)
            
            print(f"  √ 替换标记行: {val1}")
            
        elif mode == "REPLACE1":
            print("  - 模式: 替换标记间内容")
            # 读取源文件内容
            with open(json_file, 'r', encoding='utf-8') as f:
                source_content = f.read().strip()  # 去除源文件内容的首尾空白
            
            # 读取目标文件
            with open(target_file, 'r', encoding='utf-8') as f:
                target_content = f.read()
            
            # 修改后的逻辑：完全替换包含标记在内的中间内容
            # 查找val1和val2在文件中的位置
            start_pos = target_content.find(val1)
            end_pos = target_content.find(val2, start_pos) + len(val2)
            
            if start_pos != -1 and end_pos != -1:
                # 构建新内容：前部分 + 源文件内容 + 后部分
                new_content = target_content[:start_pos] + source_content + target_content[end_pos:]
                
                # 写回文件
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"  √ 替换内容: [{val1}]到[{val2}]之间（包含标记行）")
            else:
                print(f"  X 未找到标记: [{val1}]或[{val2}]")
                return 3
            
        elif mode == "APPEND":
            print("  - 模式: 追加到文件末尾")
            # 读取源文件内容
            with open(json_file, 'r', encoding='utf-8') as f:
                source_content = f.read()
            
            if not val1:
                # 直接追加到文件末尾
                with open(target_file, 'a', encoding='utf-8') as f:
                    f.write(source_content)
                print("  √ 追加到文件末尾")
            else:
                # 追加到倒数第val1行
                with open(target_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 计算插入位置
                insert_pos = max(0, len(lines) - int(val1))
                
                # 插入内容
                lines.insert(insert_pos, source_content + '\n')
                
                # 写回文件
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                print(f"  √ 追加到倒数第{val1}行")
            
        elif mode == "INSERT":
            print("  - 模式: 在标记后插入")
            # 读取源文件内容
            with open(json_file, 'r', encoding='utf-8') as f:
                source_content = f.read()
            
            # 读取目标文件
            with open(target_file, 'r', encoding='utf-8') as f:
                target_content = f.readlines()
            
            # 在包含val1的行后插入内容
            new_content = []
            for line in target_content:
                new_content.append(line)
                if val1 in line:
                    new_content.append(source_content + '\n')
            
            # 写回文件
            with open(target_file, 'w', encoding='utf-8') as f:
                f.writelines(new_content)
            
            print(f"  √ 在[{val1}]后插入内容")
            
        else:
            print(f"  X 未知模式: {mode}")
            return 3
        
        return 0
    
    except Exception as e:
        print(f"  X 处理MOD时出错: {str(e)}")
        return 4

def install_mods():
    """安装MOD主函数"""
    # 获取应用程序路径
    script_dir = get_application_path()
    
    # 创建备份目录
    bak_dir = os.path.join(script_dir, "Sultan's Game_Data", "StreamingAssets", "bak")
    ensure_directory(bak_dir)
    
    # 设置计数器
    total_mods = 0
    success_mods = 0
    skipped_mods = 0
    failed_mods = 0
    
    # 递归处理Mods目录
    mods_dir = os.path.join(script_dir, "Mods")
    print(f"[调试] MOD目录: {mods_dir}")
    print(f"[调试] MOD目录是否存在: {os.path.exists(mods_dir)}")
    
    if not os.path.exists(mods_dir):
        print(f"警告: MOD目录不存在 - {mods_dir}")
        print("尝试创建MOD目录...")
        try:
            os.makedirs(mods_dir)
            print("MOD目录创建成功")
        except Exception as e:
            print(f"创建MOD目录失败: {str(e)}")
    
    # 列出MOD目录中的所有文件
    if os.path.exists(mods_dir):
        print("MOD目录内容:")
        for item in os.listdir(mods_dir):
            print(f"  - {item}")
    
    for root, _, files in os.walk(mods_dir):
        for file in files:
            if file.endswith('.json'):
                json_file = os.path.join(root, file)
                config_file = os.path.splitext(json_file)[0] + '.config'
                
                total_mods += 1
                print(f"[读取配置文件] {config_file}")
                
                # 检查配置文件是否存在
                if os.path.exists(config_file):
                    print(f"[处理] {json_file}")
                    result = process_mod(json_file, config_file, bak_dir)
                    
                    if result == 0:
                        success_mods += 1
                    elif result == 1:
                        skipped_mods += 1
                    else:
                        failed_mods += 1
                else:
                    print(f"[跳过] {json_file} - 找不到配置文件")
                    skipped_mods += 1
    
    print("=" * 38)
    print(f"安装完成! 总计: {total_mods} 个MOD")
    print(f"  成功: {success_mods}")
    print(f"  跳过: {skipped_mods}")
    print(f"  失败: {failed_mods}")
    print("=" * 38)

def main():
    """主函数"""
    print_header("MOD安装管理工具")
    
    # 执行还原操作
    if not restore_mods():
        print("还原操作失败，安装中止")
        input("按任意键继续...")
        return
    
    # 安装MOD
    print("[安装阶段] 开始处理MOD文件...")
    install_mods()
    
    input("按任意键继续...")

if __name__ == "__main__":
    main()