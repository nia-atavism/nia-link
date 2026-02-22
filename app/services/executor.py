"""
Nia-Link Executor Service v0.8
突觸橋接 (Synaptic Bridge) - 擬人化交互、軌跡追蹤、JS 沙箱
"""

import asyncio
import base64
import json
import logging
import random
import numpy as np
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Page, Browser

from ..config import get_settings
from .proxy import ProxyPool
from .page_observer import PageObserver
from .visualizer import TrajectoryVisualizer

logger = logging.getLogger("nia-link.executor")


class ExecutorService:
    def __init__(self, headless: bool = True):
        self.settings = get_settings()
        self.headless = headless
        self.session_dir = self.settings.get_session_dir()
        self.temp_dir = self.settings.get_temp_dir()
        self.trajectory_log = []  # v0.7: 紀錄滑鼠軌跡點位

    def _get_session_path(self, account_id: str) -> str:
        return str(self.session_dir / f"{account_id}.json")

    def _calculate_bezier_path(self, start, end, steps=20):
        """
        計算貝茲曲線軌跡，模擬人類滑鼠移動
        """
        t = np.linspace(0, 1, steps).reshape(-1, 1)
        # 隨機偏移控制點
        offset_x = random.uniform(-150, 150)
        offset_y = random.uniform(-150, 150)
        control = np.array([
            (start[0] + end[0]) / 2 + offset_x,
            (start[1] + end[1]) / 2 + offset_y
        ])
        
        start_pt = np.array(start)
        end_pt = np.array(end)
        
        path = (1-t)**2 * start_pt + 2*(1-t)*t * control + t**2 * end_pt
        return path.tolist()

    async def _human_click(self, page: Page, selector: str, timeout: int = 5000):
        """
        模擬人類移動滑鼠並點擊
        """
        element = await page.wait_for_selector(selector, timeout=timeout)
        box = await element.bounding_box()
        if not box:
            raise Exception(f"Element {selector} has no bounding box")

        target_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
        target_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
        
        # 取得目前滑鼠位置（模擬從中心或上次位置出發）
        start_x = self.trajectory_log[-1]['x'] if self.trajectory_log else 640
        start_y = self.trajectory_log[-1]['y'] if self.trajectory_log else 360
        
        path = self._calculate_bezier_path((start_x, start_y), (target_x, target_y), steps=random.randint(15, 30))
        
        path_array = np.array(path)
        for x, y in path_array:
            # v0.7: 紀錄軌跡雲點位
            self.trajectory_log.append({"x": round(float(x), 1), "y": round(float(y), 1), "ts": asyncio.get_event_loop().time()})
            await page.mouse.move(float(x), float(y))
            await asyncio.sleep(random.uniform(0.005, 0.012))
        
        await page.mouse.click(target_x, target_y, delay=random.uniform(50, 150))

    async def _human_type(self, page: Page, selector: str, text: str):
        """
        模擬人類打字，帶有隨機延遲（Jitter）
        """
        await page.focus(selector)
        for char in text:
            await page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.04, 0.18))

    async def _safe_evaluate(self, page: Page, script: str, timeout_ms: int = 5000) -> dict:
        """
        v0.8: 安全執行 JavaScript，帶有逾時保護
        """
        try:
            result = await asyncio.wait_for(
                page.evaluate(script),
                timeout=timeout_ms / 1000
            )
            return {"status": "success", "result": result}
        except asyncio.TimeoutError:
            return {"status": "error", "error": f"JS execution timed out ({timeout_ms}ms)"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def interact(self, url: str, actions: List[Dict], account_id: Optional[str] = None) -> Dict:
        """
        執行一系列交互動作，支援 v0.7 突觸橋接（軌跡追蹤）
        """
        self.trajectory_log = []  # 重設軌跡
        async with async_playwright() as p:
            # 動態選擇瀏覽器引擎
            browser_type_name = self.settings.browser_type
            browser_engine = getattr(p, browser_type_name, p.chromium)
            
            # Proxy 支援 - 使用代理池
            launch_opts = {"headless": self.headless}
            proxy_pool = ProxyPool()
            proxy_config = proxy_pool.get_playwright_proxy()
            if proxy_config:
                launch_opts["proxy"] = proxy_config
            
            browser = await browser_engine.launch(**launch_opts)
            
            context_options = {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "viewport": {"width": 1280, "height": 720}
            }
            if account_id:
                session_path = self._get_session_path(account_id)
                import os
                if os.path.exists(session_path):
                    context_options["storage_state"] = session_path
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            results = []
            js_results = []  # v0.8: JS 執行結果
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # v0.9: Capture page state BEFORE interactions
                observer = PageObserver()
                before_state = await observer.capture_state(page)
                after_state = {"console_errors": []}
                observer.setup_console_listener(page, after_state)

                for action in actions:
                    act_type = action.get("type")
                    selector = action.get("selector")
                    label = action.get("label")
                    
                    try:
                        if act_type == "fill":
                            await self._human_type(page, selector, action.get("text", ""))
                            results.append(f"Synaptic-typed into {selector}")
                        elif act_type == "click":
                            try:
                                await self._human_click(page, selector)
                                results.append(f"Synaptic-clicked {selector}")
                            except Exception:
                                if label:
                                    await page.click(f"text='{label}'")
                                    results.append(f"Fallback clicked: {label}")
                                else:
                                    raise
                        elif act_type == "upload":
                            await page.set_input_files(selector, action.get("files", []))
                            results.append(f"Uploaded to {selector}")
                        elif act_type == "wait":
                            ms = action.get("ms", 1000)
                            await page.wait_for_timeout(ms)
                            results.append(f"Paused for {ms}ms")
                        elif act_type == "evaluate":
                            # v0.8: JS 沙箱執行
                            script = action.get("script", "")
                            timeout_ms = action.get("timeout", 5000)
                            js_result = await self._safe_evaluate(page, script, timeout_ms)
                            js_results.append(js_result)
                            results.append(f"JS evaluated: {js_result['status']}")
                        elif act_type == "select":
                            # v0.8: 下拉選單支援
                            value = action.get("value", "")
                            await page.select_option(selector, value)
                            results.append(f"Selected '{value}' in {selector}")
                        elif act_type == "scroll":
                            # v0.8: 捲動支援
                            direction = action.get("direction", "down")
                            amount = action.get("amount", 500)
                            if direction == "down":
                                await page.evaluate(f"window.scrollBy(0, {amount})")
                            elif direction == "up":
                                await page.evaluate(f"window.scrollBy(0, -{amount})")
                            results.append(f"Scrolled {direction} {amount}px")
                        elif act_type == "auto_fill":
                            # v0.8: 智慧填表
                            field_mapping = action.get("field_mapping", {})
                            filled_count = 0
                            for field_selector, field_value in field_mapping.items():
                                try:
                                    el = await page.query_selector(field_selector)
                                    if el:
                                        tag = await el.evaluate("el => el.tagName.toLowerCase()")
                                        input_type = await el.evaluate("el => el.type || ''")
                                        if tag == "select":
                                            await page.select_option(field_selector, field_value)
                                        elif tag == "input" and input_type in ("checkbox", "radio"):
                                            if field_value:
                                                await el.check()
                                            else:
                                                await el.uncheck()
                                        else:
                                            await self._human_type(page, field_selector, str(field_value))
                                        filled_count += 1
                                except Exception as fill_err:
                                    results.append(f"auto_fill skip {field_selector}: {fill_err}")
                            results.append(f"Auto-filled {filled_count}/{len(field_mapping)} fields")
                    except Exception as e:
                        results.append(f"Error {act_type} on {selector}: {str(e)}")
                
                if account_id:
                    await context.storage_state(path=self._get_session_path(account_id))
                    results.append(f"Synaptic link maintained for {account_id}")

                import time as _time
                ts = int(_time.time())
                screenshot_path = str(self.temp_dir / f"nia-link-v08-{ts}.png")
                await page.screenshot(path=screenshot_path)
                
                # v0.8: 截圖 Base64
                screenshot_bytes = await page.screenshot(type="png")
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                
                # v0.7: 將軌跡數據保存為 JSON
                traj_path = str(self.temp_dir / f"trajectory-{ts}.json")
                with open(traj_path, "w") as f:
                    json.dump(self.trajectory_log, f)
                
                # v0.9: Capture page state AFTER interactions
                after_state_full = await observer.capture_state(page)
                after_state_full["console_errors"] = after_state.get("console_errors", [])
                page_state_diff = observer.compute_diff(before_state, after_state_full)

                # v0.9: 視覺化軌跡繪製
                visualizer = TrajectoryVisualizer()
                viz_screenshot_path = visualizer.draw_trajectory(screenshot_path, self.trajectory_log)

                return {
                    "status": "success",
                    "log": results,
                    "screenshot": screenshot_path,
                    "viz_screenshot": viz_screenshot_path,
                    "screenshot_base64": screenshot_b64,
                    "trajectory_cloud": traj_path,
                    "points_captured": len(self.trajectory_log),
                    "js_results": js_results if js_results else None,
                    "page_state": page_state_diff
                }
            except Exception as e:
                return {"status": "error", "message": str(e), "log": results}
            finally:
                await browser.close()
