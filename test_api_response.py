#!/usr/bin/env python3
"""
测试后端API响应
"""

import requests
import json

def test_api():
    """测试游戏状态API"""
    base_url = "http://localhost:8001"

    print("=== 测试游戏状态API ===")

    try:
        # 1. 创建房间
        print("1. 创建房间...")
        create_data = {
            "room_name": "测试房间",
            "max_players": 9,
            "llm_config": {
                "model_name": "glm-4.6",
                "api_key": "test-key",
                "provider": "anthropic"
            }
        }

        response = requests.post(f"{base_url}/rooms", json=create_data)
        if response.status_code != 200:
            print(f"创建房间失败: {response.text}")
            return

        room_data = response.json()
        room_id = room_data["room_id"]
        print(f"房间创建成功: {room_id}")

        # 2. 添加玩家
        print("2. 添加玩家...")
        player_names = ["牛姐", "依依", "路易", "国锋", "刘艺", "小倩", "费费", "流云", "再亮"]

        for i, name in enumerate(player_names, 1):
            join_data = {
                "room_id": room_id,
                "player_name": name,
                "ai_config": {"language": "zh"},
                "model_configuration": {
                    "model_name": "glm-4.6",
                    "api_key": f"key{i}",
                    "provider": "anthropic"
                }
            }

            response = requests.post(f"{base_url}/rooms/{room_id}/join", json=join_data)
            if response.status_code == 200:
                print(f"  {name}添加成功")
            else:
                print(f"  {name}添加失败: {response.text}")

        # 3. 开始游戏
        print("3. 开始游戏...")
        response = requests.post(f"{base_url}/games/{room_id}/start")
        if response.status_code == 200:
            game_data = response.json()
            game_id = game_data.get("game_id", room_id)
            print(f"游戏开始成功: {game_id}")
        else:
            print(f"游戏开始失败: {response.text}")
            return

        # 4. 获取游戏状态
        print("4. 获取游戏状态...")
        import time
        time.sleep(2)  # 等待游戏初始化

        response = requests.get(f"{base_url}/games/{game_id}/state")
        if response.status_code == 200:
            game_state = response.json()
            print("游戏状态获取成功!")
            print(f"  游戏ID: {game_state.get('session_id')}")
            print(f"  阶段: {game_state.get('current_phase')}")
            print(f"  天数: {game_state.get('day_count')}")
            print(f"  玩家数量: {len(game_state.get('players', []))}")
            print(f"  事件数量: {len(game_state.get('events', []))}")

            # 显示前3个事件
            events = game_state.get('events', [])
            if events:
                print("  前3个事件:")
                for i, event in enumerate(events[:3]):
                    print(f"    {i+1}. [{event.get('type')}] {event.get('content')[:50]}...")
            else:
                print("  没有事件数据!")

            # 检查players数据结构
            players = game_state.get('players', [])
            if players:
                player = players[0]
                print(f"  第一个玩家数据结构: {list(player.keys())}")
                if 'role_abilities' in player:
                    print(f"  角色能力: {player['role_abilities']}")

        else:
            print(f"获取游戏状态失败: {response.status_code}")
            print(f"响应: {response.text}")

    except Exception as e:
        print(f"测试异常: {e}")

if __name__ == "__main__":
    test_api()
