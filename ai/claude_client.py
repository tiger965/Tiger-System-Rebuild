"""
Claude API客户端 - 智能决策的执行引擎
负责管理与Claude Opus 4.1的所有交互
包含请求管理、重试机制、成本控制等核心功能
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import hashlib

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import aiohttp
from dotenv import load_dotenv

from prompts.prompt_templates import PromptType, PromptTemplates

load_dotenv()
logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """请求优先级"""
    URGENT = 1     # 紧急（黑天鹅事件）
    HIGH = 2       # 高（Level 3触发）
    NORMAL = 3     # 正常（Level 2触发）
    LOW = 4        # 低（常规分析）


@dataclass
class APIRequest:
    """API请求数据结构"""
    request_id: str
    prompt: str
    prompt_type: PromptType
    priority: RequestPriority
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 30
    callback: Optional[Any] = None


@dataclass
class APIResponse:
    """API响应数据结构"""
    request_id: str
    content: str
    usage: Dict[str, int]
    cost: float
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None


class CostController:
    """成本控制器"""
    
    def __init__(self, daily_budget: float = 10.0):  # 更合理的日预算
        self.daily_budget = daily_budget
        self.hourly_budget = daily_budget / 24
        
        # 成本追踪
        self.daily_cost = 0.0
        self.hourly_cost = 0.0
        self.total_cost = 0.0
        
        # 时间追踪
        self.current_day = datetime.now().date()
        self.current_hour = datetime.now().hour
        
        # 成本历史
        self.cost_history = deque(maxlen=30*24)  # 30天历史
        
        # Claude Opus定价（按token）
        self.input_price_per_1k = 0.015   # $0.015 per 1K input tokens
        self.output_price_per_1k = 0.075  # $0.075 per 1K output tokens
    
    def calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算API调用成本"""
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        
        input_cost = (input_tokens / 1000) * self.input_price_per_1k
        output_cost = (output_tokens / 1000) * self.output_price_per_1k
        
        return input_cost + output_cost
    
    def can_make_request(self, priority: RequestPriority) -> Tuple[bool, str]:
        """检查是否可以发起请求"""
        self._update_time_buckets()
        
        # 紧急请求总是允许
        if priority == RequestPriority.URGENT:
            return True, "Urgent request bypasses budget"
        
        # 检查每日预算
        if self.daily_cost >= self.daily_budget:
            return False, f"Daily budget exceeded: ${self.daily_cost:.2f}/${self.daily_budget:.2f}"
        
        # 检查小时预算（软限制）
        if self.hourly_cost >= self.hourly_budget * 2:  # 允许2倍超支
            if priority != RequestPriority.HIGH:
                return False, f"Hourly budget exceeded: ${self.hourly_cost:.2f}"
        
        return True, "OK"
    
    def record_cost(self, cost: float, priority: RequestPriority):
        """记录成本"""
        self._update_time_buckets()
        
        self.daily_cost += cost
        self.hourly_cost += cost
        self.total_cost += cost
        
        # 记录历史
        self.cost_history.append({
            'timestamp': datetime.now(),
            'cost': cost,
            'priority': priority.value,
            'daily_total': self.daily_cost,
            'hourly_total': self.hourly_cost
        })
        
        # 日志记录
        logger.info(f"API cost: ${cost:.4f} | Daily: ${self.daily_cost:.2f}/${self.daily_budget:.2f}")
    
    def _update_time_buckets(self):
        """更新时间桶"""
        now = datetime.now()
        
        # 检查是否新的一天
        if now.date() != self.current_day:
            self.daily_cost = 0.0
            self.current_day = now.date()
            logger.info(f"New day, resetting daily budget")
        
        # 检查是否新的小时
        if now.hour != self.current_hour:
            self.hourly_cost = 0.0
            self.current_hour = now.hour
    
    def get_stats(self) -> Dict:
        """获取成本统计"""
        return {
            'daily_cost': self.daily_cost,
            'daily_budget': self.daily_budget,
            'daily_remaining': max(0, self.daily_budget - self.daily_cost),
            'hourly_cost': self.hourly_cost,
            'hourly_budget': self.hourly_budget,
            'total_cost': self.total_cost,
            'cost_per_request': self.total_cost / len(self.cost_history) if self.cost_history else 0
        }


