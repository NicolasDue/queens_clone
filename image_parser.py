from PIL import Image
import numpy as np
from loguru import logger
from typing import List, Tuple, Dict, Optional

ColorMatrix = List[List[str]]
Color = Tuple[int, int, int]
ColorMap = Dict[Color, str]

class ColorGridProcessor:
    def __init__(self, grid_size: int = 8, pixel_delta: int = None):
        self.grid_size: int = grid_size
        self.pixel_delta: int = pixel_delta
        self.image: Optional[Image.Image] = None
        self.color_to_letter: ColorMap = {}
        self.letter_counter: int = 0

    def load_image(self, image: Image.Image) -> None:
        self.image = image

    def get_dominant_color(self, x: int, y: int, size: int) -> Color:
        if self.image is None:
            raise ValueError("No image loaded")
        region = self.image.crop((x, y, x + size, y + size))
        colors = region.getcolors(size * size)
        return max(colors, key=lambda x: x[0])[1]

    def process_image(self) -> ColorMatrix:
        if self.image is None:
            raise ValueError("No image loaded")

        w, h = np.array(self.image.size)
        s_w, s_h = w // self.grid_size, h // self.grid_size
        
        if self.pixel_delta is None:
            self.pixel_delta = min(s_w, s_h) // 4

        color_matrix: ColorMatrix = []

        for i in range(self.grid_size):
            row: List[str] = []
            for j in range(self.grid_size):
                x = j * s_w + s_w // 2
                y = i * s_h + s_h // 2
                color = self.get_dominant_color(x - self.pixel_delta, y - self.pixel_delta, 2 * self.pixel_delta)
                
                if color not in self.color_to_letter:
                    self.color_to_letter[color] = chr(65 + self.letter_counter)
                    self.letter_counter += 1
                
                row.append(self.color_to_letter[color])
            color_matrix.append(row)

        return color_matrix

    def print_color_matrix(self, matrix: ColorMatrix) -> None:
        for row in matrix:
            print(row)

def read_grid_from_image(image: Image.Image, grid_size: int) -> ColorMatrix:
    processor = ColorGridProcessor(grid_size=grid_size)
    processor.load_image(image)
    color_matrix = processor.process_image()
    return color_matrix
