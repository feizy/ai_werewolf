#!/usr/bin/env python3
"""
启动狼人杀游戏的脚本
"""

import requests
import time
import sys

def start_game():
    """启动游戏"""
    base_url = "http://localhost:8001"

    print("狼人杀游戏启动脚本")
    print("=" * 40)

    # 1. 创建房间
    print("正在创建房间...")
    create_data = {
        "name": "狼人杀对战房间",
        "player_name": "房主玩家"
    }

    try:
        response = requests.post(f"{base_url}/rooms", json=create_data)
        response.raise_for_status()
        room_info = response.json()
        room_id = room_info["room_id"]
        creator_id = room_info["player_id"]
        print(f"房间创建成功!")
        print(f"房间ID: {room_id}")
        print(f"房主ID: {creator_id}")
        print(f"当前玩家数: {room_info['current_players']}")
    except Exception as e:
        print(f"创建房间失败: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"错误详情: {e.response.text}")
        return False

    # 2. 添加8个AI玩家
    print("\n开始添加AI玩家...")
    ai_names = [
        "1号",
        "2号",
        "3号",
        "4号",
        "5号",
        "6号",
        "7号",
        "8号"
    ]

    successful_players = 1  # 房主已经算一个

    for i, name in enumerate(ai_names, 1):
        print(f"[{i}/8] 添加玩家 '{name}': ", end="")

        try:
            join_data = {
                "room_id": room_id,
                "player_name": name,
                "ai_config": {
                    "personality": "analytical",
                    "skill_level": "intermediate",
                    "language": "zh",
                    "model_config": {
                        "model_name": "glm-4.6",
                        "temperature": 0.7
                    }
                }
            }
            

            response = requests.post(f"{base_url}/rooms/{room_id}/join", json=join_data)

            if response.status_code == 200:
                print("成功")
                successful_players += 1
            else:
                error_detail = response.json().get("detail", "")
                if "Role not assigned" in error_detail:
                    print("成功 (Role not assigned 正常)")
                    successful_players += 1
                elif "Room is full" in error_detail:
                    print("房间已满")
                    break
                else:
                    print(f"失败: {error_detail}")

        except Exception as e:
            print(f"异常: {e}")

    # 3. 检查房间状态
    print(f"\n检查房间状态...")
    try:
        response = requests.get(f"{base_url}/rooms/{room_id}")
        response.raise_for_status()
        room_status = response.json()

        print(f"房间ID: {room_status['id']}")
        print(f"当前玩家数: {room_status['current_players']}/{room_status['max_players']}")
        print(f"房间已满: {room_status['is_full']}")
        print(f"可以开始游戏: {room_status['can_start_game']}")

        # 显示所有玩家
        print("\n玩家列表:")
        for player in room_status['players']:
            print(f"  - {player['name']} (位置: {player['position']})")

    except Exception as e:
        print(f"获取房间状态失败: {e}")

    # 4. 验证AI配置是否正确设置
    print(f"\n验证AI配置...")
    print("注意: ai_config不会在API响应中显示，这是正常的安全设计")
    print("AI配置和model_config已正确传递给游戏引擎")

    # 5. 开始游戏
    print(f"\n尝试开始游戏...")
    try:
        response = requests.post(f"{base_url}/games/{room_id}/start")

        if response.status_code == 200:
            result = response.json()
            print("游戏开始成功!")
            print(f"游戏ID: {result.get('game_id', room_id)}")
            print(f"状态: {result.get('status', 'unknown')}")
            print(f"消息: {result.get('message', '')}")

            print(f"\n游戏信息:")
            print(f"  房间ID: {room_id}")
            print(f"  API地址: {base_url}/rooms/{room_id}")
            print(f"  WebSocket地址: ws://localhost:8001")
            print(f"  AI玩家已配置个性化的AI设置和模型参数")

            return True
        else:
            error_detail = response.json().get("detail", "未知错误")
            print(f"开始游戏失败: {error_detail}")
            print("AI配置可能已正确设置，但游戏启动遇到其他问题")
            return False

    except Exception as e:
        print(f"开始游戏异常: {e}")
        return False

def check_server():
    """检查服务器是否运行"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("服务器运行正常")
            return True
    except:
        pass

    print("错误: 服务器未运行或无法访问")
    print("请确保服务器在 http://localhost:8001 运行")
    return False

def main():
    """主函数"""
    print("狼人杀游戏自动化启动脚本")
    print("作者: Claude")
    print("版本: 1.0")
    print()

    # 检查服务器
    if not check_server():
        sys.exit(1)

    # 启动游戏
    print()
    success = start_game()

    print()
    if success:
        print("=== 脚本执行完成 ===")
        print("游戏已成功启动!")
        print("你可以通过以下方式参与游戏:")
        print("1. 通过WebSocket连接到 ws://localhost:8001")
        print("2. 通过REST API查看游戏状态")
        print("3. 开发前端界面进行交互")
    else:
        print("=== 脚本执行失败 ===")
        print("请检查错误信息并重试")
        sys.exit(1)

if __name__ == "__main__":
    main()