class RequestQueue:
    """请求队列管理器"""
    
    def __init__(self, max_size: int = 1000):
        self.queues = {
            RequestPriority.URGENT: deque(),
            RequestPriority.HIGH: deque(),
            RequestPriority.NORMAL: deque(),
            RequestPriority.LOW: deque()
        }
        self.max_size = max_size
        self.total_size = 0
        self.processing = False
    
    def add_request(self, request: APIRequest) -> bool:
        """添加请求到队列"""
        if self.total_size >= self.max_size:
            logger.warning(f"Queue full, rejecting request {request.request_id}")
            return False
        
        # 检查重复请求
        if self._is_duplicate(request):
            logger.debug(f"Duplicate request detected: {request.request_id}")
            return False
        
        self.queues[request.priority].append(request)
        self.total_size += 1
        
        logger.debug(f"Request {request.request_id} added to {request.priority.name} queue")
        return True
    
    def get_next_request(self) -> Optional[APIRequest]:
        """获取下一个请求（按优先级）"""
        for priority in RequestPriority:
            queue = self.queues[priority]
            if queue:
                request = queue.popleft()
                self.total_size -= 1
                return request
        return None
    
    def _is_duplicate(self, request: APIRequest) -> bool:
        """检查是否重复请求"""
        # 生成请求指纹
        fingerprint = hashlib.md5(
            f"{request.prompt_type.value}:{request.context.get('symbol', '')}".encode()
        ).hexdigest()
        
        # 检查最近的请求
        cutoff = datetime.now() - timedelta(minutes=5)
        for priority_queue in self.queues.values():
            for existing in priority_queue:
                if existing.timestamp < cutoff:
                    continue
                existing_fp = hashlib.md5(
                    f"{existing.prompt_type.value}:{existing.context.get('symbol', '')}".encode()
                ).hexdigest()
                if fingerprint == existing_fp:
                    return True
        return False
    
    def clear_old_requests(self):
        """清理过期请求"""
        cutoff = datetime.now() - timedelta(minutes=30)
        
        for priority, queue in self.queues.items():
            old_len = len(queue)
            # 过滤掉旧请求
            self.queues[priority] = deque(
                [r for r in queue if r.timestamp > cutoff]
            )
            removed = old_len - len(self.queues[priority])
            if removed > 0:
                self.total_size -= removed
                logger.info(f"Cleared {removed} old requests from {priority.name} queue")
    
    def get_stats(self) -> Dict:
        """获取队列统计"""
        return {
            'total_size': self.total_size,
            'urgent_queue': len(self.queues[RequestPriority.URGENT]),
            'high_queue': len(self.queues[RequestPriority.HIGH]),
            'normal_queue': len(self.queues[RequestPriority.NORMAL]),
            'low_queue': len(self.queues[RequestPriority.LOW]),
            'capacity': f"{self.total_size}/{self.max_size}"
        }


