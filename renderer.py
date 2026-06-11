from PIL import Image, ImageDraw, ImageFont

# =========================
# THEME
# =========================

BACKGROUND_COLOR = "#232f3b"

BOX_COLOR_A = "#2F4154"
BOX_COLOR_B = "#263445"

GRID_COLOR = "#c3cbeb"

GRID_SHADOW_COLOR = "#000000"

COORDINATE_COLOR = "#abc5e0"

PREFILLED_NUMBER_COLOR = "#abc5e0"
PLAYER_NUMBER_COLOR = "#ffffff"

NUMBER_Y_OFFSET = -8

SHADOW_OFFSET = 2
SHADOW_ALPHA = 80  # soft feel


# =========================
# RENDER FUNCTION
# =========================

def render_board(board, original_board):
    img = Image.new("RGB", (1000, 1000), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    margin = 50
    board_size = 900
    cell_size = board_size // 9

    font = ImageFont.truetype(
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        24
    )

    number_font = ImageFont.truetype(
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        64
    )

    # =========================
    # 1. BOX BACKGROUNDS
    # =========================
    for box_row in range(3):
        for box_col in range(3):

            color = BOX_COLOR_A if (box_row + box_col) % 2 == 0 else BOX_COLOR_B

            x1 = margin + box_col * 3 * cell_size
            y1 = margin + box_row * 3 * cell_size

            x2 = x1 + 3 * cell_size
            y2 = y1 + 3 * cell_size

            draw.rectangle([x1, y1, x2, y2], fill=color)

    # =========================
    # 2. GRID SHADOW (draw first)
    # =========================
    for i in range(10):
        width = 6 if i % 3 == 0 else 2

        x = margin + i * cell_size + SHADOW_OFFSET
        y = margin + i * cell_size + SHADOW_OFFSET

        draw.line(
            (x, margin + SHADOW_OFFSET, x, margin + board_size + SHADOW_OFFSET),
            fill=GRID_SHADOW_COLOR,
            width=width
        )

        draw.line(
            (margin + SHADOW_OFFSET, y, margin + board_size + SHADOW_OFFSET, y),
            fill=GRID_SHADOW_COLOR,
            width=width
        )

    # =========================
    # 3. GRID MAIN (on top)
    # =========================
    for i in range(10):
        width = 6 if i % 3 == 0 else 2

        x = margin + i * cell_size
        y = margin + i * cell_size

        draw.line(
            (x, margin, x, margin + board_size),
            fill=GRID_COLOR,
            width=width
        )

        draw.line(
            (margin, y, margin + board_size, y),
            fill=GRID_COLOR,
            width=width
        )

    # =========================
    # 4. NUMBERS (WITH SHADOW)
    # =========================
    for row in range(9):
        for col in range(9):

            value = board[row][col]
            if value == 0:
                continue

            center_x = margin + col * cell_size + cell_size // 2
            center_y = margin + row * cell_size + cell_size // 2

            text = str(value)

            bbox = draw.textbbox((0, 0), text, font=number_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            if original_board[row][col] != 0:
                fill = PREFILLED_NUMBER_COLOR
            else:
                fill = PLAYER_NUMBER_COLOR

            # shadow
            draw.text(
                (
                    center_x - text_width / 2 + SHADOW_OFFSET,
                    center_y - text_height / 2 + NUMBER_Y_OFFSET + SHADOW_OFFSET
                ),
                text,
                fill=GRID_SHADOW_COLOR,
                font=number_font
            )

            # main number
            draw.text(
                (
                    center_x - text_width / 2,
                    center_y - text_height / 2 + NUMBER_Y_OFFSET
                ),
                text,
                fill=fill,
                font=number_font
            )

    # =========================
    # 5. COORDINATES
    # =========================
    letters = "ABCDEFGHI"

    for col in range(9):
        x = margin + col * cell_size + cell_size // 2
        draw.text((x - 6, 18), letters[col], fill=COORDINATE_COLOR, font=font)

    for row in range(9):
        y = margin + row * cell_size + cell_size // 2
        draw.text((18, y - 8), str(row + 1), fill=COORDINATE_COLOR, font=font)

    # =========================
    # SAVE
    # =========================
    img.save("board.png")
    return "board.png"


# =========================
# UTILITY
# =========================

def sudoku_to_grid(sudoku):
    sudoku_string = str(sudoku).zfill(81)

    board = []

    for row in range(9):
        current_row = []
        for col in range(9):
            index = row * 9 + col
            current_row.append(int(sudoku_string[index]))

        board.append(current_row)

    return board