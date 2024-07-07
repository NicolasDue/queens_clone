from flask import Flask, render_template, jsonify, request
import time
from PIL import Image
from io import BytesIO
from image_parser import read_grid_from_image
from loguru import logger

app = Flask(__name__)

# Initialize the grid data
def initialize_grid(grid_size):
    return [[{"state": 0} for _ in range(grid_size)] for _ in range(grid_size)]

# Global variables for grid and regions
regions = [
    ['A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C'],
    ['A', 'A', 'D', 'E', 'E', 'B', 'B', 'C', 'C'],
    ['A', 'A', 'D', 'D', 'E', 'E', 'B', 'C', 'C'],
    ['A', 'A', 'D', 'E', 'E', 'B', 'B', 'F', 'C'],
    ['A', 'A', 'A', 'A', 'B', 'B', 'F', 'F', 'F'],
    ['A', 'G', 'A', 'A', 'A', 'B', 'F', 'H', 'F'],
    ['G', 'G', 'G', 'A', 'A', 'B', 'H', 'H', 'H'],
    ['G', 'I', 'G', 'B', 'B', 'B', 'B', 'B', 'B'],
    ['I', 'I', 'I', 'B', 'B', 'B', 'B', 'B', 'B']
]



def create_grid_from_click_grid(click_grid):
    """
    - 1s in the click grid are converted to 1s in the grid
    - 2s in the click grid are converted to 2s in the grid
    - Cells around a 2 are in the click grid converted to 1s in the grid
    - Cells in the same row and the same column as a 2 in the click grid are converted to 1s in the grid
    """
    grid = initialize_grid(len(click_grid))
    for i in range(len(click_grid)):
        for j in range(len(click_grid)):
            if click_grid[i][j]['state'] == 1:
                grid[i][j]['state'] = 1
            elif click_grid[i][j]['state'] == 2:
                # Rows and columns
                for k in range(len(click_grid)):
                    if click_grid[i][k]['state'] == 0:
                        grid[i][k]['state'] = 1
                    if click_grid[k][j]['state'] == 0:
                        grid[k][j]['state'] = 1
                # Cells around the cell
                # (i-1, j-1), (i-1, j), (i-1, j+1), (i, j-1), (i, j+1), (i+1, j-1), (i+1, j), (i+1, j+1)
                for x in range(i-1, i+2):
                    for y in range(j-1, j+2):
                        if 0 <= x < len(click_grid) and 0 <= y < len(click_grid):
                            if click_grid[x][y]['state'] == 0:
                                grid[x][y]['state'] = 1
                grid[i][j]['state'] = 2
    return grid

"""
Grid contains the states that are going to be displayed on the frontend.
Click grid contains the states of the cells that are clicked by the user.
We can build the grid by combining the regions and click grid.
This allows to remove cross marks when a star is removed.
"""
click_grid = initialize_grid(len(regions))
grid = create_grid_from_click_grid(click_grid)

region_colors = {
    'A': '#FFCDD2',
    'B': '#BBDEFB',
    'C': '#C8E6C9',
    'D': '#D1C4E9',
    'E': '#FFE0B2',
    'F': '#FFCCBC',
    'G': '#F0F4C3',
    'H': '#E1BEE7',
    'I': '#B2DFDB',
    'J': '#FFEBEE',
    'K': '#C5CAE9',
    'L': '#DCEDC8',
    'M': '#F8BBD0',
    'N': '#D7CCC8',
    'O': '#FFF9C4',
    'P': '#B3E5FC',
    'Q': '#FFAB91',
    'R': '#F5F5F5',
    'S': '#FFCC80',
    'T': '#D1C4E9',
    'U': '#B2EBF2',
    'V': '#F0F4C3',
    'W': '#E6EE9C',
    'X': '#FFECB3',
    'Y': '#B39DDB',
    'Z': '#BCAAA4',
}

start_time = time.time()  # Initialize the start time

@app.route('/')
def index():
    global start_time
    elapsed_time = time.time() - start_time
    return render_template('index.html', grid=grid, regions=regions, region_colors=region_colors, elapsed_time=int(elapsed_time))


@app.route('/update_cell', methods=['POST'])
def update_cell():
    data = request.json
    row = data['row']
    col = data['col']
    is_reverse = data['is_reverse']
    cell = click_grid[row][col]

    if is_reverse:
        # Reverse toggle: 2 -> 1 -> 0 -> 2
        cell['state'] = (cell['state'] - 1) % 3
    else:
        # Normal toggle: 0 -> 1 -> 2 -> 0
        cell['state'] = (cell['state'] + 1) % 3
    
    grid = create_grid_from_click_grid(click_grid)
    return jsonify(success=True, cell=cell, grid=grid)


@app.route('/reset_grid', methods=['POST'])
def reset_grid():
    global grid, click_grid, start_time
    grid_size = len(grid)
    click_grid = initialize_grid(grid_size)
    grid = create_grid_from_click_grid(click_grid)
    start_time = time.time()  # Reset the timer
    return jsonify(success=True)

@app.route('/load_game', methods=['POST'])
def load_game():
    global regions, grid, click_grid  # Ensure regions and grid are updated globally
    logger.info("Loading game from clipboard image")
    n = int(request.form.get('n'))

    image = request.files['image'].read()
    image = Image.open(BytesIO(image))

    regions = read_grid_from_image(image, grid_size=n)
    click_grid = initialize_grid(n)
    grid = create_grid_from_click_grid(click_grid)
    return jsonify(success=True, regions=regions, region_colors=region_colors)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