class ClaudeClient:
    """Claude API客户端主类"""
    
    def __init__(self, api_key: Optional[str] = None):
        # API配置
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("Claude API key not provided")
        
        # 初始化客户端
        self.client = Anthropic(api_key=self.api_key)
        self.async_client = AsyncAnthropic(api_key=self.api_key)
        
        # 模型配置
        self.model = "claude-opus-4-1-20250805"
        self.max_tokens = 4000
        self.temperature = 0.3  # 降低随机性，提高一致性
        
        # 组件初始化
        self.cost_controller = CostController()
        self.request_queue = RequestQueue()
        self.prompt_templates = PromptTemplates()
        
        # 性能统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 响应缓存
        self.response_cache = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        # 启动后台任务
        self.background_tasks = []
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """启动后台任务"""
        # 队列处理任务
        asyncio.create_task(self._process_queue_worker())
        # 缓存清理任务
        asyncio.create_task(self._cache_cleanup_worker())
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _make_api_call(self, prompt: str, timeout: int = 30) -> Message:
        """实际的API调用（带重试）"""
        try:
            message = await asyncio.wait_for(
                self.async_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                ),
                timeout=timeout
            )
            return message
        except asyncio.TimeoutError:
            logger.error(f"API call timeout after {timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            raise
    
    async def analyze(self,
                      prompt_type: PromptType,
                      context: Dict[str, Any],
                      priority: RequestPriority = RequestPriority.NORMAL,
                      use_cache: bool = True) -> APIResponse:
        """
        执行AI分析
        
        Args:
            prompt_type: 提示词类型
            context: 上下文数据
            priority: 请求优先级
            use_cache: 是否使用缓存
            
        Returns:
            API响应
        """
        # 生成请求ID
        request_id = f"{prompt_type.value}_{context.get('symbol', 'unknown')}_{int(time.time())}"
        
        # 检查缓存
        if use_cache:
            cached = self._check_cache(request_id)
            if cached:
                self.stats['cache_hits'] += 1
                logger.debug(f"Cache hit for {request_id}")
                return cached
        
        self.stats['cache_misses'] += 1
        
        # 构建提示词
        prompt = self.prompt_templates.build_prompt(prompt_type, context)
        
        # 创建请求
        request = APIRequest(
            request_id=request_id,
            prompt=prompt,
            prompt_type=prompt_type,
            priority=priority,
            context=context
        )
        
        # 检查成本限制
        can_request, reason = self.cost_controller.can_make_request(priority)
        if not can_request:
            logger.warning(f"Request blocked: {reason}")
            return APIResponse(
                request_id=request_id,
                content="",
                usage={},
                cost=0,
                response_time=0,
                success=False,
                error=reason
            )
        
        # 高优先级直接处理，低优先级加入队列
        if priority in [RequestPriority.URGENT, RequestPriority.HIGH]:
            return await self._process_request(request)
        else:
            # 加入队列
            if self.request_queue.add_request(request):
                logger.info(f"Request {request_id} queued")
                # 返回队列确认
                return APIResponse(
                    request_id=request_id,
                    content="Request queued for processing",
                    usage={},
                    cost=0,
                    response_time=0,
                    success=True,
                    error=None
                )
            else:
                return APIResponse(
                    request_id=request_id,
                    content="",
                    usage={},
                    cost=0,
                    response_time=0,
                    success=False,
                    error="Queue full"
                )
    
    async def _process_request(self, request: APIRequest) -> APIResponse:
        """处理单个请求"""
        start_time = time.time()
        
        try:
            # 调用API
            message = await self._make_api_call(request.prompt, request.timeout)
            
            # 提取响应
            content = message.content[0].text if message.content else ""
            usage = {
                'input_tokens': message.usage.input_tokens,
                'output_tokens': message.usage.output_tokens,
                'total_tokens': message.usage.input_tokens + message.usage.output_tokens
            }
            
            # 计算成本
            cost = self.cost_controller.calculate_cost(usage)
            self.cost_controller.record_cost(cost, request.priority)
            
            # 记录响应时间
            response_time = time.time() - start_time
            
            # 创建响应
            response = APIResponse(
                request_id=request.request_id,
                content=content,
                usage=usage,
                cost=cost,
                response_time=response_time,
                success=True,
                error=None
            )
            
            # 缓存响应
            self._cache_response(request.request_id, response)
            
            # 更新统计
            self.stats['total_requests'] += 1
            self.stats['successful_requests'] += 1
            self.stats['total_response_time'] += response_time
            
            logger.info(f"Request {request.request_id} completed in {response_time:.2f}s, cost: ${cost:.4f}")
            
            return response
            
        except Exception as e:
            # 记录失败
            self.stats['total_requests'] += 1
            self.stats['failed_requests'] += 1
            
            logger.error(f"Request {request.request_id} failed: {str(e)}")
            
            return APIResponse(
                request_id=request.request_id,
                content="",
                usage={},
                cost=0,
                response_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    async def _process_queue_worker(self):
        """后台队列处理工作器"""
        while True:
            try:
                # 清理旧请求
                self.request_queue.clear_old_requests()
                
                # 获取下一个请求
                request = self.request_queue.get_next_request()
                if request:
                    # 检查成本
                    can_request, reason = self.cost_controller.can_make_request(request.priority)
                    if can_request:
                        response = await self._process_request(request)
                        
                        # 如果有回调，执行回调
                        if request.callback:
                            await request.callback(response)
                    else:
                        logger.debug(f"Delaying request due to: {reason}")
                        # 重新加入队列
                        self.request_queue.add_request(request)
                
                # 避免过于频繁
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Queue worker error: {str(e)}")
                await asyncio.sleep(5)
    
    def _check_cache(self, request_id: str) -> Optional[APIResponse]:
        """检查缓存"""
        if request_id in self.response_cache:
            cached_item = self.response_cache[request_id]
            # 检查是否过期
            if datetime.now() - cached_item['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cached_item['response']
            else:
                # 过期，删除
                del self.response_cache[request_id]
        return None
    
    def _cache_response(self, request_id: str, response: APIResponse):
        """缓存响应"""
        self.response_cache[request_id] = {
            'response': response,
            'timestamp': datetime.now()
        }
    
    async def _cache_cleanup_worker(self):
        """缓存清理工作器"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次
                
                now = datetime.now()
                expired_keys = []
                
                for key, item in self.response_cache.items():
                    if now - item['timestamp'] > timedelta(seconds=self.cache_ttl):
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.response_cache[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
                    
            except Exception as e:
                logger.error(f"Cache cleanup error: {str(e)}")
    
    def get_stats(self) -> Dict:
        """获取客户端统计信息"""
        avg_response_time = (
            self.stats['total_response_time'] / self.stats['successful_requests']
            if self.stats['successful_requests'] > 0 else 0
        )
        
        return {
            **self.stats,
            'avg_response_time': avg_response_time,
            'success_rate': (
                self.stats['successful_requests'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            ),
            'cache_hit_rate': (
                self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
                if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0 else 0
            ),
            **self.cost_controller.get_stats(),
            **self.request_queue.get_stats()
        }
    
    async def batch_analyze(self,
                           requests: List[Tuple[PromptType, Dict[str, Any]]],
                           priority: RequestPriority = RequestPriority.NORMAL) -> List[APIResponse]:
        """
        批量分析（相似请求合并）
        
        Args:
            requests: [(提示词类型, 上下文)]列表
            priority: 优先级
            
        Returns:
            响应列表
        """
        # 对请求进行分组（按币种）
        grouped = {}
        for prompt_type, context in requests:
            symbol = context.get('symbol', 'unknown')
            if symbol not in grouped:
                grouped[symbol] = []
            grouped[symbol].append((prompt_type, context))
        
        responses = []
        
        # 并发处理每组
        tasks = []
        for symbol, group in grouped.items():
            # 如果同一币种有多个请求，可以合并上下文
            if len(group) > 1:
                # 合并上下文
                merged_context = {}
                for _, ctx in group:
                    merged_context.update(ctx)
                
                # 使用综合分析
                task = self.analyze(
                    PromptType.BASIC_ANALYSIS,
                    merged_context,
                    priority
                )
                tasks.append(task)
            else:
                # 单个请求直接处理
                prompt_type, context = group[0]
                task = self.analyze(prompt_type, context, priority)
                tasks.append(task)
        
        # 等待所有任务完成
        responses = await asyncio.gather(*tasks)
        
        return responses