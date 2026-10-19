"""
OASIS 双平台并行模拟预设脚本
同时运行Twitter和Reddit模拟，读取相同的配置文件

功能特性:
- 双平台（Twitter + Reddit）并行模拟
- 完成模拟后不立即关闭环境，进入等待命令模式
- 支持通过IPC接收Interview命令
- 支持单个Agent采访和批量采访
- 支持远程关闭环境命令

使用方式:
    python run_parallel_simulation.py --config simulation_config.json
    python run_parallel_simulation.py --config simulation_config.json --no-wait  # 完成后立即关闭
    python run_parallel_simulation.py --config simulation_config.json --twitter-only
    python run_parallel_simulation.py --config simulation_config.json --reddit-only

日志结构:
    sim_xxx/
    ├── twitter/
    │   └── actions.jsonl    # Twitter 平台动作日志
    ├── reddit/
    │   └── actions.jsonl    # Reddit 平台动作日志
    ├── simulation.log       # 主模拟进程日志
    └── run_state.json       # 运行状态（API 查询用）
"""

# ============================================================
# 解决 Windows 编码问题：在所有 import 之前设置 UTF-8 编码
# 这是为了修复 OASIS 第三方库读取文件时未指定编码的问题
# ============================================================
import sys
import os

if sys.platform == 'win32':
    # 设置 Python 默认 I/O 编码为 UTF-8
    # 这会影响所有未指定编码的 open() 调用
    os.environ.setdefault('PYTHONUTF8', '1')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    
    # 重新配置标准输出流为 UTF-8（解决控制台中文乱码）
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    # 强制设置默认编码（影响 open() 函数的默认编码）
    # 注意：这需要在 Python 启动时就设置，运行时设置可能不生效
    # 所以我们还需要 monkey-patch 内置的 open 函数
    import builtins
    _original_open = builtins.open
    
    def _utf8_open(file, mode='r', buffering=-1, encoding=None, errors=None, 
                   newline=None, closefd=True, opener=None):
        """
        包装 open() 函数，对于文本模式默认使用 UTF-8 编码
        这可以修复第三方库（如 OASIS）读取文件时未指定编码的问题
        """
        # 只对文本模式（非二进制）且未指定编码的情况设置默认编码
        if encoding is None and 'b' not in mode:
            encoding = 'utf-8'
        return _original_open(file, mode, buffering, encoding, errors, 
                              newline, closefd, opener)
    
    builtins.open = _utf8_open

import argparse
import asyncio
import json
import logging
import multiprocessing
import random
import signal
import sqlite3
import warnings
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


# 全局变量：用于信号处理
_shutdown_event = None
_cleanup_done = False

# 添加 backend 目录到路径
# 脚本固定位于 backend/scripts/ 目录
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_scripts_dir, '..'))
_project_root = os.path.abspath(os.path.join(_backend_dir, '..'))
sys.path.insert(0, _scripts_dir)
sys.path.insert(0, _backend_dir)

# 加载项目根目录的 .env 文件（包含 LLM_API_KEY 等配置）
from dotenv import load_dotenv
_env_file = os.path.join(_project_root, '.env')
if os.path.exists(_env_file):
    load_dotenv(_env_file)
    print(f"已加载环境配置: {_env_file}")
else:
    # 尝试加载 backend/.env
    _backend_env = os.path.join(_backend_dir, '.env')
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env)
        print(f"已加载环境配置: {_backend_env}")


class MaxTokensWarningFilter(logging.Filter):
    """过滤掉 camel-ai 关于 max_tokens 的警告（我们故意不设置 max_tokens，让模型自行决定）"""
    
    def filter(self, record):
        # 过滤掉包含 max_tokens 警告的日志
        if "max_tokens" in record.getMessage() and "Invalid or missing" in record.getMessage():
            return False
        return True


# 在模块加载时立即添加过滤器，确保在 camel 代码执行前生效
logging.getLogger().addFilter(MaxTokensWarningFilter())


def disable_oasis_logging():
    """
    禁用 OASIS 库的详细日志输出
    OASIS 的日志太冗余（记录每个 agent 的观察和动作），我们使用自己的 action_logger
    """
    # 禁用 OASIS 的所有日志器
    oasis_loggers = [
        "social.agent",
        "social.twitter", 
        "social.rec",
        "oasis.env",
        "table",
    ]
    
    for logger_name in oasis_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)  # 只记录严重错误
        logger.handlers.clear()
        logger.propagate = False


def init_logging_for_simulation(simulation_dir: str):
    """
    初始化模拟的日志配置
    
    Args:
        simulation_dir: 模拟目录路径
    """
    # 禁用 OASIS 的详细日志
    disable_oasis_logging()
    
    # 清理旧的 log 目录（如果存在）
    old_log_dir = os.path.join(simulation_dir, "log")
    if os.path.exists(old_log_dir):
        import shutil
        shutil.rmtree(old_log_dir, ignore_errors=True)


from action_logger import SimulationLogManager, PlatformActionLogger
from app.services.platform_behaviors import (
    CANONICAL_PLATFORMS,
    PLATFORM_CHARACTERISTICS,
    PLATFORM_ACTION_SPACES,
    compute_feed_score,
    get_platform_characteristics,
    get_platform_behavior,
    sample_agent_role,
    sample_platform_action,
)

try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    import oasis
    from oasis import (
        ActionType,
        LLMAction,
        ManualAction,
        generate_twitter_agent_graph,
        generate_reddit_agent_graph
    )
    from oasis.social_platform.platform import Platform
    from oasis.social_platform.channel import Channel
    from oasis.social_platform.config.user import UserInfo
    from app.services.simulation.style_realizer import style_realizer
except ImportError as e:
    print(f"错误: 缺少依赖 {e}")
    print("请先安装: pip install oasis-ai camel-ai")
    sys.exit(1)


def patch_oasis_user_info_for_indonesian_style() -> None:
    """
    Monkey-patch UserInfo OASIS agar otomatis menyuntikkan instruksi
    gaya bahasa netizen Indonesia dan few-shot authentic ke system message.
    """
    if getattr(UserInfo, "_indonesian_style_patched", False):
        return

    orig_twitter = UserInfo.to_twitter_system_message
    orig_reddit = UserInfo.to_reddit_system_message

    def patched_to_twitter_system_message(self) -> str:
        base_prompt = orig_twitter(self)
        return style_realizer.build_natural_system_prompt(
            base_prompt=base_prompt,
            user_info=self,
            platform="twitter"
        )

    def patched_to_reddit_system_message(self) -> str:
        # OASIS to_reddit_system_message memerlukan field demografis default jika tidak ada
        if hasattr(self, "profile") and isinstance(self.profile, dict):
            other = self.profile.setdefault("other_info", {})
            if isinstance(other, dict):
                other.setdefault("gender", "person")
                other.setdefault("age", "25")
                other.setdefault("mbti", "INFP")
                other.setdefault("country", "Indonesia")
        base_prompt = orig_reddit(self)
        return style_realizer.build_natural_system_prompt(
            base_prompt=base_prompt,
            user_info=self,
            platform="reddit"
        )

    UserInfo.to_twitter_system_message = patched_to_twitter_system_message
    UserInfo.to_reddit_system_message = patched_to_reddit_system_message
    UserInfo._indonesian_style_patched = True


def enrich_social_agents_with_style(agent_graph, platform: str = "twitter") -> None:
    """
    Perkaya dan sinkronkan system prompt seluruh SocialAgent di agent_graph
    dengan panduan gaya bahasa netizen Indonesia dan reinit memory agent.
    """
    for agent_id, agent in agent_graph.get_agents():
        user_info = getattr(agent, "user_info", None)
        register = style_realizer.determine_register(user_info)
        guidance = style_realizer.format_style_guidance(register=register, platform=platform)

        sys_msg = getattr(agent, "system_message", None)
        current_content = sys_msg.content if sys_msg and hasattr(sys_msg, "content") else ""

        if "ATURAN GAYA KOMUNIKASI & REGISTER BAHASA NETIZEN INDONESIA" not in current_content:
            new_content = f"{current_content.rstrip()}\n{guidance}\n"
            if hasattr(agent, "_original_system_message") and hasattr(agent._original_system_message, "content"):
                agent._original_system_message.content = new_content
            if hasattr(agent, "_system_message") and hasattr(agent._system_message, "content"):
                agent._system_message.content = new_content
            if hasattr(agent, "orig_sys_message") and hasattr(agent.orig_sys_message, "content"):
                agent.orig_sys_message.content = new_content

            if hasattr(agent, "init_messages"):
                agent.init_messages()


# Aktifkan patch otomatis saat modul dimuat
patch_oasis_user_info_for_indonesian_style()


# Twitter可用动作（不包含INTERVIEW，INTERVIEW只能通过ManualAction手动触发）
TWITTER_ACTIONS = [
    ActionType.CREATE_POST,
    ActionType.LIKE_POST,
    ActionType.REPOST,
    ActionType.FOLLOW,
    ActionType.DO_NOTHING,
    ActionType.QUOTE_POST,
]

# Reddit可用动作（不包含INTERVIEW，INTERVIEW只能通过ManualAction手动触发）
# Catatan: ActionType.TREND dihilangkan karena schema OpenAI 'required' tanpa 'properties' memicu BadRequest 400
REDDIT_ACTIONS = [
    ActionType.LIKE_POST,
    ActionType.DISLIKE_POST,
    ActionType.CREATE_POST,
    ActionType.CREATE_COMMENT,
    ActionType.LIKE_COMMENT,
    ActionType.DISLIKE_COMMENT,
    ActionType.SEARCH_POSTS,
    ActionType.SEARCH_USER,
    ActionType.REFRESH,
    ActionType.DO_NOTHING,
    ActionType.FOLLOW,
    ActionType.MUTE,
]


# IPC相关常量
IPC_COMMANDS_DIR = "ipc_commands"
IPC_RESPONSES_DIR = "ipc_responses"
ENV_STATUS_FILE = "env_status.json"

class CommandType:
    """命令类型常量"""
    INTERVIEW = "interview"
    BATCH_INTERVIEW = "batch_interview"
    CLOSE_ENV = "close_env"


