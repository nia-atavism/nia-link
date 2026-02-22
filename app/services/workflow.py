"""
Nia-Link Workflow Service v0.9
多頁面工作流 (Workflow Chain) - 支援多步驟連鎖動作
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional

from ..config import get_settings
from .scraper import ScraperService
from .executor import ExecutorService

logger = logging.getLogger("nia-link.workflow")


class WorkflowService:
    """
    多頁面工作流服務
    
    支援的步驟類型:
    - scrape: 爬取頁面內容
    - interact: 執行交互動作
    - wait: 等待指定時間
    - assert: 驗證頁面狀態
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.scraper = ScraperService()
        self.executor = ExecutorService(headless=self.settings.headless)
    
    async def execute(self, steps: List[Dict], context: Optional[Dict] = None) -> Dict:
        """
        執行多步驟工作流
        
        Args:
            steps: 步驟列表，每個步驟包含 type, url, actions 等
            context: 初始上下文（cookies, account_id 等）
            
        Returns:
            包含每步結果和總體狀態的字典
        """
        start_time = time.time()
        context = context or {}
        results = []
        overall_status = "success"
        
        for i, step in enumerate(steps):
            step_type = step.get("type", "scrape")
            step_url = step.get("url")
            step_name = step.get("name", f"Step {i + 1}")
            
            logger.info(f"Workflow step {i + 1}/{len(steps)}: {step_name} ({step_type})")
            
            step_result = {
                "step": i + 1,
                "name": step_name,
                "type": step_type,
                "status": "pending"
            }
            
            try:
                if step_type == "scrape":
                    result = await self.scraper.scrape(
                        url=step_url,
                        output_format=step.get("format", "markdown"),
                        mode=step.get("mode", "fast"),
                        timeout=step.get("timeout"),
                        extract_actions=step.get("extract_actions", True),
                        cookies=context.get("cookies"),
                        screenshot=step.get("screenshot", False)
                    )
                    step_result["status"] = "success"
                    step_result["title"] = result["data"].get("title")
                    step_result["token_savings"] = result["cost"].get("reduction_percent")
                    
                    # 將 actions 傳遞到下一步的 context
                    if result["data"].get("actions"):
                        context["last_actions"] = result["data"]["actions"]
                    
                elif step_type == "interact":
                    actions = step.get("actions", [])
                    result = await self.executor.interact(
                        url=step_url,
                        actions=actions,
                        account_id=context.get("account_id")
                    )
                    step_result["status"] = result.get("status", "error")
                    step_result["log"] = result.get("log", [])
                    step_result["js_results"] = result.get("js_results")
                    
                    if result.get("status") == "error":
                        step_result["error"] = result.get("message")
                        if not step.get("continue_on_error", False):
                            overall_status = "partial"
                            results.append(step_result)
                            break
                
                elif step_type == "wait":
                    ms = step.get("ms", 1000)
                    await asyncio.sleep(ms / 1000)
                    step_result["status"] = "success"
                    step_result["waited_ms"] = ms
                
                elif step_type == "assert":
                    condition = step.get("condition", "")
                    target = step.get("target", "")
                    last_step = results[-1] if results else {}
                    
                    if condition == "status_is":
                        actual = last_step.get("status", "")
                        passed = actual == target
                    elif condition == "title_contains":
                        actual = last_step.get("title", "")
                        passed = target.lower() in actual.lower() if actual else False
                    else:
                        passed = False
                    
                    step_result["status"] = "passed" if passed else "failed"
                    step_result["condition"] = condition
                    step_result["target"] = target
                    
                    if not passed and not step.get("continue_on_error", False):
                        overall_status = "failed"
                        results.append(step_result)
                        break
                
                else:
                    step_result["status"] = "skipped"
                    step_result["error"] = f"Unknown step type: {step_type}"
                    
            except Exception as e:
                logger.error(f"Workflow step {i + 1} failed: {e}")
                step_result["status"] = "error"
                step_result["error"] = str(e)
                
                if not step.get("continue_on_error", False):
                    overall_status = "failed"
                    results.append(step_result)
                    break
            
            results.append(step_result)
        
        total_time = round(time.time() - start_time, 3)
        
        return {
            "status": overall_status,
            "total_steps": len(steps),
            "completed_steps": len(results),
            "total_time": total_time,
            "results": results
        }
