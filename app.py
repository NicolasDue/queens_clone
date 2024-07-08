from flask import Flask, render_template, jsonify, request
import time
from PIL import Image
from io import BytesIO
from image_parser import read_grid_from_image
from loguru import logger
import distinctipy

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


def initialize_grid(grid_size):
    return [[{"state": 0} for _ in range(grid_size)] for _ in range(grid_size)]

def validate_grid(grid, regions):
    n = len(grid)
    stars_per_row = [0] * n
    stars_per_col = [0] * n
    stars_per_region = {}

    for row in range(n):
        for col in range(n):
            if grid[row][col]['state'] == 2:  # If it's a star
                # Check this row
                if stars_per_row[row] >= 1:
                    return False
                stars_per_row[row] += 1

                # Check this column
                if stars_per_col[col] >= 1:
                    return False
                stars_per_col[col] += 1

                # Check adjacent cells (including diagonals)
                for i in range(max(0, row-1), min(n, row+2)):
                    for j in range(max(0, col-1), min(n, col+2)):
                        if (i != row or j != col) and grid[i][j]['state'] == 2:
                            return False

                # Check the region
                current_region = regions[row][col]
                if current_region in stars_per_region:
                    if stars_per_region[current_region] >= 2:
                        return False
                    stars_per_region[current_region] += 1
                else:
                    stars_per_region[current_region] = 1

    # Check if all rows, columns, and regions have exactly 1 star
    if any(count != 1 for count in stars_per_row + stars_per_col):
        return False
    if any(count != 1 for count in stars_per_region.values()):
        return False

    return True


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

def generate_region_colors(n):
    # Generate n distinct colors
    colors = distinctipy.get_colors(n, pastel_factor=3)
    
    # Convert the colors to hexadecimal format
    hex_colors = ['#{:02x}{:02x}{:02x}'.format(int(c[0]*255), int(c[1]*255), int(c[2]*255)) for c in colors]
    
    # Create region labels (A, B, C, ...)
    region_labels = [chr(65 + i) for i in range(n)]
    
    # Create the dictionary
    region_colors = dict(zip(region_labels, hex_colors))
    
    return region_colors

region_colors = generate_region_colors(len(grid))

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
        cell['state'] = (cell['state'] - 1) % 3
    else:
        cell['state'] = (cell['state'] + 1) % 3
    
    grid = create_grid_from_click_grid(click_grid)
    is_valid = validate_grid(grid, regions)
    logger.info(f"Is valid: {is_valid}")
    return jsonify(success=True, cell=cell, grid=grid, is_valid=is_valid)


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
    global regions, grid, click_grid, region_colors  # Ensure regions and grid are updated globally
    logger.info("Loading game from clipboard image")
    n = int(request.form.get('n'))

    image = request.files['image'].read()
    image = Image.open(BytesIO(image))

    regions = read_grid_from_image(image, grid_size=n)
    click_grid = initialize_grid(n)
    grid = create_grid_from_click_grid(click_grid)

    region_colors = generate_region_colors(len(grid))
    return jsonify(success=True, regions=regions, region_colors=region_colors)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
