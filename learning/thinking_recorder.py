"""
AI思考过程记录工具 - Window 9核心组件
记录所有AI思考过程，生成可复用的学习资料
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pickle
from uuid import uuid4


class ThinkingRecorder:
    """记录所有AI思考过程，生成学习资料"""
    
    def __init__(self, base_path: str = "learning_data"):
        """
        初始化思考记录器
        
        Args:
            base_path: 学习数据存储基础路径
        """
        self.base_path = Path(base_path)
        self._init_directories()
        
    def _init_directories(self):
        """初始化存储目录结构"""
        directories = [
            self.base_path / "thinking" / "json",
            self.base_path / "thinking" / "markdown", 
            self.base_path / "thinking" / "training",
            self.base_path / "decisions",
            self.base_path / "signals",
            self.base_path / "patterns",
            self.base_path / "weights"
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            
    def record_thinking_process(self, decision_id: str, thinking_chain: List[Dict]) -> Dict:
        """
        记录完整的10步思考链
        
        Args:
            decision_id: 决策ID
            thinking_chain: 思考链列表
            
        Returns:
            记录的完整信息
        """
        record = {
            "decision_id": decision_id,
            "timestamp": datetime.now().isoformat(),
            "thinking_steps": self._format_thinking_steps(thinking_chain),
            "final_decision": thinking_chain[-1] if thinking_chain else None,
            "confidence": self._calculate_confidence(thinking_chain),
            "metadata": {
                "ai_model": "Claude Opus 4.1",
                "version": "1.0",
                "market_condition": self._analyze_market_condition(thinking_chain)
            }
        }
        
        # 保存为多种格式
        self.save_as_learning_material(record)
        
        return record
        
    def _format_thinking_steps(self, thinking_chain: List[Dict]) -> List[Dict]:
        """格式化思考步骤"""
        formatted_steps = []
        
        step_names = [
            "数据收集",
            "异常识别", 
            "模式匹配",
            "风险评估",
            "机会识别",
            "策略选择",
            "仓位计算",
            "时机判断",
            "执行计划",
            "决策输出"
        ]
        
        for i, (step_name, content) in enumerate(zip(step_names, thinking_chain), 1):
            formatted_step = {
                "step": i,
                "name": step_name,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "data_sources": self._extract_data_sources(content),
                "patterns_found": self._extract_patterns(content) if i == 3 else [],
                "risks_identified": self._extract_risks(content) if i == 4 else [],
                "opportunities": self._extract_opportunities(content) if i == 5 else []
            }
            formatted_steps.append(formatted_step)
            
        return formatted_steps
        
    def _extract_data_sources(self, content: Dict) -> List[str]:
        """提取数据源"""
        sources = []
        if isinstance(content, dict):
            if "sources" in content:
                sources = content["sources"]
            elif "data_from" in content:
                sources = content["data_from"]
            else:
                # 从内容中推断数据源
                text = str(content)
                if "Window2" in text or "exchange" in text.lower():
                    sources.append("Window2_Exchange")
                if "Window3" in text or "collector" in text.lower():
                    sources.append("Window3_Collector")
                if "Window4" in text or "analysis" in text.lower():
                    sources.append("Window4_Analysis")
                    
        return sources
        
    def _extract_patterns(self, content: Dict) -> List[Dict]:
        """提取发现的模式"""
        patterns = []
        if isinstance(content, dict) and "patterns" in content:
            patterns = content["patterns"]
        return patterns
        
    def _extract_risks(self, content: Dict) -> List[Dict]:
        """提取识别的风险"""
        risks = []
        if isinstance(content, dict) and "risks" in content:
            risks = content["risks"]
        return risks
        
    def _extract_opportunities(self, content: Dict) -> List[Dict]:
        """提取机会"""
        opportunities = []
        if isinstance(content, dict) and "opportunities" in content:
            opportunities = content["opportunities"]
        return opportunities
        
    def _calculate_confidence(self, thinking_chain: List[Dict]) -> float:
        """计算决策信心度"""
        if not thinking_chain:
            return 0.0
            
        # 基于思考链的完整性和一致性计算信心度
        base_confidence = 0.5
        
        # 完整性加分
        if len(thinking_chain) >= 10:
            base_confidence += 0.2
            
        # 检查是否有风险评估
        has_risk_assessment = any("risk" in str(step).lower() for step in thinking_chain)
        if has_risk_assessment:
            base_confidence += 0.15
            
        # 检查是否有数据支撑
        has_data_support = any("data" in str(step).lower() for step in thinking_chain)
        if has_data_support:
            base_confidence += 0.15
            
        return min(base_confidence, 1.0)
        
    def _analyze_market_condition(self, thinking_chain: List[Dict]) -> str:
        """分析市场状况"""
        # 从思考链中提取市场状况
        conditions = []
        
        for step in thinking_chain:
            step_str = str(step).lower()
            if "volatile" in step_str or "波动" in step_str:
                conditions.append("volatile")
            if "trend" in step_str or "趋势" in step_str:
                conditions.append("trending")
            if "sideways" in step_str or "横盘" in step_str:
                conditions.append("sideways")
                
        if "volatile" in conditions:
            return "high_volatility"
        elif "trending" in conditions:
            return "trending"
        elif "sideways" in conditions:
            return "sideways"
        else:
            return "normal"
            
    def save_as_learning_material(self, record: Dict):
        """
        生成固定格式的学习资料
        
        Args:
            record: 记录数据
        """
        decision_id = record['decision_id']
        
        # 保存为JSON格式（程序读取）
        json_path = self.base_path / "thinking" / "json" / f"{decision_id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
            
        # 保存为Markdown格式（人类可读）
        md_path = self.base_path / "thinking" / "markdown" / f"{decision_id}.md"
        self._save_as_markdown(record, md_path)
        
        # 保存为训练数据格式（为未来模型准备）
        training_path = self.base_path / "thinking" / "training" / f"{decision_id}.pkl"
        with open(training_path, 'wb') as f:
            pickle.dump(record, f)
            
    def _save_as_markdown(self, record: Dict, path: Path):
        """保存为Markdown格式"""
        md_content = f"""# AI思考过程记录