class ParallelIPCHandler:
    """
    双平台IPC命令处理器
    
    管理两个平台的环境，处理Interview命令
    """
    
    def __init__(
        self,
        simulation_dir: str,
        environments: Optional[Dict[str, Any]] = None,
        agent_graphs: Optional[Dict[str, Any]] = None,
        twitter_env=None,
        twitter_agent_graph=None,
        reddit_env=None,
        reddit_agent_graph=None
    ):
        self.simulation_dir = simulation_dir
        self.environments: Dict[str, Any] = {}
        self.agent_graphs: Dict[str, Any] = {}

        if environments:
            for p, env in environments.items():
                if env is not None:
                    self.environments[p.lower().strip()] = env
        if agent_graphs:
            for p, graph in agent_graphs.items():
                if graph is not None:
                    self.agent_graphs[p.lower().strip()] = graph

        # Kompatibilitas mundur
        if twitter_env is not None:
            self.environments["twitter"] = twitter_env
        if twitter_agent_graph is not None:
            self.agent_graphs["twitter"] = twitter_agent_graph
        if reddit_env is not None:
            self.environments["reddit"] = reddit_env
        if reddit_agent_graph is not None:
            self.agent_graphs["reddit"] = reddit_agent_graph

        self.twitter_env = self.environments.get("twitter")
        self.twitter_agent_graph = self.agent_graphs.get("twitter")
        self.reddit_env = self.environments.get("reddit")
        self.reddit_agent_graph = self.agent_graphs.get("reddit")

        self.commands_dir = os.path.join(simulation_dir, IPC_COMMANDS_DIR)
        self.responses_dir = os.path.join(simulation_dir, IPC_RESPONSES_DIR)
        self.status_file = os.path.join(simulation_dir, ENV_STATUS_FILE)

        # 确保目录存在
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)

    def update_status(self, status: str):
        """更新环境状态 (Mendukung 7 platform kanonikal)"""
        status_data = {
            "status": status,
            "twitter_available": self.environments.get("twitter") is not None,
            "reddit_available": self.environments.get("reddit") is not None,
            "active_platforms": list(self.environments.keys()),
            "timestamp": datetime.now().isoformat()
        }
        for p in CANONICAL_PLATFORMS:
            status_data[f"{p}_available"] = self.environments.get(p) is not None

        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
    
    def poll_command(self) -> Optional[Dict[str, Any]]:
        """轮询获取待处理命令"""
        if not os.path.exists(self.commands_dir):
            return None
        
        # 获取命令文件（按时间排序）
        command_files = []
        for filename in os.listdir(self.commands_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.commands_dir, filename)
                command_files.append((filepath, os.path.getmtime(filepath)))
        
        command_files.sort(key=lambda x: x[1])
        
        for filepath, _ in command_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
        
        return None
    
    def send_response(self, command_id: str, status: str, result: Dict = None, error: str = None):
        """发送响应"""
        response = {
            "command_id": command_id,
            "status": status,
            "result": result,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        response_file = os.path.join(self.responses_dir, f"{command_id}.json")
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        
        # 删除命令文件
        command_file = os.path.join(self.commands_dir, f"{command_id}.json")
        try:
            os.remove(command_file)
        except OSError:
            pass
    
    def _get_env_and_graph(self, platform: str):
        """
        获取指定平台的环境和agent_graph (Mendukung 7 Platform Kanonikal)

        Args:
            platform: 平台名称 (twitter, reddit, tiktok, instagram, threads, linkedin, youtube)

        Returns:
            (env, agent_graph, platform_name) 或 (None, None, None)
        """
        p = platform.lower().strip()
        env = self.environments.get(p)
        graph = self.agent_graphs.get(p)
        if env and graph:
            return env, graph, p
        return None, None, None
    
    async def _interview_single_platform(self, agent_id: int, prompt: str, platform: str) -> Dict[str, Any]:
        """
        在单个平台上执行Interview
        
        Returns:
            包含结果的字典，或包含error的字典
        """
        env, agent_graph, actual_platform = self._get_env_and_graph(platform)
        
        if not env or not agent_graph:
            return {"platform": platform, "error": f"{platform}平台不可用"}
        
        try:
            agent = agent_graph.get_agent(agent_id)
            interview_action = ManualAction(
                action_type=ActionType.INTERVIEW,
                action_args={"prompt": prompt}
            )
            actions = {agent: interview_action}
            await env.step(actions)
            
            result = self._get_interview_result(agent_id, actual_platform)
            result["platform"] = actual_platform
            return result
            
        except Exception as e:
            return {"platform": platform, "error": str(e)}
    
    async def handle_interview(self, command_id: str, agent_id: int, prompt: str, platform: str = None) -> bool:
        """
        处理单个Agent采访命令

        Args:
            command_id: 命令ID
            agent_id: Agent ID
            prompt: 采访问题
            platform: 指定平台（可选）
                - nama platform: 只采访该平台
                - None/不指定: 同时采访所有活跃平台，返回整合结果

        Returns:
            True 表示成功，False 表示失败
        """
        if platform:
            p = platform.lower().strip()
            result = await self._interview_single_platform(agent_id, prompt, p)

            if "error" in result:
                self.send_response(command_id, "failed", error=result["error"])
                print(f"  Interview失败: agent_id={agent_id}, platform={p}, error={result['error']}")
                return False
            else:
                self.send_response(command_id, "completed", result=result)
                print(f"  Interview完成: agent_id={agent_id}, platform={p}")
                return True

        if not self.environments:
            self.send_response(command_id, "failed", error="没有可用的模拟环境")
            return False

        results = {
            "agent_id": agent_id,
            "prompt": prompt,
            "platforms": {}
        }
        success_count = 0

        tasks = []
        platforms_to_interview = []
        for p in self.environments.keys():
            tasks.append(self._interview_single_platform(agent_id, prompt, p))
            platforms_to_interview.append(p)

        platform_results = await asyncio.gather(*tasks)
        for platform_name, platform_result in zip(platforms_to_interview, platform_results):
            results["platforms"][platform_name] = platform_result
            if "error" not in platform_result:
                success_count += 1

        if success_count > 0:
            self.send_response(command_id, "completed", result=results)
            print(f"  Interview完成: agent_id={agent_id}, 成功平台数={success_count}/{len(platforms_to_interview)}")
            return True
        else:
            errors = [f"{p}: {r.get('error', '未知错误')}" for p, r in results["platforms"].items()]
            self.send_response(command_id, "failed", error="; ".join(errors))
            print(f"  Interview失败: agent_id={agent_id}, 所有平台都失败")
            return False

    async def handle_batch_interview(self, command_id: str, interviews: List[Dict], platform: str = None) -> bool:
        """
        处理批量采访命令 (Mendukung 7 platform)

        Args:
            command_id: 命令ID
            interviews: [{"agent_id": int, "prompt": str, "platform": str(optional)}, ...]
            platform: 默认平台（可被每个interview项覆盖）
        """
        platform_batches: Dict[str, List[Dict]] = {p: [] for p in self.environments.keys()}
        all_platforms_interviews = []

        for interview in interviews:
            item_platform = interview.get("platform", platform)
            if item_platform:
                tp = item_platform.lower().strip()
                if tp in platform_batches:
                    platform_batches[tp].append(interview)
            else:
                all_platforms_interviews.append(interview)

        if all_platforms_interviews:
            for p in platform_batches.keys():
                platform_batches[p].extend(all_platforms_interviews)

        results = {}
        for p, p_interviews in platform_batches.items():
            if not p_interviews:
                continue
            env, agent_graph, _ = self._get_env_and_graph(p)
            if not env or not agent_graph:
                continue
            try:
                actions = {}
                for interview in p_interviews:
                    agent_id = interview.get("agent_id")
                    prompt = interview.get("prompt", "")
                    try:
                        agent = agent_graph.get_agent(agent_id)
                        actions[agent] = ManualAction(
                            action_type=ActionType.INTERVIEW,
                            action_args={"prompt": prompt}
                        )
                    except Exception as e:
                        print(f"  警告: 无法获取{p} Agent {agent_id}: {e}")

                if actions:
                    await env.step(actions)
                    for interview in p_interviews:
                        agent_id = interview.get("agent_id")
                        result = self._get_interview_result(agent_id, p)
                        result["platform"] = p
                        results[f"{p}_{agent_id}"] = result
            except Exception as e:
                print(f"  {p}批量Interview失败: {e}")

        if results:
            self.send_response(command_id, "completed", result={
                "interviews_count": len(results),
                "results": results
            })
            print(f"  批量Interview完成: {len(results)} 个Agent")
            return True
        else:
            self.send_response(command_id, "failed", error="没有成功的采访")
            return False
    
    def _get_interview_result(self, agent_id: int, platform: str) -> Dict[str, Any]:
        """从数据库获取最新的Interview结果"""
        db_path = os.path.join(self.simulation_dir, f"{platform}_simulation.db")
        
        result = {
            "agent_id": agent_id,
            "response": None,
            "timestamp": None
        }
        
        if not os.path.exists(db_path):
            return result
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询最新的Interview记录
            cursor.execute("""
                SELECT user_id, info, created_at
                FROM trace
                WHERE action = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (ActionType.INTERVIEW.value, agent_id))
            
            row = cursor.fetchone()
            if row:
                user_id, info_json, created_at = row
                try:
                    info = json.loads(info_json) if info_json else {}
                    result["response"] = info.get("response", info)
                    result["timestamp"] = created_at
                except json.JSONDecodeError:
                    result["response"] = info_json
            
            conn.close()
            
        except Exception as e:
            print(f"  读取Interview结果失败: {e}")
        
        return result
    
    async def process_commands(self) -> bool:
        """
        处理所有待处理命令
        
        Returns:
            True 表示继续运行，False 表示应该退出
        """
        command = self.poll_command()
        if not command:
            return True
        
        command_id = command.get("command_id")
        command_type = command.get("command_type")
        args = command.get("args", {})
        
        print(f"\n收到IPC命令: {command_type}, id={command_id}")
        
        if command_type == CommandType.INTERVIEW:
            await self.handle_interview(
                command_id,
                args.get("agent_id", 0),
                args.get("prompt", ""),
                args.get("platform")
            )
            return True
            
        elif command_type == CommandType.BATCH_INTERVIEW:
            await self.handle_batch_interview(
                command_id,
                args.get("interviews", []),
                args.get("platform")
            )
            return True
            
        elif command_type == CommandType.CLOSE_ENV:
            print("收到关闭环境命令")
            self.send_response(command_id, "completed", result={"message": "环境即将关闭"})
            return False
        
        else:
            self.send_response(command_id, "failed", error=f"未知命令类型: {command_type}")
            return True


def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# 需要过滤掉的非核心动作类型（这些动作对分析价值较低）
FILTERED_ACTIONS = {'refresh', 'sign_up'}

# 动作类型映射表（数据库中的名称 -> 标准名称）
ACTION_TYPE_MAP = {
    'create_post': 'CREATE_POST',
    'like_post': 'LIKE_POST',
    'dislike_post': 'DISLIKE_POST',
    'repost': 'REPOST',
    'quote_post': 'QUOTE_POST',
    'follow': 'FOLLOW',
    'mute': 'MUTE',
    'create_comment': 'CREATE_COMMENT',
    'like_comment': 'LIKE_COMMENT',
    'dislike_comment': 'DISLIKE_COMMENT',
    'search_posts': 'SEARCH_POSTS',
    'search_user': 'SEARCH_USER',
    'trend': 'TREND',
    'do_nothing': 'DO_NOTHING',
    'interview': 'INTERVIEW',
    # Platform-specific actions across 7 canonical platforms
    'create_script': 'CREATE_SCRIPT',
    'like_video': 'LIKE_VIDEO',
    'comment': 'CREATE_COMMENT',
    'reply': 'CREATE_COMMENT',
    'share_to_friends': 'SHARE',
    'duet_react': 'REPOST',
    'follow_creator': 'FOLLOW',
    'skip': 'DO_NOTHING',
    'save_post': 'LIKE_POST',
    'share_story': 'REPOST',
    'like': 'LIKE_POST',
    'subscribe': 'FOLLOW',
    'share': 'REPOST',
    'connect': 'FOLLOW',
}


def get_agent_names_from_config(config: Dict[str, Any]) -> Dict[int, str]:
    """
    从 simulation_config 中获取 agent_id -> entity_name 的映射
    
    这样可以在 actions.jsonl 中显示真实的实体名称，而不是 "Agent_0" 这样的代号
    
    Args:
        config: simulation_config.json 的内容
        
    Returns:
        agent_id -> entity_name 的映射字典
    """
    agent_names = {}
    agent_configs = config.get("agent_configs", [])
    
    for agent_config in agent_configs:
        agent_id = agent_config.get("agent_id")
        entity_name = agent_config.get("entity_name", f"Agent_{agent_id}")
        if agent_id is not None:
            agent_names[agent_id] = entity_name
    
    return agent_names


def fetch_new_actions_from_db(
    db_path: str,
    last_rowid: int,
    agent_names: Dict[int, str]
) -> Tuple[List[Dict[str, Any]], int]:
    """
    从数据库中获取新的动作记录，并补充完整的上下文信息
    
    Args:
        db_path: 数据库文件路径
        last_rowid: 上次读取的最大 rowid 值（使用 rowid 而不是 created_at，因为不同平台的 created_at 格式不同）
        agent_names: agent_id -> agent_name 映射
        
    Returns:
        (actions_list, new_last_rowid)
        - actions_list: 动作列表，每个元素包含 agent_id, agent_name, action_type, action_args（含上下文信息）
        - new_last_rowid: 新的最大 rowid 值
    """
    actions = []
    new_last_rowid = last_rowid
    
    if not os.path.exists(db_path):
        return actions, new_last_rowid
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 使用 rowid 来追踪已处理的记录（rowid 是 SQLite 的内置自增字段）
        # 这样可以避免 created_at 格式差异问题（Twitter 用整数，Reddit 用日期时间字符串）
        cursor.execute("""
            SELECT rowid, user_id, action, info
            FROM trace
            WHERE rowid > ?
            ORDER BY rowid ASC
        """, (last_rowid,))
        
        for rowid, user_id, action, info_json in cursor.fetchall():
            # 更新最大 rowid
            new_last_rowid = rowid
            
            # 过滤非核心动作
            if action in FILTERED_ACTIONS:
                continue
            
            # 解析动作参数
            try:
                action_args = json.loads(info_json) if info_json else {}
            except json.JSONDecodeError:
                action_args = {}
            
            # 精简 action_args，只保留关键字段（保留完整内容，不截断）
            simplified_args = {}
            if 'content' in action_args:
                simplified_args['content'] = action_args['content']
            if 'post_id' in action_args:
                simplified_args['post_id'] = action_args['post_id']
            if 'comment_id' in action_args:
                simplified_args['comment_id'] = action_args['comment_id']
            if 'quoted_id' in action_args:
                simplified_args['quoted_id'] = action_args['quoted_id']
            if 'new_post_id' in action_args:
                simplified_args['new_post_id'] = action_args['new_post_id']
            if 'follow_id' in action_args:
                simplified_args['follow_id'] = action_args['follow_id']
            if 'query' in action_args:
                simplified_args['query'] = action_args['query']
            if 'like_id' in action_args:
                simplified_args['like_id'] = action_args['like_id']
            if 'dislike_id' in action_args:
                simplified_args['dislike_id'] = action_args['dislike_id']
            
            # 转换动作类型名称
            action_type = ACTION_TYPE_MAP.get(action, action.upper())
            
            # 补充上下文信息（帖子内容、用户名等）
            _enrich_action_context(cursor, action_type, simplified_args, agent_names)
            
            actions.append({
                'agent_id': user_id,
                'agent_name': agent_names.get(user_id, f'Agent_{user_id}'),
                'action_type': action_type,
                'action_args': simplified_args,
            })
        
        conn.close()
    except Exception as e:
        print(f"读取数据库动作失败: {e}")
    
    return actions, new_last_rowid


def _enrich_action_context(
    cursor,
    action_type: str,
    action_args: Dict[str, Any],
    agent_names: Dict[int, str]
) -> None:
    """
    为动作补充上下文信息（帖子内容、用户名等）
    
    Args:
        cursor: 数据库游标
        action_type: 动作类型
        action_args: 动作参数（会被修改）
        agent_names: agent_id -> agent_name 映射
    """
    try:
        # 点赞/踩帖子：补充帖子内容和作者
        if action_type in ('LIKE_POST', 'DISLIKE_POST'):
            post_id = action_args.get('post_id')
            if post_id:
                post_info = _get_post_info(cursor, post_id, agent_names)
                if post_info:
                    action_args['post_content'] = post_info.get('content', '')
                    action_args['post_author_name'] = post_info.get('author_name', '')
        
        # 转发帖子：补充原帖内容和作者
        elif action_type == 'REPOST':
            new_post_id = action_args.get('new_post_id')
            if new_post_id:
                # 转发帖子的 original_post_id 指向原帖
                cursor.execute("""
                    SELECT original_post_id FROM post WHERE post_id = ?
                """, (new_post_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    original_post_id = row[0]
                    original_info = _get_post_info(cursor, original_post_id, agent_names)
                    if original_info:
                        action_args['original_content'] = original_info.get('content', '')
                        action_args['original_author_name'] = original_info.get('author_name', '')
        
        # 引用帖子：补充原帖内容、作者和引用评论
        elif action_type == 'QUOTE_POST':
            quoted_id = action_args.get('quoted_id')
            new_post_id = action_args.get('new_post_id')
            
            if quoted_id:
                original_info = _get_post_info(cursor, quoted_id, agent_names)
                if original_info:
                    action_args['original_content'] = original_info.get('content', '')
                    action_args['original_author_name'] = original_info.get('author_name', '')
            
            # 获取引用帖子的评论内容（quote_content）
            if new_post_id:
                cursor.execute("""
                    SELECT quote_content FROM post WHERE post_id = ?
                """, (new_post_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    action_args['quote_content'] = row[0]
        
        # 关注用户：补充被关注用户的名称
        elif action_type == 'FOLLOW':
            follow_id = action_args.get('follow_id')
            if follow_id:
                # 从 follow 表获取 followee_id
                cursor.execute("""
                    SELECT followee_id FROM follow WHERE follow_id = ?
                """, (follow_id,))
                row = cursor.fetchone()
                if row:
                    followee_id = row[0]
                    target_name = _get_user_name(cursor, followee_id, agent_names)
                    if target_name:
                        action_args['target_user_name'] = target_name
        
        # 屏蔽用户：补充被屏蔽用户的名称
        elif action_type == 'MUTE':
            # 从 action_args 中获取 user_id 或 target_id
            target_id = action_args.get('user_id') or action_args.get('target_id')
            if target_id:
                target_name = _get_user_name(cursor, target_id, agent_names)
                if target_name:
                    action_args['target_user_name'] = target_name
        
        # 点赞/踩评论：补充评论内容和作者
        elif action_type in ('LIKE_COMMENT', 'DISLIKE_COMMENT'):
            comment_id = action_args.get('comment_id')
            if comment_id:
                comment_info = _get_comment_info(cursor, comment_id, agent_names)
                if comment_info:
                    action_args['comment_content'] = comment_info.get('content', '')
                    action_args['comment_author_name'] = comment_info.get('author_name', '')
        
        # 发表评论：补充所评论的帖子信息
        elif action_type == 'CREATE_COMMENT':
            post_id = action_args.get('post_id')
            if post_id:
                post_info = _get_post_info(cursor, post_id, agent_names)
                if post_info:
                    action_args['post_content'] = post_info.get('content', '')
                    action_args['post_author_name'] = post_info.get('author_name', '')
    
    except Exception as e:
        # 补充上下文失败不影响主流程
        print(f"补充动作上下文失败: {e}")


def _get_post_info(
    cursor,
    post_id: int,
    agent_names: Dict[int, str]
) -> Optional[Dict[str, str]]:
    """
    获取帖子信息
    
    Args:
        cursor: 数据库游标
        post_id: 帖子ID
        agent_names: agent_id -> agent_name 映射
        
    Returns:
        包含 content 和 author_name 的字典，或 None
    """
    try:
        cursor.execute("""
            SELECT p.content, p.user_id, u.agent_id
            FROM post p
            LEFT JOIN user u ON p.user_id = u.user_id
            WHERE p.post_id = ?
        """, (post_id,))
        row = cursor.fetchone()
        if row:
            content = row[0] or ''
            user_id = row[1]
            agent_id = row[2]
            
            # 优先使用 agent_names 中的名称
            author_name = ''
            if agent_id is not None and agent_id in agent_names:
                author_name = agent_names[agent_id]
            elif user_id:
                # 从 user 表获取名称
                cursor.execute("SELECT name, user_name FROM user WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()
                if user_row:
                    author_name = user_row[0] or user_row[1] or ''
            
            return {'content': content, 'author_name': author_name}
    except Exception:
        pass
    return None


def _get_user_name(
    cursor,
    user_id: int,
    agent_names: Dict[int, str]
) -> Optional[str]:
    """
    获取用户名称
    
    Args:
        cursor: 数据库游标
        user_id: 用户ID
        agent_names: agent_id -> agent_name 映射
        
    Returns:
        用户名称，或 None
    """
    try:
        cursor.execute("""
            SELECT agent_id, name, user_name FROM user WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            agent_id = row[0]
            name = row[1]
            user_name = row[2]
            
            # 优先使用 agent_names 中的名称
            if agent_id is not None and agent_id in agent_names:
                return agent_names[agent_id]
            return name or user_name or ''
    except Exception:
        pass
    return None


def _get_comment_info(
    cursor,
    comment_id: int,
    agent_names: Dict[int, str]
) -> Optional[Dict[str, str]]:
    """
    获取评论信息
    
    Args:
        cursor: 数据库游标
        comment_id: 评论ID
        agent_names: agent_id -> agent_name 映射
        
    Returns:
        包含 content 和 author_name 的字典，或 None
    """
    try:
        cursor.execute("""
            SELECT c.content, c.user_id, u.agent_id
            FROM comment c
            LEFT JOIN user u ON c.user_id = u.user_id
            WHERE c.comment_id = ?
        """, (comment_id,))
        row = cursor.fetchone()
        if row:
            content = row[0] or ''
            user_id = row[1]
            agent_id = row[2]
            
            # 优先使用 agent_names 中的名称
            author_name = ''
            if agent_id is not None and agent_id in agent_names:
                author_name = agent_names[agent_id]
            elif user_id:
                # 从 user 表获取名称
                cursor.execute("SELECT name, user_name FROM user WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()
                if user_row:
                    author_name = user_row[0] or user_row[1] or ''
            
            return {'content': content, 'author_name': author_name}
    except Exception:
        pass
    return None


def create_model(config: Dict[str, Any], use_boost: bool = False):
    """
    创建LLM模型
    
    支持双 LLM 配置，用于并行模拟时提速：
    - 通用配置：LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
    - 加速配置（可选）：LLM_BOOST_API_KEY, LLM_BOOST_BASE_URL, LLM_BOOST_MODEL_NAME
    
    如果配置了加速 LLM，并行模拟时可以让不同平台使用不同的 API 服务商，提高并发能力。
    
    Args:
        config: 模拟配置字典
        use_boost: 是否使用加速 LLM 配置（如果可用）
    """
    # 检查是否有加速配置
    boost_api_key = os.environ.get("LLM_BOOST_API_KEY", "")
    boost_base_url = os.environ.get("LLM_BOOST_BASE_URL", "")
    boost_model = os.environ.get("LLM_BOOST_MODEL_NAME", "")
    has_boost_config = bool(boost_api_key)
    
    # 根据参数和配置情况选择使用哪个 LLM
    if use_boost and has_boost_config:
        # 使用加速配置
        llm_api_key = boost_api_key
        llm_base_url = boost_base_url
        llm_model = boost_model or os.environ.get("LLM_MODEL_NAME", "")
        config_label = "[加速LLM]"
    else:
        # 使用通用配置
        llm_api_key = os.environ.get("LLM_API_KEY", "")
        llm_base_url = os.environ.get("LLM_BASE_URL", "")
        llm_model = os.environ.get("LLM_MODEL_NAME", "")
        config_label = "[通用LLM]"
    
    # 如果 .env 中没有模型名，则使用 config 作为备用
    if not llm_model:
        llm_model = config.get("llm_model", "mirofish-agent")
    
    # 设置 camel-ai 所需的环境变量
    if llm_api_key:
        os.environ["OPENAI_API_KEY"] = llm_api_key
    
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("缺少 API Key 配置，请在项目根目录 .env 文件中设置 LLM_API_KEY")
    
    if llm_base_url:
        os.environ["OPENAI_API_BASE_URL"] = llm_base_url
    
    print(f"{config_label} model={llm_model}, base_url={llm_base_url[:40] if llm_base_url else '默认'}...")
    
    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=llm_model,
    )


def get_active_agents_for_round(
    env,
    config: Dict[str, Any],
    current_hour: int,
    round_num: int
) -> List:
    """根据时间和配置决定本轮激活哪些Agent"""
    time_config = config.get("time_config", {})
    agent_configs = config.get("agent_configs", [])
    
    base_min = time_config.get("agents_per_hour_min", 5)
    base_max = time_config.get("agents_per_hour_max", 20)
    
    peak_hours = time_config.get("peak_hours", [9, 10, 11, 14, 15, 20, 21, 22])
    off_peak_hours = time_config.get("off_peak_hours", [0, 1, 2, 3, 4, 5])
    
    if current_hour in peak_hours:
        multiplier = time_config.get("peak_activity_multiplier", 1.5)
    elif current_hour in off_peak_hours:
        multiplier = time_config.get("off_peak_activity_multiplier", 0.3)
    else:
        multiplier = 1.0
    
    target_count = int(random.uniform(base_min, base_max) * multiplier)
    
    candidates = []
    for cfg in agent_configs:
        agent_id = cfg.get("agent_id", 0)
        active_hours = cfg.get("active_hours", list(range(8, 23)))
        activity_level = cfg.get("activity_level", 0.5)
        
        if current_hour not in active_hours:
            continue
        
        if random.random() < activity_level:
            candidates.append(agent_id)

    if not candidates and agent_configs:
        fallback_pool = [cfg.get("agent_id", 0) for cfg in agent_configs if cfg.get("agent_id") is not None]
        fallback_count = max(1, min(max(1, target_count), len(fallback_pool)))
        candidates = random.sample(fallback_pool, fallback_count)

    selected_ids = random.sample(
        candidates,
        min(target_count, len(candidates))
    ) if candidates else []
    
    active_agents = []
    for agent_id in selected_ids:
        try:
            agent = env.agent_graph.get_agent(agent_id)
            active_agents.append((agent_id, agent))
        except Exception:
            pass
    
    return active_agents


class PlatformSimulation:
    """平台模拟结果容器"""
    def __init__(self):
        self.env = None
        self.agent_graph = None
        self.total_actions = 0


# ==============================================================================
# MESIN SIMULASI PERILAKU MULTI-PLATFORM (TIKTOK, INSTAGRAM, THREADS, LINKEDIN, YOUTUBE)
# Menerapkan Spesifikasi Matematis Notion:
# 1. Normalized Feed Scoring:
#    Score = lambda_rec * 2^(-dt / t_half) + beta_pop * min(1, ln(1 + Eng)/ln(1 + Eng_p99)) + gamma_echo * (1 + cos(e_i, e_j))/2
# 2. Pareto 90-9-1 Participation Dynamics (90% lurker, 9% contributor, 1% creator)
# 3. Parameter terkalibrasi per platform (TikTok t_half=1.8, Reddit t_half=6.0, dll)
# 4. Sinkronisasi barrier per putaran virtual
# ==============================================================================

class BehavioralAgent:
    """Agent representasi multi-platform (TikTok, Instagram, Threads, LinkedIn, YouTube)."""
    def __init__(
        self,
        agent_id: int,
        name: str,
        user_name: str,
        bio: str,
        persona: str,
        profile: Optional[Dict[str, Any]] = None,
        platform: str = "tiktok",
        model: Optional[Any] = None,
    ):
        self.agent_id = int(agent_id)
        self.user_id = int(agent_id)
        self.name = name
        self.user_name = user_name
        self.bio = bio
        self.persona = persona
        self.profile = profile or {}
        self.platform = platform.lower().strip()
        self.model = model

        # Big Five OCEAN personality traits [0.0, 1.0]
        ocean = self.profile.get("ocean", {})
        self.openness = float(ocean.get("openness", self.profile.get("openness", random.uniform(0.3, 0.8))))
        self.conscientiousness = float(ocean.get("conscientiousness", self.profile.get("conscientiousness", random.uniform(0.3, 0.8))))
        self.extraversion = float(ocean.get("extraversion", self.profile.get("extraversion", random.uniform(0.3, 0.8))))
        self.agreeableness = float(ocean.get("agreeableness", self.profile.get("agreeableness", random.uniform(0.3, 0.8))))
        self.neuroticism = float(ocean.get("neuroticism", self.profile.get("neuroticism", random.uniform(0.2, 0.7))))

        # Skoring opini dan embedding representasi
        self.opinion_score = float(self.profile.get("opinion_score", self.profile.get("alignment", random.uniform(-0.5, 0.5))))
        self.embedding = self.profile.get("embedding", [self.openness, self.conscientiousness, self.extraversion, self.agreeableness, self.opinion_score])

        # Register gaya bahasa PUEBI
        self.register = self._determine_register()

    def _determine_register(self) -> str:
        prof = (self.profile.get("profession") or "").lower()
        mbti = (self.profile.get("mbti") or "").upper()
        age = self.profile.get("age", 25)
        try:
            age = int(age)
        except Exception:
            age = 25

        if self.platform == "linkedin" or any(k in prof for k in ("dosen", "peneliti", "pejabat", "pengacara", "dokter", "birokrat", "direktur")):
            return "formal"
        if self.neuroticism > 0.65 or "TP" in mbti:
            return "sarkastik"
        if age < 30 and (self.platform in ("tiktok", "instagram", "threads") or self.extraversion > 0.6):
            return "gaul jaksel"
        return "kasual santai"

    async def interview(self, question: str) -> str:
        """Menjawab pertanyaan wawancara agen human-in-the-loop berdasarkan persona & register."""
        if self.model and hasattr(self.model, "step"):
            try:
                prompt = (
                    f"Anda adalah {self.name} (Usia: {self.profile.get('age', 25)}, Pekerjaan: {self.profile.get('profession', 'Umum')}).\n"
                    f"Persona: {self.persona}\n"
                    f"Platform: {self.platform.capitalize()}, Gaya bicara: {self.register}.\n"
                    f"Pertanyaan: {question}\n"
                    f"Jawablah dengan sudut pandang dan gaya bahasa karakter Anda (1-3 kalimat):"
                )
                from camel.messages import BaseMessage
                msg = BaseMessage.make_user_message(role_name="User", content=prompt)
                resp = await self.model.step([msg]) if asyncio.iscoroutinefunction(self.model.step) else self.model.step([msg])
                if hasattr(resp, "msg") and hasattr(resp.msg, "content"):
                    return str(resp.msg.content).strip()
            except Exception:
                pass

        topic = "kebijakan_publik"
        q_lower = question.lower()
        if any(w in q_lower for w in ("asap", "karhutla", "kabut", "polusi", "lingkungan", "kebakaran")):
            topic = "karhutla_kabut_asap"
        elif any(w in q_lower for w in ("ai", "tech", "teknologi", "aplikasi", "sistem")):
            topic = "teknologi"

        few_shots = style_realizer.retrieve_few_shots(register=self.register, topic=topic, k=1)
        if few_shots:
            return f"Sebagai {self.name}: {few_shots[0].response}"
        return f"Sebagai {self.name} ({self.profile.get('profession', 'Warga')}): Menurut saya mengenai hal tersebut, situasinya membutuhkan perhatian serius dan tindakan terkoordinasi."


class BehavioralAgentGraph:
    """Graph kontainer agen untuk BehavioralPlatformEnv."""
    def __init__(self, agents: Dict[int, BehavioralAgent]):
        self.agents = agents

    def get_agents(self) -> List[Tuple[int, BehavioralAgent]]:
        return list(self.agents.items())

    def get_agent(self, agent_id: int) -> Optional[BehavioralAgent]:
        return self.agents.get(agent_id)

    @property
    def num_agents(self) -> int:
        return len(self.agents)

    def get_num_agents(self) -> int:
        return len(self.agents)


def generate_platform_content(
    agent: BehavioralAgent,
    platform: str,
    action_type: str,
    topic: str = "kebijakan_publik",
    reference_post: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Menghasilkan konten postingan atau komentar realistis sesuai karakteristik platform & gaya PUEBI.
    """
    p = platform.lower().strip()
    register = agent.register
    name = agent.name
    profession = agent.profile.get("profession", "Warga")

    few_shots = style_realizer.retrieve_few_shots(register=register, topic=topic, k=2)
    sample_text = few_shots[0].response if few_shots else ""

    if p == "tiktok":
        templates = [
            "ya Allah beneran parah bgt kabutnya 😭 plis jgn keluar rumah tanpa masker ya guys! #kabutasap #staysafe",
            "kondisi udara hari ini gak make sense bgt woy, batuk2 terus ampe sesak 😭 save riau & kalimantan!",
            "POV hari ini napas berasa hisap asep knalpot... butuh bantuan masker medis secepatnya plis 🙏",
            "update kondisi terkini di lapangan: langit udah mulai oranye pekat, stay safe semuanya! #info"
        ]
        if action_type in ("COMMENT", "CREATE_COMMENT", "REPLY"):
            return random.choice([
                "asli nyesek bgt liatnya 😭 stay safe ya kak!",
                "bener bgt woy, di tempatku juga udah bau sangit parah",
                "plis bagi info posko oksigen darurat terdekat dong 🙏",
                "semoga segera ada tindakan tegas dr pemerintah, gak tahan bgt napasnya"
            ])
        return random.choice(templates)

    elif p == "instagram":
        templates = [
            "Kondisi kualitas udara di wilayah terdampak kabut asap kian memprihatinkan. Langit gelap gulita dan indeks ISPU berada di level berbahaya. Mari kita satukan kepedulian, salurkan masker medis N95 dan tabung oksigen untuk saudara-saudara kita yang membutuhkan. Stay safe semuanya. #PeduliKesehatan #Solidaritas",
            "Refleksi hari ini: Udara bersih adalah hak asasi setiap warga negara, bukan kemewahan. Melihat anak-anak terpaksa beraktivitas di bawah paparan polusi pekat sungguh menyayat hati. Mari tingkatkan kepedulian dan saling menjaga sesama.",
            "Kabar dari lapangan: Jarak pandang sangat terbatas dan kasus ISPA melonjak tajam. Jangan lupa gunakan masker standar medis dan batasi aktivitas di luar ruangan. Jaga kesehatan keluarga kita."
        ]
        if action_type in ("COMMENT", "CREATE_COMMENT", "REPLY"):
            return random.choice([
                "Aamiin ya Allah, semoga saudara-saudara kita lekas diberikan udara yang bersih dan sehat kembali 🙏",
                "Terima kasih atas kepedulian dan informasinya kak, semoga bantuan segera tersalurkan merata.",
                "Sedih sekali melihat dampaknya pada anak-anak dan lansia... tetap waspada dan saling jaga ya semuanya.",
            ])
        return random.choice(templates)

    elif p == "threads":
        templates = [
            "Hari ke-5 bangun pagi dengan bau sangit menyengat sampai ke dalam kamar. Air purifier sudah nyala maksimal tapi tetap saja mata perih dan tenggorokan gatal. Darurat polusi ini tidak boleh dinormalisasi.",
            "Jarak pandang siang ini cuma 100 meter. Masalah lingkungan ini harus diselesaikan dari akar regulasi dan penegakan hukum konsesi, bukan sekadar pasrah menunggu turunnya hujan buatan.",
            "Banyak rekan kerja dan tetangga mulai tumbang karena ISPA. Kebijakan WFH dan penutupan sementara sekolah tatap muka harus segera diberlakukan secara tegas oleh pemda.",
        ]
        if action_type in ("COMMENT", "REPLY", "CREATE_COMMENT"):
            return random.choice([
                "Setuju banget. Penanganannya terasa lambat padahal dampaknya sudah di depan mata.",
                "Sama di sini juga, udara terasa sangat berat dihirup. Semoga segera ada evaluasi total.",
                "Persis, jangan sampai setiap tahun kita harus mengulangi kepasrahan yang sama tanpa ada solusi jangka panjang.",
            ])
        return random.choice(templates)

    elif p == "linkedin":
        templates = [
            "Krisis kabut asap dan lonjakan indeks kualitas udara di berbagai daerah menjadi alarm mendesak perlunya penguatan tata kelola lingkungan (ESG) yang ketat. Industri dan regulator harus bersinergi dalam audit sekat kanal gambut, kepatuhan zero-burning, serta memastikan Health, Safety, and Environment (HSE) tenaga kerja dan masyarakat terlindungi secara berkelanjutan.",
            "Menilik kerugian ekonomi makro akibat penutupan jalur logistik, penerbangan, dan penurunan produktivitas tenaga kerja karena ISPA, mitigasi risiko bencana lingkungan harus diposisikan sebagai investasi strategis nasional, bukan beban biaya kepatuhan administratif semata.",
            "Transformasi keberlanjutan menuntut transparansi data pemantauan titik panas satelit dan penegakan hukum strict liability tanpa kompromi. Hanya dengan kepatuhan tata kelola yang terukur kita dapat memutus siklus tahunan ini.",
        ]
        if action_type in ("COMMENT", "CREATE_COMMENT", "REPLY"):
            return random.choice([
                "Perspektif yang sangat komprehensif. Aspek kepatuhan ESG dan akuntabilitas multi-pihak memang menjadi kunci fundamental.",
                "Sepakat. Sinergi antara audit independen, mitigasi risiko HSE, dan keberpihakan regulasi adalah pilar utama keberlanjutan.",
                "Analisis yang sangat tepat. Kerugian ekonomi akibat penurunan kesehatan masyarakat jauh melampaui biaya pencegahan sejak dini.",
            ])
        return random.choice(templates)

    elif p == "youtube":
        templates = [
            "Analisis Mendalam Penanganan Krisis Kabut Asap: Pembahasan komprehensif mengenai dinamika hidrologis lahan gambut, penegakan regulasi strict liability, serta dampaknya terhadap kesehatan publik dan ekonomi daerah.",
            "Liputan Investigasi Lapangan: Mengurai benang merah antara drainase kanal konsesi perkebunan dengan percepatan kebakaran bawah tanah gambut di musim kemarau.",
            "Dokumentasi Data Satelit dan Evaluasi Penanganan Bencana: Meninjau efektivitas operasi TMC dan pemadaman darat dalam mengendalikan sebaran asap lintas wilayah.",
        ]
        if action_type in ("COMMENT", "CREATE_COMMENT", "REPLY"):
            return random.choice([
                "Paparan data dan investigasi yang sangat berbobot dan membuka mata. Penjelasan tentang hidrologi gambut sangat mencerahkan.",
                "Terima kasih atas liputan objektif ini. Semoga pemangku kebijakan menyimak kajian ilmiah ini agar penanganannya lebih preventif.",
                "Ulasan yang sangat runtut dan sistematis. Fakta di lapangan menunjukkan pentingnya transparansi data satelit titik panas.",
            ])
        return random.choice(templates)

    return sample_text or f"Tanggapan dari {name} ({profession}) mengenai isu {topic}."


def load_platform_agents(
    config: Dict[str, Any],
    platform: str,
    simulation_dir: str,
    model: Optional[Any] = None
) -> BehavioralAgentGraph:
    """Memuat dan menginisialisasi BehavioralAgentGraph dari berkas profil platform."""
    norm_p = platform.lower().strip()
    profile_path = os.path.join(simulation_dir, f"{norm_p}_profiles.json")
    if not os.path.exists(profile_path):
        profile_path = os.path.join(simulation_dir, "reddit_profiles.json")

    agent_names = get_agent_names_from_config(config)
    agents: Dict[int, BehavioralAgent] = {}

    raw_profiles = []
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                raw_profiles = json.load(f)
        except Exception as e:
            print(f"[{platform}] Gagal membaca {profile_path}: {e}")

    if not raw_profiles and "agent_configs" in config:
        raw_profiles = config["agent_configs"]

    for idx, p in enumerate(raw_profiles):
        agent_id = p.get("user_id", p.get("agent_id", idx))
        try:
            agent_id = int(agent_id)
        except Exception:
            agent_id = idx

        name = agent_names.get(agent_id, p.get("name", p.get("user_name", f"Agent_{agent_id}")))
        user_name = p.get("user_name", f"user_{agent_id}")
        bio = p.get("bio", f"User {name}")
        persona = p.get("persona", bio)

        agent = BehavioralAgent(
            agent_id=agent_id,
            name=name,
            user_name=user_name,
            bio=bio,
            persona=persona,
            profile=p,
            platform=norm_p,
            model=model
        )
        agents[agent_id] = agent

    return BehavioralAgentGraph(agents)


class BehavioralPlatformEnv:
    """
    Lingkungan simulasi platform perilaku otonom.
    Mendukung TikTok, Instagram, Threads, LinkedIn, YouTube dengan:
    - Trace dan Post persistence di SQLite (<platform>_simulation.db)
    - Normalized Feed Scoring (Notion Mathematical Spec)
    - Pareto 90-9-1 dynamics
    - Human-in-the-loop interview handling
    """
    def __init__(self, agent_graph: BehavioralAgentGraph, platform: str, database_path: str):
        self.agent_graph = agent_graph
        self.platform = platform.lower().strip()
        self.database_path = database_path
        self._conn = None
        self._last_interview_results: Dict[int, Any] = {}

    async def reset(self):
        if os.path.exists(self.database_path):
            try:
                os.remove(self.database_path)
            except OSError:
                pass
        self._conn = sqlite3.connect(self.database_path, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY,
                agent_id INTEGER,
                name TEXT,
                user_name TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS post (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                original_post_id INTEGER,
                quote_content TEXT,
                num_likes INTEGER DEFAULT 0,
                num_shares INTEGER DEFAULT 0,
                num_comments INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comment (
                comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                user_id INTEGER,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS like (
                like_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                post_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS follow (
                follow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER,
                followee_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trace (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        for agent_id, agent in self.agent_graph.get_agents():
            cursor.execute(
                "INSERT OR REPLACE INTO user (user_id, agent_id, name, user_name, bio) VALUES (?, ?, ?, ?, ?)",
                (agent_id, agent_id, agent.name, agent.user_name, agent.bio)
            )
        cursor.close()

    async def step(self, actions_dict: Dict[Any, Any], simulated_hour: int = 0, round_num: int = 0):
        if not self._conn:
            self._conn = sqlite3.connect(self.database_path, isolation_level=None)
        cursor = self._conn.cursor()

        for agent_ref, action_spec in actions_dict.items():
            if isinstance(agent_ref, int):
                agent = self.agent_graph.get_agent(agent_ref)
            else:
                agent = agent_ref

            if not agent:
                continue

            agent_id = agent.agent_id

            # ManualAction handling (initial posts or interview)
            if hasattr(action_spec, "action_type"):
                atype = getattr(action_spec.action_type, "value", str(action_spec.action_type))
                args = getattr(action_spec, "action_args", {}) or {}

                if atype in (ActionType.INTERVIEW.value, "INTERVIEW", "interview"):
                    prompt = args.get("prompt", "")
                    resp = await agent.interview(prompt)
                    self._last_interview_results[agent_id] = resp
                    cursor.execute(
                        "INSERT INTO trace (user_id, action, info, created_at) VALUES (?, ?, ?, ?)",
                        (agent_id, ActionType.INTERVIEW.value, json.dumps({"prompt": prompt, "response": resp}, ensure_ascii=False), datetime.now().isoformat())
                    )
                    continue

                elif atype in (ActionType.CREATE_POST.value, "CREATE_POST", "create_post"):
                    content = args.get("content", "")
                    cursor.execute(
                        "INSERT INTO post (user_id, content, created_at) VALUES (?, ?, ?)",
                        (agent_id, content, datetime.now().isoformat())
                    )
                    post_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO trace (user_id, action, info, created_at) VALUES (?, ?, ?, ?)",
                        (agent_id, "create_post", json.dumps({"content": content, "post_id": post_id}, ensure_ascii=False), datetime.now().isoformat())
                    )
                    continue

            # Regular step: Pareto 90-9-1 role sampling
            role = sample_agent_role()

            # Fetch existing posts from DB for feed scoring
            cursor.execute("""
                SELECT post_id, user_id, content, num_likes, num_shares, num_comments, created_at
                FROM post
                ORDER BY post_id DESC
                LIMIT 30
            """)
            raw_posts = cursor.fetchall()

            # If no posts exist yet, promote to creator to seed content
            if not raw_posts:
                role = "creator"

            if role == "creator":
                chosen_action = sample_platform_action(self.platform, "creator")
                action_name = chosen_action.lower()
                content = generate_platform_content(agent, self.platform, chosen_action)
                cursor.execute(
                    "INSERT INTO post (user_id, content, created_at) VALUES (?, ?, ?)",
                    (agent_id, content, datetime.now().isoformat())
                )
                post_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO trace (user_id, action, info, created_at) VALUES (?, ?, ?, ?)",
                    (agent_id, action_name, json.dumps({"content": content, "post_id": post_id}, ensure_ascii=False), datetime.now().isoformat())
                )

            elif role == "contributor":
                chosen_action = sample_platform_action(self.platform, "contributor")
                action_name = chosen_action.lower()

                # Score candidate posts using Notion Mathematical Spec:
                # Score = lambda_rec * 2^(-dt / t_half) + beta_pop * min(1, ln(1 + Eng) / ln(1 + Eng_p99)) + gamma_echo * (1 + cos(e_i, e_j)) / 2
                scored_posts = []
                for p_id, p_uid, p_content, p_likes, p_shares, p_comments, p_created in raw_posts:
                    post_dict = {
                        "post_id": p_id,
                        "user_id": p_uid,
                        "content": p_content,
                        "likes": p_likes,
                        "shares": p_shares,
                        "comments": p_comments,
                        "age_rounds": max(0.5, float(round_num - (p_id % max(1, round_num + 1)))),
                        "alignment": agent.opinion_score,
                    }
                    agent_dict = {
                        "agent_id": agent_id,
                        "opinion_score": agent.opinion_score,
                        "embedding": agent.embedding,
                    }
                    score = compute_feed_score(
                        platform=self.platform,
                        post=post_dict,
                        agent=agent_dict,
                        current_hour=simulated_hour,
                        delta_t=post_dict["age_rounds"],
                    )
                    scored_posts.append((score, post_dict))

                scored_posts.sort(key=lambda x: x[0], reverse=True)
                target_post = scored_posts[0][1] if scored_posts else None

                if not target_post:
                    continue

                target_post_id = target_post["post_id"]
                target_author_id = target_post["user_id"]

                if chosen_action in ("LIKE_POST", "LIKE_VIDEO", "LIKE", "SAVE_POST"):
                    cursor.execute("UPDATE post SET num_likes = num_likes + 1 WHERE post_id = ?", (target_post_id,))
                    cursor.execute("INSERT INTO like (user_id, post_id, created_at) VALUES (?, ?, ?)", (agent_id, target_post_id, datetime.now().isoformat()))
                    like_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO trace (user_id, action, info, created_at) VALUES (?, ?, ?, ?)",
                        (agent_id, "like_post", json.dumps({"post_id": target_post_id, "like_id": like_id}, ensure_ascii=False), datetime.now().isoformat())
                    )

                elif chosen_action in ("CREATE_COMMENT", "COMMENT", "REPLY"):
                    comment_text = generate_platform_content(agent, self.platform, chosen_action, reference_post=target_post)
                    cursor.execute("UPDATE post SET num_comments = num_comments + 1 WHERE post_id = ?", (target_post_id,))
                    cursor.execute("INSERT INTO comment (post_id, user_id, content, created_at) VALUES (?, ?, ?, ?)", (target_post_id, agent_id, comment_text, datetime.now().isoformat()))
                    comment_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO trace (user_id, action, info, created_at) VALUES (?, ?, ?, ?)",
                        (agent_id, "create_comment", json.dumps({"post_id": target_post_id, "comment_id": comment_id, "content": comment_text}, ensure_ascii=False), datetime.now().isoformat())
                    )

                elif chosen_action in ("REPOST", "SHARE", "SHARE_TO_FRIENDS", "SHARE_STORY", "DUET_REACT", "QUOTE_POST"):
                    cursor.execute("UPDATE post SET num_shares = num_shares + 1 WHERE post_id = ?", (target_post_id,))
                    cursor.execute("INSERT INTO post (user_id, content, original_post_id, created_at) VALUES (?, ?, ?, ?)", (agent_id, target_post["content"], target_post_id, datetime.now().isoformat()))
                    new_post_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO trace (user_id, action, info, created_at) VALUES (?, ?, ?, ?)",
                        (agent_id, "repost", json.dumps({"post_id": target_post_id, "new_post_id": new_post_id}, ensure_ascii=False), datetime.now().isoformat())
                    )

                elif chosen_action in ("FOLLOW", "FOLLOW_CREATOR", "SUBSCRIBE", "CONNECT"):
                    cursor.execute("INSERT INTO follow (follower_id, followee_id, created_at) VALUES (?, ?, ?)", (agent_id, target_author_id, datetime.now().isoformat()))
                    follow_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO trace (user_id, action, info, created_at) VALUES (?, ?, ?, ?)",
                        (agent_id, "follow", json.dumps({"follow_id": follow_id, "target_id": target_author_id}, ensure_ascii=False), datetime.now().isoformat())
                    )

                else:
                    cursor.execute(
                        "INSERT INTO trace (user_id, action, info, created_at) VALUES (?, ?, ?, ?)",
                        (agent_id, action_name, json.dumps({"post_id": target_post_id}, ensure_ascii=False), datetime.now().isoformat())
                    )

            else: # lurker
                pass

        cursor.close()

    async def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


async def run_behavioral_platform_simulation(
    platform: str,
    config: Dict[str, Any],
    simulation_dir: str,
    action_logger: Optional[PlatformActionLogger] = None,
    main_logger: Optional[SimulationLogManager] = None,
    max_rounds: Optional[int] = None,
    barrier: Optional[asyncio.Barrier] = None,
) -> PlatformSimulation:
    """Menjalankan loop simulasi otonom untuk platform perilaku (TikTok, Instagram, Threads, LinkedIn, YouTube)."""
    result = PlatformSimulation()
    norm_p = platform.lower().strip()

    def log_info(msg):
        if main_logger:
            main_logger.info(f"[{norm_p.capitalize()}] {msg}")
        print(f"[{norm_p.capitalize()}] {msg}")

    log_info("Inisialisasi lingkungan simulasi perilaku...")

    model = create_model(config, use_boost=True)
    result.agent_graph = load_platform_agents(config, norm_p, simulation_dir, model=model)
    if result.agent_graph.get_num_agents() == 0:
        log_info(f"Peringatan: Tidak ada agen yang ditemukan untuk {norm_p}")
        return result

    agent_names = get_agent_names_from_config(config)
    for agent_id, agent in result.agent_graph.get_agents():
        if agent_id not in agent_names:
            agent_names[agent_id] = agent.name

    db_path = os.path.join(simulation_dir, f"{norm_p}_simulation.db")
    result.env = BehavioralPlatformEnv(
        agent_graph=result.agent_graph,
        platform=norm_p,
        database_path=db_path
    )
    await result.env.reset()
    log_info(f"Lingkungan {norm_p.capitalize()} aktif ({result.agent_graph.get_num_agents()} agen)")

    if action_logger:
        action_logger.log_simulation_start(config)

    total_actions = 0
    last_rowid = 0

    # Putaran 0: Eksekusi event awal
    event_config = config.get("event_config", {})
    initial_posts = event_config.get("initial_posts", [])

    if action_logger:
        action_logger.log_round_start(0, 0)

    initial_action_count = 0
    if initial_posts:
        initial_actions = {}
        for post in initial_posts:
            agent_id = post.get("poster_agent_id", 0)
            content = post.get("content", "")
            agent = result.agent_graph.get_agent(agent_id)
            if not agent and result.agent_graph.get_agents():
                agent = result.agent_graph.get_agents()[0][1]
            if agent:
                initial_actions[agent] = ManualAction(
                    action_type=ActionType.CREATE_POST,
                    action_args={"content": content}
                )
                if action_logger:
                    action_logger.log_action(
                        round_num=0,
                        agent_id=agent.agent_id,
                        agent_name=agent_names.get(agent.agent_id, f"Agent_{agent.agent_id}"),
                        action_type="CREATE_POST",
                        action_args={"content": content}
                    )
                    total_actions += 1
                    initial_action_count += 1

        if initial_actions:
            await result.env.step(initial_actions, simulated_hour=0, round_num=0)
            log_info(f"Dipublikasikan {len(initial_actions)} postingan awal")

    if action_logger:
        action_logger.log_round_end(0, initial_action_count, simulated_hours=0)

    # Main simulation loop
    time_config = config.get("time_config", {})
    total_hours = time_config.get("total_simulation_hours", 72)
    minutes_per_round = time_config.get("minutes_per_round", 30)
    total_rounds = (total_hours * 60) // minutes_per_round

    if max_rounds is not None and max_rounds > 0:
        original_rounds = total_rounds
        total_rounds = min(total_rounds, max_rounds)
        if total_rounds < original_rounds:
            log_info(f"Putaran dipotong: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")

    start_time = datetime.now()

    for round_num in range(total_rounds):
        if _shutdown_event and _shutdown_event.is_set():
            if main_logger:
                main_logger.info(f"Menerima sinyal berhenti pada putaran {round_num + 1}")
            break

        start_hour = time_config.get("start_hour", 8)
        simulated_minutes = round_num * minutes_per_round
        simulated_hour = (start_hour + (simulated_minutes // 60)) % 24
        simulated_day = (start_hour * 60 + simulated_minutes) // (60 * 24) + 1

        active_agents = get_active_agents_for_round(
            result.env, config, simulated_hour, round_num
        )

        if action_logger:
            action_logger.log_round_start(round_num + 1, simulated_hour)

        round_action_count = 0
        if active_agents:
            actions = {agent: LLMAction() for _, agent in active_agents}
            await result.env.step(actions, simulated_hour=simulated_hour, round_num=round_num)

            actual_actions, last_rowid = fetch_new_actions_from_db(
                db_path, last_rowid, agent_names
            )

            for action_data in actual_actions:
                if action_logger:
                    action_logger.log_action(
                        round_num=round_num + 1,
                        agent_id=action_data['agent_id'],
                        agent_name=action_data['agent_name'],
                        action_type=action_data['action_type'],
                        action_args=action_data['action_args']
                    )
                    total_actions += 1
                    round_action_count += 1

        if action_logger:
            action_logger.log_round_end(round_num + 1, round_action_count, simulated_hours=simulated_hour)

        if barrier is not None:
            try:
                await barrier.wait()
            except (asyncio.BrokenBarrierError, Exception):
                pass

        if (round_num + 1) % 20 == 0:
            progress = (round_num + 1) / total_rounds * 100
            log_info(f"Hari {simulated_day}, {simulated_hour:02d}:00 - Putaran {round_num + 1}/{total_rounds} ({progress:.1f}%)")

    if action_logger:
        action_logger.log_simulation_end(total_rounds, total_actions)

    result.total_actions = total_actions
    elapsed = (datetime.now() - start_time).total_seconds()
    log_info(f"Simulasi {norm_p.capitalize()} selesai! Waktu: {elapsed:.1f}d, Total aksi: {total_actions}")
    return result


async def run_twitter_simulation(
    config: Dict[str, Any],
    simulation_dir: str,
    action_logger: Optional[PlatformActionLogger] = None,
    main_logger: Optional[SimulationLogManager] = None,
    max_rounds: Optional[int] = None,
    barrier: Optional[asyncio.Barrier] = None,
) -> PlatformSimulation:
    """运行Twitter模拟
    
    Args:
        config: 模拟配置
        simulation_dir: 模拟目录
        action_logger: 动作日志记录器
        main_logger: 主日志管理器
        max_rounds: 最大模拟轮数（可选，用于截断过长的模拟）
        
    Returns:
        PlatformSimulation: 包含env和agent_graph的结果对象
    """
    result = PlatformSimulation()
    
    def log_info(msg):
        if main_logger:
            main_logger.info(f"[Twitter] {msg}")
        print(f"[Twitter] {msg}")
    
    log_info("初始化...")
    
    # Twitter 使用通用 LLM 配置
    model = create_model(config, use_boost=False)
    
    # OASIS Twitter使用CSV格式
    profile_path = os.path.join(simulation_dir, "twitter_profiles.csv")
    if not os.path.exists(profile_path):
        log_info(f"错误: Profile文件不存在: {profile_path}")
        return result
    
    patch_oasis_user_info_for_indonesian_style()
    result.agent_graph = await generate_twitter_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=TWITTER_ACTIONS,
    )
    enrich_social_agents_with_style(result.agent_graph, platform="twitter")
    
    # 从配置文件获取 Agent 真实名称映射（使用 entity_name 而非默认的 Agent_X）
    agent_names = get_agent_names_from_config(config)
    # 如果配置中没有某个 agent，则使用 OASIS 的默认名称
    for agent_id, agent in result.agent_graph.get_agents():
        if agent_id not in agent_names:
            agent_names[agent_id] = getattr(agent, 'name', f'Agent_{agent_id}')
    
    db_path = os.path.join(simulation_dir, "twitter_simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    # Opsi 2 (Patch): Menggunakan recsys_type="random" untuk mem-bypass Twitter/twhin-bert-base
    # Mencegah pemuatan model PyTorch transformer lokal dan mengeliminasi crash OOM (-9) / CPU saturation
    adaptive_semaphore = min(30, max(4, (os.cpu_count() or 2) * 2))
    twitter_platform = Platform(
        db_path=db_path,
        channel=Channel(),
        recsys_type="random",
        refresh_rec_post_count=2,
        max_rec_post_len=2,
        following_post_count=3,
    )
    result.env = oasis.make(
        agent_graph=result.agent_graph,
        platform=twitter_platform,
        database_path=db_path,
        semaphore=adaptive_semaphore,
    )
    
    await result.env.reset()
    log_info("环境已启动")
    
    if action_logger:
        action_logger.log_simulation_start(config)
    
    total_actions = 0
    last_rowid = 0  # 跟踪数据库中最后处理的行号（使用 rowid 避免 created_at 格式差异）
    
    # 执行初始事件
    event_config = config.get("event_config", {})
    initial_posts = event_config.get("initial_posts", [])
    
    # 记录 round 0 开始（初始事件阶段）
    if action_logger:
        action_logger.log_round_start(0, 0)  # round 0, simulated_hour 0
    
    initial_action_count = 0
    if initial_posts:
        initial_actions = {}
        for post in initial_posts:
            agent_id = post.get("poster_agent_id", 0)
            content = post.get("content", "")
            try:
                agent = result.env.agent_graph.get_agent(agent_id)
                initial_actions[agent] = ManualAction(
                    action_type=ActionType.CREATE_POST,
                    action_args={"content": content}
                )
                
                if action_logger:
                    action_logger.log_action(
                        round_num=0,
                        agent_id=agent_id,
                        agent_name=agent_names.get(agent_id, f"Agent_{agent_id}"),
                        action_type="CREATE_POST",
                        action_args={"content": content}
                    )
                    total_actions += 1
                    initial_action_count += 1
            except Exception:
                pass
        
        if initial_actions:
            await result.env.step(initial_actions)
            log_info(f"已发布 {len(initial_actions)} 条初始帖子")
    
    # 记录 round 0 结束
    if action_logger:
        action_logger.log_round_end(0, initial_action_count)
    
    # 主模拟循环
    time_config = config.get("time_config", {})
    total_hours = time_config.get("total_simulation_hours", 72)
    minutes_per_round = time_config.get("minutes_per_round", 30)
    total_rounds = (total_hours * 60) // minutes_per_round
    
    # 如果指定了最大轮数，则截断
    if max_rounds is not None and max_rounds > 0:
        original_rounds = total_rounds
        total_rounds = min(total_rounds, max_rounds)
        if total_rounds < original_rounds:
            log_info(f"轮数已截断: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
    
    start_time = datetime.now()
    
    for round_num in range(total_rounds):
        # 检查是否收到退出信号
        if _shutdown_event and _shutdown_event.is_set():
            if main_logger:
                main_logger.info(f"收到退出信号，在第 {round_num + 1} 轮停止模拟")
            break
        
        start_hour = time_config.get("start_hour", 8)
        simulated_minutes = round_num * minutes_per_round
        simulated_hour = (start_hour + (simulated_minutes // 60)) % 24
        simulated_day = (start_hour * 60 + simulated_minutes) // (60 * 24) + 1
        
        active_agents = get_active_agents_for_round(
            result.env, config, simulated_hour, round_num
        )
        
        # 无论是否有活跃agent，都记录round开始
        if action_logger:
            action_logger.log_round_start(round_num + 1, simulated_hour)
        
        if not active_agents:
            # 没有活跃agent时也记录round结束（actions_count=0）
            if action_logger:
                action_logger.log_round_end(round_num + 1, 0)
            continue
        
        actions = {agent: LLMAction() for _, agent in active_agents}
        await result.env.step(actions)
        
        # 从数据库获取实际执行的动作并记录
        actual_actions, last_rowid = fetch_new_actions_from_db(
            db_path, last_rowid, agent_names
        )
        
        round_action_count = 0
        for action_data in actual_actions:
            if action_logger:
                action_logger.log_action(
                    round_num=round_num + 1,
                    agent_id=action_data['agent_id'],
                    agent_name=action_data['agent_name'],
                    action_type=action_data['action_type'],
                    action_args=action_data['action_args']
                )
                total_actions += 1
                round_action_count += 1
        
        if action_logger:
            action_logger.log_round_end(round_num + 1, round_action_count)

        if barrier is not None:
            try:
                await barrier.wait()
            except (asyncio.BrokenBarrierError, Exception):
                pass

        if (round_num + 1) % 20 == 0:
            progress = (round_num + 1) / total_rounds * 100
            log_info(f"Day {simulated_day}, {simulated_hour:02d}:00 - Round {round_num + 1}/{total_rounds} ({progress:.1f}%)")

    # 注意：不关闭环境，保留给Interview使用

    if action_logger:
        action_logger.log_simulation_end(total_rounds, total_actions)

    result.total_actions = total_actions
    elapsed = (datetime.now() - start_time).total_seconds()
    log_info(f"模拟循环完成! 耗时: {elapsed:.1f}秒, 总动作: {total_actions}")

    return result


async def run_reddit_simulation(
    config: Dict[str, Any],
    simulation_dir: str,
    action_logger: Optional[PlatformActionLogger] = None,
    main_logger: Optional[SimulationLogManager] = None,
    max_rounds: Optional[int] = None,
    barrier: Optional[asyncio.Barrier] = None,
) -> PlatformSimulation:
    """运行Reddit模拟
    
    Args:
        config: 模拟配置
        simulation_dir: 模拟目录
        action_logger: 动作日志记录器
        main_logger: 主日志管理器
        max_rounds: 最大模拟轮数（可选，用于截断过长的模拟）
        
    Returns:
        PlatformSimulation: 包含env和agent_graph的结果对象
    """
    result = PlatformSimulation()
    
    def log_info(msg):
        if main_logger:
            main_logger.info(f"[Reddit] {msg}")
        print(f"[Reddit] {msg}")
    
    log_info("初始化...")
    
    # Reddit 使用加速 LLM 配置（如果有的话，否则回退到通用配置）
    model = create_model(config, use_boost=True)
    
    profile_path = os.path.join(simulation_dir, "reddit_profiles.json")
    if not os.path.exists(profile_path):
        log_info(f"错误: Profile文件不存在: {profile_path}")
        return result
    
    patch_oasis_user_info_for_indonesian_style()
    result.agent_graph = await generate_reddit_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=REDDIT_ACTIONS,
    )
    enrich_social_agents_with_style(result.agent_graph, platform="reddit")
    
    # 从配置文件获取 Agent 真实名称映射（使用 entity_name 而非默认的 Agent_X）
    agent_names = get_agent_names_from_config(config)
    # 如果配置中没有某个 agent，则使用 OASIS 的默认名称
    for agent_id, agent in result.agent_graph.get_agents():
        if agent_id not in agent_names:
            agent_names[agent_id] = getattr(agent, 'name', f'Agent_{agent_id}')
    
    db_path = os.path.join(simulation_dir, "reddit_simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    adaptive_semaphore = min(30, max(4, (os.cpu_count() or 2) * 2))
    result.env = oasis.make(
        agent_graph=result.agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=db_path,
        semaphore=adaptive_semaphore,
    )
    
    await result.env.reset()
    log_info("环境已启动")
    
    if action_logger:
        action_logger.log_simulation_start(config)
    
    total_actions = 0
    last_rowid = 0  # 跟踪数据库中最后处理的行号（使用 rowid 避免 created_at 格式差异）
    
    # 执行初始事件
    event_config = config.get("event_config", {})
    initial_posts = event_config.get("initial_posts", [])
    
    # 记录 round 0 开始（初始事件阶段）
    if action_logger:
        action_logger.log_round_start(0, 0)  # round 0, simulated_hour 0
    
    initial_action_count = 0
    if initial_posts:
        initial_actions = {}
        for post in initial_posts:
            agent_id = post.get("poster_agent_id", 0)
            content = post.get("content", "")
            try:
                agent = result.env.agent_graph.get_agent(agent_id)
                if agent in initial_actions:
                    if not isinstance(initial_actions[agent], list):
                        initial_actions[agent] = [initial_actions[agent]]
                    initial_actions[agent].append(ManualAction(
                        action_type=ActionType.CREATE_POST,
                        action_args={"content": content}
                    ))
                else:
                    initial_actions[agent] = ManualAction(
                        action_type=ActionType.CREATE_POST,
                        action_args={"content": content}
                    )
                
                if action_logger:
                    action_logger.log_action(
                        round_num=0,
                        agent_id=agent_id,
                        agent_name=agent_names.get(agent_id, f"Agent_{agent_id}"),
                        action_type="CREATE_POST",
                        action_args={"content": content}
                    )
                    total_actions += 1
                    initial_action_count += 1
            except Exception:
                pass
        
        if initial_actions:
            await result.env.step(initial_actions)
            log_info(f"已发布 {len(initial_actions)} 条初始帖子")
    
    # 记录 round 0 结束
    if action_logger:
        action_logger.log_round_end(0, initial_action_count)
    
    # 主模拟循环
    time_config = config.get("time_config", {})
    total_hours = time_config.get("total_simulation_hours", 72)
    minutes_per_round = time_config.get("minutes_per_round", 30)
    total_rounds = (total_hours * 60) // minutes_per_round
    
    # 如果指定了最大轮数，则截断
    if max_rounds is not None and max_rounds > 0:
        original_rounds = total_rounds
        total_rounds = min(total_rounds, max_rounds)
        if total_rounds < original_rounds:
            log_info(f"轮数已截断: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
    
    start_time = datetime.now()
    
    for round_num in range(total_rounds):
        # 检查是否收到退出信号
        if _shutdown_event and _shutdown_event.is_set():
            if main_logger:
                main_logger.info(f"收到退出信号，在第 {round_num + 1} 轮停止模拟")
            break
        
        start_hour = time_config.get("start_hour", 8)
        simulated_minutes = round_num * minutes_per_round
        simulated_hour = (start_hour + (simulated_minutes // 60)) % 24
        simulated_day = (start_hour * 60 + simulated_minutes) // (60 * 24) + 1
        
        active_agents = get_active_agents_for_round(
            result.env, config, simulated_hour, round_num
        )
        
        # 无论是否有活跃agent，都记录round开始
        if action_logger:
            action_logger.log_round_start(round_num + 1, simulated_hour)
        
        if not active_agents:
            # 没有活跃agent时也记录round结束（actions_count=0）
            if action_logger:
                action_logger.log_round_end(round_num + 1, 0)
            continue
        
        actions = {agent: LLMAction() for _, agent in active_agents}
        await result.env.step(actions)
        
        # 从数据库获取实际执行的动作并记录
        actual_actions, last_rowid = fetch_new_actions_from_db(
            db_path, last_rowid, agent_names
        )
        
        round_action_count = 0
        for action_data in actual_actions:
            if action_logger:
                action_logger.log_action(
                    round_num=round_num + 1,
                    agent_id=action_data['agent_id'],
                    agent_name=action_data['agent_name'],
                    action_type=action_data['action_type'],
                    action_args=action_data['action_args']
                )
                total_actions += 1
                round_action_count += 1
        
        if action_logger:
            action_logger.log_round_end(round_num + 1, round_action_count)

        if barrier is not None:
            try:
                await barrier.wait()
            except (asyncio.BrokenBarrierError, Exception):
                pass

        if (round_num + 1) % 20 == 0:
            progress = (round_num + 1) / total_rounds * 100
            log_info(f"Day {simulated_day}, {simulated_hour:02d}:00 - Round {round_num + 1}/{total_rounds} ({progress:.1f}%)")

    # 注意：不关闭环境，保留给Interview使用

    if action_logger:
        action_logger.log_simulation_end(total_rounds, total_actions)
    
    result.total_actions = total_actions
    elapsed = (datetime.now() - start_time).total_seconds()
    log_info(f"模拟循环完成! 耗时: {elapsed:.1f}秒, 总动作: {total_actions}")
    
    return result


async def main():
    parser = argparse.ArgumentParser(description='OASIS & Behavioral Multi-Platform Parallel Simulation')
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='配置文件路径 (simulation_config.json)'
    )
    parser.add_argument(
        '--twitter-only',
        action='store_true',
        help='只运行Twitter模拟'
    )
    parser.add_argument(
        '--reddit-only',
        action='store_true',
        help='只运行Reddit模拟'
    )
    parser.add_argument(
        '--platforms',
        type=str,
        default=None,
        help='要运行的平台列表，逗号分隔 (如 twitter,reddit,tiktok,instagram,threads,linkedin,youtube)'
    )
    parser.add_argument(
        '--max-rounds',
        type=int,
        default=None,
        help='最大模拟轮数（可选，用于截断过长的模拟）'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        default=False,
        help='模拟完成后立即关闭环境，不进入等待命令模式'
    )

    args = parser.parse_args()

    # 在 main 函数开始时创建 shutdown 事件，确保整个程序都能响应退出信号
    global _shutdown_event
    _shutdown_event = asyncio.Event()

    if not os.path.exists(args.config):
        print(f"错误: 配置文件不存在: {args.config}")
        sys.exit(1)

    config = load_config(args.config)
    simulation_dir = os.path.dirname(args.config) or "."
    wait_for_commands = not args.no_wait

    # Tentukan platform yang akan dijalankan
    if args.twitter_only:
        selected_platforms = ["twitter"]
    elif args.reddit_only:
        selected_platforms = ["reddit"]
    elif args.platforms:
        selected_platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]
    elif config.get("platforms"):
        selected_platforms = [p.strip().lower() for p in config["platforms"] if p.strip()]
    else:
        # Cek profil yang tersedia di direktori atau jalankan semua platform kanonikal
        found_platforms = []
        for p in CANONICAL_PLATFORMS:
            if p == "twitter" and os.path.exists(os.path.join(simulation_dir, "twitter_profiles.csv")):
                found_platforms.append(p)
            elif os.path.exists(os.path.join(simulation_dir, f"{p}_profiles.json")):
                found_platforms.append(p)
        if found_platforms:
            selected_platforms = found_platforms
        else:
            selected_platforms = list(CANONICAL_PLATFORMS)

    # Pastikan platform valid dan terurut unik
    selected_platforms = [p for p in CANONICAL_PLATFORMS if p in selected_platforms]
    if not selected_platforms:
        selected_platforms = ["twitter", "reddit"]

    # 初始化日志配置（禁用 OASIS 日志，清理旧文件）
    init_logging_for_simulation(simulation_dir)

    # 创建日志管理器
    log_manager = SimulationLogManager(simulation_dir)
    platform_loggers = {p: log_manager.get_platform_logger(p) for p in selected_platforms}

    log_manager.info("=" * 60)
    log_manager.info(f"OASIS & Behavioral Multi-Platform Parallel Simulation ({len(selected_platforms)} Platform)")
    log_manager.info(f"配置文件: {args.config}")
    log_manager.info(f"模拟ID: {config.get('simulation_id', 'unknown')}")
    log_manager.info(f"运行平台: {', '.join(p.capitalize() for p in selected_platforms)}")
    log_manager.info(f"等待命令模式: {'启用' if wait_for_commands else '禁用'}")
    log_manager.info("=" * 60)

    time_config = config.get("time_config", {})
    total_hours = time_config.get('total_simulation_hours', 72)
    minutes_per_round = time_config.get('minutes_per_round', 30)
    config_total_rounds = (total_hours * 60) // minutes_per_round

    log_manager.info(f"模拟参数:")
    log_manager.info(f"  - 总模拟时长: {total_hours}小时")
    log_manager.info(f"  - 每轮时间: {minutes_per_round}分钟")
    log_manager.info(f"  - 配置总轮数: {config_total_rounds}")
    if args.max_rounds:
        log_manager.info(f"  - 最大轮数限制: {args.max_rounds}")
        if args.max_rounds < config_total_rounds:
            log_manager.info(f"  - 实际执行轮数: {args.max_rounds} (已截断)")
    log_manager.info(f"  - Agent数量: {len(config.get('agent_configs', []))}")

    log_manager.info("日志结构:")
    log_manager.info(f"  - 主日志: simulation.log")
    for p in selected_platforms:
        log_manager.info(f"  - {p.capitalize()}动作: {p}/actions.jsonl")
    log_manager.info("=" * 60)

    start_time = datetime.now()

    # Inisialisasi barrier sinkronisasi antar-platform per ronde virtual
    barrier = asyncio.Barrier(len(selected_platforms)) if len(selected_platforms) > 1 else None

    tasks = []
    task_platforms = []
    for p in selected_platforms:
        p_logger = platform_loggers[p]
        if p == "twitter":
            tasks.append(run_twitter_simulation(config, simulation_dir, p_logger, log_manager, args.max_rounds, barrier=barrier))
            task_platforms.append("twitter")
        elif p == "reddit":
            tasks.append(run_reddit_simulation(config, simulation_dir, p_logger, log_manager, args.max_rounds, barrier=barrier))
            task_platforms.append("reddit")
        else:
            tasks.append(run_behavioral_platform_simulation(p, config, simulation_dir, p_logger, log_manager, args.max_rounds, barrier=barrier))
            task_platforms.append(p)

    results_list = await asyncio.gather(*tasks)
    platform_results = dict(zip(task_platforms, results_list))

    total_elapsed = (datetime.now() - start_time).total_seconds()
    log_manager.info("=" * 60)
    log_manager.info(f"模拟循环完成! 总耗时: {total_elapsed:.1f}秒")

    # 是否进入等待命令模式
    if wait_for_commands:
        log_manager.info("")
        log_manager.info("=" * 60)
        log_manager.info("进入等待命令模式 - 环境保持运行")
        log_manager.info("支持的命令: interview, batch_interview, close_env")
        log_manager.info("=" * 60)

        # 创建IPC处理器
        environments = {}
        agent_graphs = {}
        for p, sim_res in platform_results.items():
            if sim_res and sim_res.env:
                environments[p] = sim_res.env
            if sim_res and sim_res.agent_graph:
                agent_graphs[p] = sim_res.agent_graph

        ipc_handler = ParallelIPCHandler(
            simulation_dir=simulation_dir,
            twitter_env=environments.get("twitter"),
            twitter_agent_graph=agent_graphs.get("twitter"),
            reddit_env=environments.get("reddit"),
            reddit_agent_graph=agent_graphs.get("reddit"),
            environments=environments,
            agent_graphs=agent_graphs,
        )
        ipc_handler.update_status("alive")

        # 等待命令循环（使用全局 _shutdown_event）
        try:
            while not _shutdown_event.is_set():
                should_continue = await ipc_handler.process_commands()
                if not should_continue:
                    break
                # 使用 wait_for 替代 sleep，这样可以响应 shutdown_event
                try:
                    await asyncio.wait_for(_shutdown_event.wait(), timeout=0.5)
                    break  # 收到退出信号
                except asyncio.TimeoutError:
                    pass  # 超时继续循环
        except KeyboardInterrupt:
            print("\n收到中断信号")
        except asyncio.CancelledError:
            print("\n任务被取消")
        except Exception as e:
            print(f"\n命令处理出错: {e}")

        log_manager.info("\n关闭环境...")
        ipc_handler.update_status("stopped")

    # 关闭各平台环境
    for p, sim_res in platform_results.items():
        if sim_res and sim_res.env:
            try:
                await sim_res.env.close()
                log_manager.info(f"[{p.capitalize()}] 环境已关闭")
            except Exception as e:
                log_manager.warning(f"[{p.capitalize()}] 关闭环境时出错: {e}")

    log_manager.info("=" * 60)
    log_manager.info(f"全部完成!")
    log_manager.info(f"日志文件:")
    log_manager.info(f"  - {os.path.join(simulation_dir, 'simulation.log')}")
    for p in selected_platforms:
        log_manager.info(f"  - {os.path.join(simulation_dir, p, 'actions.jsonl')}")
    log_manager.info("=" * 60)


def setup_signal_handlers(loop=None):
    """
    设置信号处理器，确保收到 SIGTERM/SIGINT 时能够正确退出
    
    持久化模拟场景：模拟完成后不退出，等待 interview 命令
    当收到终止信号时，需要：
    1. 通知 asyncio 循环退出等待
    2. 让程序有机会正常清理资源（关闭数据库、环境等）
    3. 然后才退出
    """
    def signal_handler(signum, frame):
        global _cleanup_done
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        print(f"\n收到 {sig_name} 信号，正在退出...")
        
        if not _cleanup_done:
            _cleanup_done = True
            # 设置事件通知 asyncio 循环退出（让循环有机会清理资源）
            if _shutdown_event:
                _shutdown_event.set()
        
        # 不要直接 sys.exit()，让 asyncio 循环正常退出并清理资源
        # 如果是重复收到信号，才强制退出
        else:
            print("强制退出...")
            sys.exit(1)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    setup_signal_handlers()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被中断")
    except SystemExit:
        pass
    finally:
        # 清理 multiprocessing 资源跟踪器（防止退出时的警告）
        try:
            from multiprocessing import resource_tracker
            resource_tracker._resource_tracker._stop()
        except Exception:
            pass
        print("模拟进程已退出")
