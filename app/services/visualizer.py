"""
Nia-Link Visualization Service v0.1
視覺化軌跡 (Visual Trajectory) - 軌跡繪製、熱點分析、GIF 生成預留
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image, ImageDraw

logger = logging.getLogger("nia-link.visualizer")

class TrajectoryVisualizer:
    def __init__(self):
        self.point_radius = 4
        self.line_width = 2
        self.point_color = (0, 255, 255, 180)  # 青色 (Cyan) 半透明
        self.line_color = (255, 0, 255, 100)   # 品紅 (Magenta) 半透明
        self.click_color = (255, 255, 0, 255)  # 黃色 (Yellow) 不透明

    def draw_trajectory(self, screenshot_path: str, trajectory_data: List[Dict], output_path: Optional[str] = None) -> str:
        """
        在截圖上繪製滑鼠軌跡點與連線
        """
        try:
            img = Image.open(screenshot_path).convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            points = [(p['x'], p['y']) for p in trajectory_data]
            
            # 1. 繪製連線
            if len(points) > 1:
                draw.line(points, fill=self.line_color, width=self.line_width)

            # 2. 繪製路徑點
            for p in points:
                r = self.point_radius
                draw.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=self.point_color)

            # 3. 標記終點 (通常是點擊點)
            if points:
                last_p = points[-1]
                r = self.point_radius + 2
                draw.ellipse([last_p[0]-r, last_p[1]-r, last_p[0]+r, last_p[1]+r], outline=self.click_color, width=2)

            # 合併圖層
            combined = Image.alpha_composite(img, overlay).convert("RGB")
            
            if not output_path:
                p = Path(screenshot_path)
                output_path = str(p.parent / f"{p.stem}-viz{p.suffix}")
            
            combined.save(output_path)
            logger.info(f"Trajectory visualization saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to draw trajectory: {e}")
            return screenshot_path

    def draw_from_json(self, screenshot_path: str, json_path: str, output_path: Optional[str] = None) -> str:
        """
        從 JSON 檔案讀取軌跡數據並繪製
        """
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            return self.draw_trajectory(screenshot_path, data, output_path)
        except Exception as e:
            logger.error(f"Failed to read trajectory JSON: {e}")
            return screenshot_path
