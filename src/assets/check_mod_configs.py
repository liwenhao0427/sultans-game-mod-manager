import os
import json
import datetime

def ensure_directory(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_default_config(mod_dir, mod_name):
    """为指定的MOD目录生成默认的modConfig.json文件"""
    # 获取当前日期
    current_date = datetime.datetime.now().strftime("%Y.%m.%d")
    
    # 创建默认配置
    default_config = {
        "name": mod_name,
        "author": "未知",
        "version": "1.0.0",
        "gameVersion": "未知",
        "updateDate": current_date,
        "tag": ["自动导入"],
        "source": {
            "name": "自动生成",
            "url": "https://github.com/liwenhao0427/sultans-game-mod-manager"
        },
        "files": []
    }
    
    # 遍历MOD目录中的所有文件
    for root, _, files in os.walk(mod_dir):
        for file in files:
            # 跳过modConfig.json文件本身
            if file == "modConfig.json":
                continue
                
            # 计算相对路径
            rel_path = os.path.relpath(os.path.join(root, file), mod_dir)
            
            # 添加到files列表
            default_config["files"].append({
                "source": rel_path.replace("\\", "/"),  # 确保使用正斜杠
                "mode": "REPLACE"
            })
    
    # 写入modConfig.json文件
    config_path = os.path.join(mod_dir, "modConfig.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    print(f"已为 {mod_name} 生成默认配置文件，包含 {len(default_config['files'])} 个文件")
    return len(default_config['files'])

def check_mod_configs():
    """检查所有MOD目录是否都有modConfig.json文件"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 获取Mods目录
    mods_dir = os.path.join(script_dir, "Mods")
    if not os.path.exists(mods_dir):
        print(f"错误: Mods目录不存在 ({mods_dir})")
        return
    
    print(f"开始检查 {mods_dir} 目录下的MOD配置...")
    
    # 统计信息
    total_mods = 0
    missing_configs = 0
    total_files_added = 0
    
    # 遍历Mods目录下的所有文件夹
    for mod_name in os.listdir(mods_dir):
        mod_dir = os.path.join(mods_dir, mod_name)
        
        # 只处理目录
        if not os.path.isdir(mod_dir):
            continue
            
        total_mods += 1
        
        # 检查是否存在modConfig.json
        config_file = os.path.join(mod_dir, "modConfig.json")
        if not os.path.exists(config_file):
            print(f"发现缺少配置文件: {mod_name}")
            missing_configs += 1
            
            # 生成默认配置
            files_added = generate_default_config(mod_dir, mod_name)
            total_files_added += files_added
    
    # 打印统计信息
    print("\n检查完成!")
    print(f"总计 {total_mods} 个MOD目录")
    print(f"发现 {missing_configs} 个缺少配置文件的MOD")
    print(f"总共添加了 {total_files_added} 个文件到配置中")

if __name__ == "__main__":
    check_mod_configs()
    input("按任意键退出...")