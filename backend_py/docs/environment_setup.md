# AI狼人杀游戏后端环境配置指南

本指南将帮助您配置AI狼人杀游戏后端开发环境，重点介绍如何通过.env文件配置API密钥。

## 1. Python环境准备

确保您的Python版本 ≥ 3.9：

```bash
python --version
```

如果版本过低，请安装Python 3.9或更高版本。

## 2. 安装依赖

```bash
# 进入项目目录
cd backend_py

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 如果您有NVIDIA GPU并支持CUDA，可以安装GPU版本的PyTorch
# 访问 https://pytorch.org/get-started/locally/ 获取适合您系统的命令
```

## 3. 配置API密钥（.env文件方式）

我们将使用.env文件方式配置API密钥。复制示例配置文件：

```bash
cp .env.example .env
```

然后编辑.env文件，配置您的API密钥。

### 3.1 API密钥配置选项

#### 方式1: 智谱AI (推荐，支持中文)

获取地址: https://open.bigmodel.cn/

```bash
# 在.env文件中配置
ZHIPU_API_KEY=your_actual_zhipu_api_key_here
MODEL_NAME=glm-4.6
```

#### 方式2: OpenAI

获取地址: https://platform.openai.com/api-keys

```bash
# 在.env文件中配置
OPENAI_API_KEY=your_actual_openai_api_key_here
MODEL_NAME=gpt-4
```

#### 方式3: Anthropic Claude

获取地址: https://console.anthropic.com/

```bash
# 在.env文件中配置
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
MODEL_NAME=claude-3-sonnet-20240229
```

### 3.2 配置优先级

系统会按以下优先级查找API密钥：

1. **model_config参数** - 代码中直接传入的配置
2. **环境变量** - .env文件中设置的环境变量
3. **配置文件** - model_configs.py文件中的配置

### 3.3 配置示例

创建`.env`文件并添加以下内容：

```bash
# 选择一个API提供商进行配置

# 智谱AI配置（推荐）
ZHIPU_API_KEY=your_zhipu_api_key_here
MODEL_NAME=glm-4.6

# 或者使用OpenAI
# OPENAI_API_KEY=your_openai_api_key_here
# MODEL_NAME=gpt-4

# 或者使用Anthropic Claude
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# MODEL_NAME=claude-3-sonnet-20240229

# 其他配置保持默认即可
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 3.4 验证API密钥配置

创建一个简单的测试脚本验证配置：

```python
# test_api_config.py
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def test_api_keys():
    """测试API密钥配置"""
    zhipu_key = os.getenv("ZHIPU_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    print("=== API密钥配置检查 ===")
    print(f"智谱AI API密钥: {'✓ 已配置' if zhipu_key else '✗ 未配置'}")
    print(f"OpenAI API密钥: {'✓ 已配置' if openai_key else '✗ 未配置'}")
    print(f"Anthropic API密钥: {'✓ 已配置' if anthropic_key else '✗ 未配置'}")

    # 检查至少配置了一个API密钥
    if any([zhipu_key, openai_key, anthropic_key]):
        print("\n✓ API密钥配置完成，可以启动游戏服务器")
    else:
        print("\n✗ 未配置任何API密钥，请至少配置一个API提供商")

if __name__ == "__main__":
    test_api_keys()
```

运行测试：

```bash
python test_api_config.py
```

## 4. 启动后端服务

```bash
# 确保虚拟环境已激活
# 加载.env文件配置
source .env  # Linux/macOS
# 或者在Windows中，.env文件会自动被python-dotenv加载

# 运行数据库迁移
python -m alembic upgrade head

# 启动开发服务器
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 5. 验证安装

访问以下URL验证服务是否正常运行：

- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- WebSocket测试: http://localhost:8000/game/websocket/test

## 6. API密钥获取详细指南

### 6.1 智谱AI API密钥获取

1. 访问 https://open.bigmodel.cn/
2. 注册并登录账号
3. 进入控制台
4. 点击"API Key管理"
5. 创建新的API Key
6. 复制API Key到.env文件中的`ZHIPU_API_KEY`

### 6.2 OpenAI API密钥获取

1. 访问 https://platform.openai.com/api-keys
2. 登录或注册OpenAI账号
3. 点击"Create new secret key"
4. 复制生成的API Key到.env文件中的`OPENAI_API_KEY`

### 6.3 Anthropic API密钥获取

1. 访问 https://console.anthropic.com/
2. 登录或注册Anthropic账号
3. 在API Keys部分创建新的API Key
4. 复制API Key到.env文件中的`ANTHROPIC_API_KEY`

## 常见问题

### 问题1: 找不到agentscope模块
**解决方案**: 确保已安装AgentScope：
```bash
pip install agentscope
```

### 问题2: API密钥未生效
**解决方案**:
1. 确保.env文件在项目根目录
2. 检查.env文件中是否有空格或特殊字符
3. 确保使用了正确的环境变量名称

### 问题3: 模型调用失败
**解决方案**:
1. 验证API密钥是否正确
2. 检查网络连接
3. 确认模型名称是否正确
4. 检查API配额是否充足

### 问题4: 数据库连接失败
**解决方案**: 检查数据库路径配置，默认使用SQLite。

### 问题5: 多个API密钥冲突
**解决方案**: 系统会按优先级使用第一个可用的API密钥，确保只配置一个主要的API提供商。

## 下一步

环境配置完成后，您可以：
1. 查看API文档了解可用接口
2. 使用WebSocket客户端测试游戏功能
3. 开始开发前端应用
4. 测试AI代理的决策能力

## 技术支持

如果遇到问题，请检查：
1. Python版本是否符合要求
2. 所有依赖是否正确安装
3. API密钥配置是否正确
4. .env文件格式是否正确