## 决策ID: {record['decision_id']}
**时间**: {record['timestamp']}  
**信心度**: {record['confidence']:.2%}  
**市场状况**: {record['metadata']['market_condition']}  

## 思考步骤

"""
        
        for step in record['thinking_steps']:
            md_content += f"""### 步骤 {step['step']}: {step['name']}

**内容**: 
```json
{json.dumps(step['content'], ensure_ascii=False, indent=2)}
```

"""
            if step.get('data_sources'):
                md_content += f"**数据源**: {', '.join(step['data_sources'])}\n\n"
                
            if step.get('patterns_found'):
                md_content += f"**发现的模式**: \n"
                for pattern in step['patterns_found']:
                    md_content += f"- {pattern}\n"
                md_content += "\n"
                
            if step.get('risks_identified'):
                md_content += f"**识别的风险**: \n"
                for risk in step['risks_identified']:
                    md_content += f"- {risk}\n"
                md_content += "\n"
                
            if step.get('opportunities'):
                md_content += f"**机会**: \n"
                for opp in step['opportunities']:
                    md_content += f"- {opp}\n"
                md_content += "\n"
                
        md_content += f"""## 最终决策

```json
{json.dumps(record['final_decision'], ensure_ascii=False, indent=2)}
```

---
*由Window 9学习系统自动生成*
"""
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
    def get_recent_thoughts(self, limit: int = 10) -> List[Dict]:
        """获取最近的思考记录"""
        json_dir = self.base_path / "thinking" / "json"
        
        # 获取所有JSON文件
        json_files = sorted(json_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        records = []
        for json_file in json_files[:limit]:
            with open(json_file, 'r', encoding='utf-8') as f:
                records.append(json.load(f))
                
        return records
        
    def analyze_thinking_patterns(self) -> Dict:
        """分析思考模式"""
        records = self.get_recent_thoughts(100)
        
        analysis = {
            "total_records": len(records),
            "average_confidence": 0,
            "market_conditions": {},
            "common_patterns": [],
            "success_indicators": []
        }
        
        if not records:
            return analysis
            
        # 计算平均信心度
        total_confidence = sum(r.get('confidence', 0) for r in records)
        analysis['average_confidence'] = total_confidence / len(records)
        
        # 统计市场状况
        for record in records:
            condition = record.get('metadata', {}).get('market_condition', 'unknown')
            analysis['market_conditions'][condition] = analysis['market_conditions'].get(condition, 0) + 1
            
        return analysis


if __name__ == "__main__":
    # 测试代码
    recorder = ThinkingRecorder()
    
    # 模拟思考链
    test_thinking_chain = [
        {"step": "collect", "data": "市场数据收集", "sources": ["Window2", "Window3"]},
        {"step": "identify", "anomalies": ["价格异常", "成交量激增"]},
        {"step": "match", "patterns": ["突破形态", "量价背离"]},
        {"step": "assess", "risks": ["高波动风险", "流动性风险"]},
        {"step": "find", "opportunities": ["做多机会", "套利机会"]},
        {"step": "select", "strategy": "趋势跟踪"},
        {"step": "calculate", "position": "10% 仓位"},
        {"step": "timing", "entry": "立即进场"},
        {"step": "plan", "execution": "限价单入场"},
        {"step": "decide", "action": "BUY", "symbol": "BTC/USDT", "confidence": 0.85}
    ]
    
    # 记录思考过程
    decision_id = str(uuid4())
    result = recorder.record_thinking_process(decision_id, test_thinking_chain)
    
    print(f"✅ 思考过程已记录")
    print(f"决策ID: {result['decision_id']}")
    print(f"信心度: {result['confidence']:.2%}")
    print(f"市场状况: {result['metadata']['market_condition']}")
    
    # 分析思考模式
    analysis = recorder.analyze_thinking_patterns()
    print(f"\n📊 思考模式分析:")
    print(f"总记录数: {analysis['total_records']}")
    print(f"平均信心度: {analysis['average_confidence']:.2%}")