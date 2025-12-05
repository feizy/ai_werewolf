#!/usr/bin/env python3
"""
快速启动狼人杀游戏的简化脚本
"""

import requests
import time

def quick_start():
    """快速启动游戏"""
    base_url = "http://localhost:8001"

    print("🐺 快速启动狼人杀游戏...")

    # 1. 创建房间
    print("📝 创建房间...")
    create_data = {
        "name": "快速对战房间",
        "player_name": "房主"
    }

    try:
        response = requests.post(f"{base_url}/rooms", json=create_data)
        response.raise_for_status()
        room_info = response.json()
        room_id = room_info["room_id"]
        print(f"✅ 房间创建成功! ID: {room_id}")
    except Exception as e:
        print(f"❌ 创建房间失败: {e}")
        return

    # 2. 添加8个AI玩家
    print("👥 添加AI玩家...")
    ai_names = ["AI玩家1", "AI玩家2", "AI玩家3", "AI玩家4",
                "AI玩家5", "AI玩家6", "AI玩家7", "AI玩家8"]

    for i, name in enumerate(ai_names, 1):
        try:
            join_data = {
                "room_id": room_id,
                "player_name": name
            }

            response = requests.post(f"{base_url}/rooms/{room_id}/join", json=join_data)
            print(f"[{i}/8] 添加 {name}: ", end="")

            if response.status_code == 200:
                print("✅ 成功")
            else:
                error = response.json().get("detail", "")
                if "Role not assigned" in error:
                    print("⚠️  已添加 (Role not assigned 正常)")
                else:
                    print(f"❌ 失败: {error}")

        except Exception as e:
            print(f"❌ 添加 {name} 失败: {e}")

    # 3. 检查房间状态
    print("\n📊 检查房间状态...")
    try:
        response = requests.get(f"{base_url}/rooms/{room_id}")
        response.raise_for_status()
        room_status = response.json()

        print(f"   玩家数: {room_status['current_players']}/9")
        print(f"   已满员: {room_status['is_full']}")
        print(f"   可开始: {room_status['can_start_game']}")

        if room_status['can_start_game']:
            print("\n🎮 开始游戏...")
            try:
                response = requests.post(f"{base_url}/games/{room_id}/start")
                if response.status_code == 200:
                    result = response.json()
                    print("✅ 游戏开始成功!")
                    print(f"   游戏ID: {result.get('game_id', room_id)}")
                    print(f"   状态: {result.get('status', 'unknown')}")
                    print(f"\n🎉 游戏正在进行中...")
                    print(f"   房间ID: {room_id}")
                    print(f"   API: {base_url}/rooms/{room_id}")
                else:
                    error = response.json().get("detail", "未知错误")
                    print(f"❌ 开始游戏失败: {error}")

            except Exception as e:
                print(f"❌ 开始游戏异常: {e}")
        else:
            print("❌ 房间未准备好开始游戏")

    except Exception as e:
        print(f"❌ 获取房间状态失败: {e}")

if __name__ == "__main__":
    quick_start()