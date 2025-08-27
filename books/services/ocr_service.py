# services/ocr_service.py
import cv2
import numpy as np
from PIL import Image
import easyocr
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OCRService:
    """OCR服务类"""
    
    def __init__(self):
        # 初始化EasyOCR，支持中文和英文
        self.reader = easyocr.Reader(['ch_sim', 'en'])
    
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        处理图片，返回OCR识别结果
        
        Args:
            image_path: 图片路径
            
        Returns:
            List[Dict]: 包含文本区域信息的列表
        """
        try:
            # 预处理图片
            processed_image = self._preprocess_image(image_path)
            
            # OCR识别
            results = self.reader.readtext(processed_image)
            
            # 处理识别结果
            text_regions = []
            for i, (bbox, text, confidence) in enumerate(results):
                # 计算边界框坐标
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                x = int(min(x_coords))
                y = int(min(y_coords))
                width = int(max(x_coords) - min(x_coords))
                height = int(max(y_coords) - min(y_coords))
                
                text_region = {
                    'region_id': f'region_{i}',
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'text': text.strip(),
                    'confidence': float(confidence),
                    'order_index': i
                }
                text_regions.append(text_region)
            
            # 按照阅读顺序排序（从上到下，从左到右）
            text_regions = self._sort_text_regions(text_regions)
            
            return text_regions
            
        except Exception as e:
            logger.error(f"OCR处理失败: {str(e)}")
            raise
    
    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        图片预处理
        
        Args:
            image_path: 图片路径
            
        Returns:
            np.ndarray: 预处理后的图片
        """
        # 读取图片
        image = cv2.imread(image_path)
        
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 降噪
        denoised = cv2.medianBlur(gray, 3)
        
        # 二值化
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 形态学处理，去除噪点
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
    def _sort_text_regions(self, regions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按照阅读顺序排序文本区域
        
        Args:
            regions: 文本区域列表
            
        Returns:
            List[Dict]: 排序后的文本区域列表
        """
        # 按照Y坐标分组（处理同一行的文本）
        lines = []
        current_line = []
        current_y = None
        tolerance = 20  # Y坐标容差
        
        # 先按Y坐标排序
        regions_sorted_by_y = sorted(regions, key=lambda r: r['y'])
        
        for region in regions_sorted_by_y:
            if current_y is None or abs(region['y'] - current_y) <= tolerance:
                # 同一行
                current_line.append(region)
                current_y = region['y'] if current_y is None else current_y
            else:
                # 新的一行
                if current_line:
                    # 当前行按X坐标排序
                    current_line.sort(key=lambda r: r['x'])
                    lines.append(current_line)
                current_line = [region]
                current_y = region['y']
        
        # 处理最后一行
        if current_line:
            current_line.sort(key=lambda r: r['x'])
            lines.append(current_line)
        
        # 重新分配order_index
        sorted_regions = []
        for line in lines:
            sorted_regions.extend(line)
        
        for i, region in enumerate(sorted_regions):
            region['order_index'] = i
        
        return sorted_regions

