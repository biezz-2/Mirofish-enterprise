"""
OASIS模拟管理器
管理Twitter和Reddit双平台并行模拟
使用预设脚本 + LLM智能生成配置参数
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.logger import get_logger
from .zep_entity_reader import ZepEntityReader, FilteredEntities
from .oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from .simulation_config_generator import SimulationConfigGenerator, SimulationParameters
from ..utils.locale import t

logger = get_logger('mirofish.simulation')


class SimulationStatus(str, Enum):
    """模拟状态"""
    CREATED = "created"
    PREPARING = "preparing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    PAUSED = "paused"
    STOPPED = "stopped"      # 模拟被手动停止
    COMPLETED = "completed"  # 模拟自然完成
    FAILED = "failed"


class PlatformType(str, Enum):
    """平台类型"""
    TWITTER = "twitter"
    REDDIT = "reddit"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    THREADS = "threads"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


CANONICAL_PLATFORMS = (
    "instagram",
    "linkedin",
    "reddit",
    "threads",
    "tiktok",
    "twitter",
    "youtube",
)
CANONICAL_PLATFORMS_SET = set(CANONICAL_PLATFORMS)
PLATFORM_ALIASES = {
    "x": "twitter",
    "x_twitter": "twitter",
    "ig": "instagram",
    "insta": "instagram",
    "yt": "youtube",
    "li": "linkedin",
    "th": "threads",
}


def normalize_platforms(
    platforms: Optional[List[str]] = None,
    enable_twitter: bool = True,
    enable_reddit: bool = True,
) -> List[str]:
    """
    规范化平台列表并校验合法性。
    支持向后兼容 enable_twitter / enable_reddit。
    """
    if platforms is None:
        res = []
        if enable_twitter:
            res.append("twitter")
        if enable_reddit:
            res.append("reddit")
        return res

    resolved = []
    seen = set()
    for raw in platforms:
        p = str(raw).lower().strip()
        p = PLATFORM_ALIASES.get(p, p)
        if p not in CANONICAL_PLATFORMS_SET:
            raise ValueError(f"不支持的平台: {raw}")
        if p not in seen:
            seen.add(p)
            resolved.append(p)
    return resolved


def _atomic_json_dump(path: str, value: Dict[str, Any]) -> None:
    """Write JSON through a sibling temporary file so readers never see partial JSON."""
    temporary_path = f"{path}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
    os.replace(temporary_path, path)


def migrate_prepared_simulation(simulation_dir: str) -> Dict[str, Any]:
    """Expand an inactive prepared simulation using its existing generated profiles."""
    simulation_dir = os.fspath(simulation_dir)
    state_path = os.path.join(simulation_dir, "state.json")
    config_path = os.path.join(simulation_dir, "simulation_config.json")
    reddit_path = os.path.join(simulation_dir, "reddit_profiles.json")
    twitter_path = os.path.join(simulation_dir, "twitter_profiles.csv")
    if not os.path.isfile(state_path):
        raise ValueError("prepared simulation requires state.json")
    with open(state_path, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    if state.get("status") != SimulationStatus.READY.value:
        raise ValueError("only a ready simulation can be migrated without process control")
    required_paths = (config_path, reddit_path, twitter_path)
    if not all(os.path.isfile(path) for path in required_paths):
        raise ValueError("prepared simulation requires config, Reddit, and Twitter artifacts")
    if not state.get("profiles_generated") or not state.get("config_generated"):
        raise ValueError("only a generated prepared simulation can be migrated")

    with open(reddit_path, "r", encoding="utf-8") as handle:
        reddit_profiles = json.load(handle)
    if not isinstance(reddit_profiles, list) or len(reddit_profiles) != state.get("profiles_count"):
        raise ValueError("Reddit profile artifact does not match state profiles_count")

    for platform in CANONICAL_PLATFORMS:
        if platform in {"reddit", "twitter"}:
            continue
        destination = os.path.join(simulation_dir, f"{platform}_profiles.json")
        temporary_path = f"{destination}.tmp"
        shutil.copyfile(reddit_path, temporary_path)
        os.replace(temporary_path, destination)

    with open(config_path, "r", encoding="utf-8") as handle:
        config = json.load(handle)
    from .platform_behaviors import PLATFORM_CHARACTERISTICS

    existing_configs = config.get("platform_configs") or {}
    legacy_configs = {
        "twitter": config.get("twitter_config"),
        "reddit": config.get("reddit_config"),
    }
    platform_configs = {}
    for platform in CANONICAL_PLATFORMS:
        platform_config = existing_configs.get(platform) or legacy_configs.get(platform)
        if not platform_config:
            characteristics = PLATFORM_CHARACTERISTICS[platform]
            platform_config = {
                "platform": platform,
                "recency_weight": characteristics["recency_weight"],
                "popularity_weight": characteristics["popularity_weight"],
                "relevance_weight": characteristics["relevance_weight"],
                "viral_threshold": int(characteristics["viral_threshold"]),
                "echo_chamber_strength": float(characteristics["echo_chamber_strength"]),
            }
        platform_configs[platform] = platform_config
    config["platforms"] = list(CANONICAL_PLATFORMS)
    config["platform_configs"] = platform_configs
    _atomic_json_dump(config_path, config)

    old_statuses = state.get("platform_statuses") or {}
    state["platforms"] = list(CANONICAL_PLATFORMS)
    state["enable_twitter"] = True
    state["enable_reddit"] = True
    state["platform_statuses"] = {
        platform: old_statuses.get(platform, state.get(f"{platform}_status", "not_started"))
        for platform in CANONICAL_PLATFORMS
    }
    state["platform_states"] = {
        platform: {
            "profiles_count": state["profiles_count"],
            "prepared": True,
            "config_generated": True,
        }
        for platform in CANONICAL_PLATFORMS
    }
    state["twitter_status"] = state["platform_statuses"]["twitter"]
    state["reddit_status"] = state["platform_statuses"]["reddit"]
    _atomic_json_dump(state_path, state)
    return state


@dataclass
class SimulationState:
    """模拟状态"""
    simulation_id: str
    project_id: str
    graph_id: str
    
    # 平台列表及启用状态
    platforms: Optional[List[str]] = None
    enable_twitter: bool = True
    enable_reddit: bool = True
    # 状态
    status: SimulationStatus = SimulationStatus.CREATED
    
    # 准备阶段数据
    entities_count: int = 0
    profiles_count: int = 0
    entity_types: List[str] = field(default_factory=list)
    
    # 配置生成信息
    profiles_generated: bool = False
    config_generated: bool = False
    config_reasoning: str = ""
    
    # 运行时数据与平台状态持久化
    current_round: int = 0
    platform_statuses: Dict[str, str] = field(default_factory=dict)
    platform_states: Dict[str, Any] = field(default_factory=dict)
    twitter_status: str = "not_started"
    reddit_status: str = "not_started"
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 错误信息
    error: Optional[str] = None
    
    def __post_init__(self):
        # 保持 platforms 和 enable_twitter / enable_reddit 逻辑同步
        if self.platforms is None:
            self.platforms = []
            if self.enable_twitter:
                self.platforms.append("twitter")
            if self.enable_reddit:
                self.platforms.append("reddit")
        else:
            self.enable_twitter = "twitter" in self.platforms
            self.enable_reddit = "reddit" in self.platforms

        if not self.platform_statuses:
            self.platform_statuses = {p: "not_started" for p in self.platforms}

        if "twitter" in self.platform_statuses:
            self.twitter_status = self.platform_statuses["twitter"]
        elif not self.enable_twitter:
            self.twitter_status = "disabled"

        if "reddit" in self.platform_statuses:
            self.reddit_status = self.platform_statuses["reddit"]
        elif not self.enable_reddit:
            self.reddit_status = "disabled"

    def to_dict(self) -> Dict[str, Any]:
        """完整状态字典（内部使用）"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "platforms": self.platforms,
            "enable_twitter": self.enable_twitter,
            "enable_reddit": self.enable_reddit,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "profiles_generated": self.profiles_generated,
            "config_generated": self.config_generated,
            "config_reasoning": self.config_reasoning,
            "current_round": self.current_round,
            "platform_statuses": self.platform_statuses,
            "platform_states": self.platform_states,
            "twitter_status": self.twitter_status,
            "reddit_status": self.reddit_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }
    
    def get_default_platform(self) -> str:
        """根据启用状态返回默认平台"""
        if "reddit" in self.platforms and "twitter" in self.platforms:
            return "reddit"
        elif "twitter" in self.platforms:
            return "twitter"
        elif self.platforms:
            return self.platforms[0]
        elif self.enable_twitter and not self.enable_reddit:
            return "twitter"
        return "reddit"

    def to_simple_dict(self) -> Dict[str, Any]:
        """简化状态字典（API返回使用）"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "platforms": self.platforms,
            "enable_twitter": self.enable_twitter,
            "enable_reddit": self.enable_reddit,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "profiles_generated": self.profiles_generated,
            "config_generated": self.config_generated,
            "platform_statuses": self.platform_statuses,
            "error": self.error,
        }

class SimulationManager:
    """
    模拟管理器
    
    核心功能：
    1. 从Zep图谱读取实体并过滤
    2. 生成OASIS Agent Profile
    3. 使用LLM智能生成模拟配置参数
    4. 准备预设脚本所需的所有文件
    """
    
    # 模拟数据存储目录
    SIMULATION_DATA_DIR = os.path.join(
        os.path.dirname(__file__), 
        '../../uploads/simulations'
    )
    
    def __init__(self):
        # 确保目录存在
        os.makedirs(self.SIMULATION_DATA_DIR, exist_ok=True)
        
        # 内存中的模拟状态缓存
        self._simulations: Dict[str, SimulationState] = {}
    
    def _get_simulation_dir(self, simulation_id: str) -> str:
        """获取模拟数据目录"""
        sim_dir = os.path.join(self.SIMULATION_DATA_DIR, simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        return sim_dir
    
    def _save_simulation_state(self, state: SimulationState):
        """保存模拟状态到文件"""
        sim_dir = self._get_simulation_dir(state.simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        state.updated_at = datetime.now().isoformat()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        
        self._simulations[state.simulation_id] = state
    
    def _load_simulation_state(self, simulation_id: str) -> Optional[SimulationState]:
        """从文件加载模拟状态"""
        if simulation_id in self._simulations:
            return self._simulations[simulation_id]
        
        sim_dir = self._get_simulation_dir(simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        if not os.path.exists(state_file):
            return None
        
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        platforms = data.get("platforms")
        enable_twitter = data.get("enable_twitter", True)
        enable_reddit = data.get("enable_reddit", True)
        if platforms is None:
            platforms = []
            if enable_twitter:
                platforms.append("twitter")
            if enable_reddit:
                platforms.append("reddit")

        platform_statuses = data.get("platform_statuses") or {}
        if not platform_statuses:
            for p in platforms:
                if p == "twitter":
                    platform_statuses[p] = data.get("twitter_status", "not_started")
                elif p == "reddit":
                    platform_statuses[p] = data.get("reddit_status", "not_started")
                else:
                    platform_statuses[p] = "not_started"

        state = SimulationState(
            simulation_id=simulation_id,
            project_id=data.get("project_id", ""),
            graph_id=data.get("graph_id", ""),
            platforms=platforms,
            enable_twitter=enable_twitter,
            enable_reddit=enable_reddit,
            status=SimulationStatus(data.get("status", "created")),
            entities_count=data.get("entities_count", 0),
            profiles_count=data.get("profiles_count", 0),
            entity_types=data.get("entity_types", []),
            profiles_generated=data.get("profiles_generated", False),
            config_generated=data.get("config_generated", False),
            config_reasoning=data.get("config_reasoning", ""),
            current_round=data.get("current_round", 0),
            platform_statuses=platform_statuses,
            platform_states=data.get("platform_states", {}),
            twitter_status=data.get("twitter_status", "not_started"),
            reddit_status=data.get("reddit_status", "not_started"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            error=data.get("error"),
        )
        
        self._simulations[simulation_id] = state
        return state
    
    def create_simulation(
        self,
        project_id: str,
        graph_id: str,
        enable_twitter: bool = True,
        enable_reddit: bool = True,
        platforms: Optional[List[str]] = None,
    ) -> SimulationState:
        """
        创建新的模拟
        
        Args:
            project_id: 项目ID
            graph_id: Zep图谱ID
            enable_twitter: 是否启用Twitter模拟
            enable_reddit: 是否启用Reddit模拟
            platforms: 显式指定的平台列表 (可选)
            
        Returns:
            SimulationState
        """
        import uuid
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        
        resolved_platforms = normalize_platforms(platforms, enable_twitter, enable_reddit)
        resolved_twitter = "twitter" in resolved_platforms
        resolved_reddit = "reddit" in resolved_platforms

        platform_statuses = {p: "not_started" for p in resolved_platforms}
        platform_states = {p: {} for p in resolved_platforms}

        state = SimulationState(
            simulation_id=simulation_id,
            project_id=project_id,
            graph_id=graph_id,
            platforms=resolved_platforms,
            enable_twitter=resolved_twitter,
            enable_reddit=resolved_reddit,
            status=SimulationStatus.CREATED,
            platform_statuses=platform_statuses,
            platform_states=platform_states,
            twitter_status=platform_statuses.get("twitter", "not_started" if resolved_twitter else "disabled"),
            reddit_status=platform_statuses.get("reddit", "not_started" if resolved_reddit else "disabled"),
        )
        
        self._save_simulation_state(state)
        logger.info(f"创建模拟: {simulation_id}, project={project_id}, graph={graph_id}, platforms={resolved_platforms}")
        
        return state
    
    def prepare_simulation(
        self,
        simulation_id: str,
        simulation_requirement: str,
        document_text: str,
        defined_entity_types: Optional[List[str]] = None,
        use_llm_for_profiles: bool = True,
        progress_callback: Optional[callable] = None,
        parallel_profile_count: int = 3
    ) -> SimulationState:
        """
        准备模拟环境（全程自动化）
        
        步骤：
        1. 从Zep图谱读取并过滤实体
        2. 为每个实体生成OASIS Agent Profile（可选LLM增强，支持并行）
        3. 使用LLM智能生成模拟配置参数（时间、活跃度、发言频率等）
        4. 保存配置文件和Profile文件
        5. 复制预设脚本到模拟目录
        
        Args:
            simulation_id: 模拟ID
            simulation_requirement: 模拟需求描述（用于LLM生成配置）
            document_text: 原始文档内容（用于LLM理解背景）
            defined_entity_types: 预定义的实体类型（可选）
            use_llm_for_profiles: 是否使用LLM生成详细人设
            progress_callback: 进度回调函数 (stage, progress, message)
            parallel_profile_count: 并行生成人设的数量，默认3
            
        Returns:
            SimulationState
        """
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")
        
        try:
            state.status = SimulationStatus.PREPARING
            state.error = None
            state.profiles_generated = False
            state.config_generated = False
            state.config_reasoning = ""
            self._save_simulation_state(state)
            
            sim_dir = self._get_simulation_dir(simulation_id)
            
            # ========== 阶段1: 读取并过滤实体 ==========
            if progress_callback:
                progress_callback("reading", 0, t('progress.connectingZepGraph'))
            
            reader = ZepEntityReader()
            
            if progress_callback:
                progress_callback("reading", 30, t('progress.readingNodeData'))
            
            filtered = reader.filter_defined_entities(
                graph_id=state.graph_id,
                defined_entity_types=defined_entity_types,
                enrich_with_edges=True
            )
            
            state.entities_count = filtered.filtered_count
            state.entity_types = list(filtered.entity_types)
            
            if progress_callback:
                progress_callback(
                    "reading", 100,
                    t('progress.readingComplete', count=filtered.filtered_count),
                    current=filtered.filtered_count,
                    total=filtered.filtered_count
                )
            
            if filtered.filtered_count == 0:
                state.status = SimulationStatus.FAILED
                state.error = "没有找到符合条件的实体，请检查图谱是否正确构建"
                self._save_simulation_state(state)
                raise ValueError(state.error)
            
            # ========== 阶段2: 生成Agent Profile ==========
            total_entities = len(filtered.entities)
            
            if progress_callback:
                progress_callback(
                    "generating_profiles", 0,
                    t('progress.startGenerating'),
                    current=0,
                    total=total_entities
                )
            
            # 传入graph_id以启用Zep检索功能，获取更丰富的上下文
            generator = OasisProfileGenerator(graph_id=state.graph_id)
            
            def profile_progress(current, total, msg):
                if progress_callback:
                    progress_callback(
                        "generating_profiles", 
                        int(current / total * 100), 
                        msg,
                        current=current,
                        total=total,
                        item_name=msg
                    )
            
            # 设置实时保存的文件路径
            realtime_output_path = None
            realtime_platform = "reddit"
            if "reddit" in state.platforms:
                realtime_output_path = os.path.join(sim_dir, "reddit_profiles.json")
                realtime_platform = "reddit"
            elif "twitter" in state.platforms:
                realtime_output_path = os.path.join(sim_dir, "twitter_profiles.csv")
                realtime_platform = "twitter"
            elif state.platforms:
                first_p = state.platforms[0]
                realtime_output_path = os.path.join(sim_dir, f"{first_p}_profiles.json")
                realtime_platform = first_p
            
            profiles = generator.generate_profiles_from_entities(
                entities=filtered.entities,
                use_llm=use_llm_for_profiles,
                progress_callback=profile_progress,
                graph_id=state.graph_id,  # 传入graph_id用于Zep检索
                parallel_count=parallel_profile_count,  # 并行生成数量
                realtime_output_path=realtime_output_path,  # 实时保存路径
                output_platform=realtime_platform  # 输出格式
            )
            
            state.profiles_count = len(profiles)
            state.profiles_generated = len(profiles) > 0
            self._save_simulation_state(state)
            
            # 保存各平台Profile文件（Twitter使用CSV，其它平台使用JSON）
            if progress_callback:
                progress_callback(
                    "generating_profiles", 95,
                    t('progress.savingProfiles'),
                    current=total_entities,
                    total=total_entities
                )
            
            for p in state.platforms:
                if p == "twitter":
                    generator.save_profiles(
                        profiles=profiles,
                        file_path=os.path.join(sim_dir, "twitter_profiles.csv"),
                        platform="twitter"
                    )
                else:
                    generator.save_profiles(
                        profiles=profiles,
                        file_path=os.path.join(sim_dir, f"{p}_profiles.json"),
                        platform=p
                    )
                state.platform_statuses[p] = "ready"
                state.platform_states[p] = {"profiles_count": len(profiles), "prepared": True}

            if "twitter" in state.platform_statuses:
                state.twitter_status = state.platform_statuses["twitter"]
            if "reddit" in state.platform_statuses:
                state.reddit_status = state.platform_statuses["reddit"]
            self._save_simulation_state(state)
            if progress_callback:
                progress_callback(
                    "generating_profiles", 100,
                    t('progress.profilesComplete', count=len(profiles)),
                    current=len(profiles),
                    total=len(profiles)
                )
            
            # ========== 阶段3: LLM智能生成模拟配置 ==========
            if progress_callback:
                progress_callback(
                    "generating_config", 0,
                    t('progress.analyzingRequirements'),
                    current=0,
                    total=3
                )
            
            config_generator = SimulationConfigGenerator()
            
            if progress_callback:
                progress_callback(
                    "generating_config", 30,
                    t('progress.callingLLMConfig'),
                    current=1,
                    total=3
                )
            
            sim_params = config_generator.generate_config(
                simulation_id=simulation_id,
                project_id=state.project_id,
                graph_id=state.graph_id,
                simulation_requirement=simulation_requirement,
                document_text=document_text,
                entities=filtered.entities,
                enable_twitter=state.enable_twitter,
                enable_reddit=state.enable_reddit,
                platforms=state.platforms,
            )
            if progress_callback:
                progress_callback(
                    "generating_config", 70,
                    t('progress.savingConfigFiles'),
                    current=2,
                    total=3
                )
            
            # 保存配置文件
            config_path = os.path.join(sim_dir, "simulation_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(sim_params.to_json())
            
            state.config_generated = True
            state.config_reasoning = sim_params.generation_reasoning
            
            if progress_callback:
                progress_callback(
                    "generating_config", 100,
                    t('progress.configComplete'),
                    current=3,
                    total=3
                )
            
            # 注意：运行脚本保留在 backend/scripts/ 目录，不再复制到模拟目录
            # 启动模拟时，simulation_runner 会从 scripts/ 目录运行脚本
            
            # 更新状态
            state.status = SimulationStatus.READY
            for p in state.platforms:
                state.platform_statuses[p] = "ready"
                if p in state.platform_states:
                    state.platform_states[p]["config_generated"] = True
            if "twitter" in state.platform_statuses:
                state.twitter_status = state.platform_statuses["twitter"]
            if "reddit" in state.platform_statuses:
                state.reddit_status = state.platform_statuses["reddit"]
            self._save_simulation_state(state)
            logger.info(f"模拟准备完成: {simulation_id}, "
                       f"entities={state.entities_count}, profiles={state.profiles_count}")
            
            return state
            
        except Exception as e:
            logger.error(f"模拟准备失败: {simulation_id}, error={str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            state.status = SimulationStatus.FAILED
            state.error = str(e)
            self._save_simulation_state(state)
            raise
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationState]:
        """获取模拟状态"""
        return self._load_simulation_state(simulation_id)
    
    def list_simulations(self, project_id: Optional[str] = None) -> List[SimulationState]:
        """列出所有模拟"""
        simulations = []
        
        if os.path.exists(self.SIMULATION_DATA_DIR):
            for sim_id in os.listdir(self.SIMULATION_DATA_DIR):
                # 跳过隐藏文件（如 .DS_Store）和非目录文件
                sim_path = os.path.join(self.SIMULATION_DATA_DIR, sim_id)
                if sim_id.startswith('.') or not os.path.isdir(sim_path):
                    continue
                
                state = self._load_simulation_state(sim_id)
                if state:
                    if project_id is None or state.project_id == project_id:
                        simulations.append(state)
        
        return simulations
    
    def get_profiles(self, simulation_id: str, platform: str = None) -> List[Dict[str, Any]]:
        """获取模拟的Agent Profile"""
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")

        if platform is None:
            platform = state.get_default_platform()

        norm_p = PLATFORM_ALIASES.get(str(platform).lower().strip(), str(platform).lower().strip())
        if norm_p not in CANONICAL_PLATFORMS_SET:
            raise ValueError(f"不支持的平台: {platform}")

        sim_dir = self._get_simulation_dir(simulation_id)
        if norm_p == "twitter":
            profile_path = os.path.join(sim_dir, "twitter_profiles.csv")
            if not os.path.exists(profile_path):
                return []
            import csv
            with open(profile_path, 'r', encoding='utf-8', newline='') as f:
                return list(csv.DictReader(f))
        else:
            profile_path = os.path.join(sim_dir, f"{norm_p}_profiles.json")
            if not os.path.exists(profile_path):
                # Never substitute another platform's profile file. A missing
                # platform artifact is unavailable, not evidence from Reddit.
                if norm_p == "reddit":
                    fallback = os.path.join(sim_dir, "reddit_profiles.json")
                    if os.path.exists(fallback):
                        with open(fallback, 'r', encoding='utf-8') as f:
                            return json.load(f)
                return []

            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def get_simulation_config(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """获取模拟配置"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_run_instructions(self, simulation_id: str) -> Dict[str, str]:
        """获取运行说明"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
        
        return {
            "simulation_dir": sim_dir,
            "scripts_dir": scripts_dir,
            "config_file": config_path,
            "commands": {
                "twitter": f"python {scripts_dir}/run_twitter_simulation.py --config {config_path}",
                "reddit": f"python {scripts_dir}/run_reddit_simulation.py --config {config_path}",
                "parallel": f"python {scripts_dir}/run_parallel_simulation.py --config {config_path}",
            },
            "instructions": (
                f"1. 激活conda环境: conda activate MiroFish\n"
                f"2. 运行模拟 (脚本位于 {scripts_dir}):\n"
                f"   - 单独运行Twitter: python {scripts_dir}/run_twitter_simulation.py --config {config_path}\n"
                f"   - 单独运行Reddit: python {scripts_dir}/run_reddit_simulation.py --config {config_path}\n"
                f"   - 并行运行双平台: python {scripts_dir}/run_parallel_simulation.py --config {config_path}"
            )
        }
