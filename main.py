import ctypes
import sys
import time

import pyautogui as pag

try:
    from PIL import Image, ImageGrab
except ImportError:
    Image = None
    ImageGrab = None

NUMS = list("123456")
DIGITS = set(NUMS)
GRID_SIZE = 6

VK_F8 = 0x77
VK_ESC = 0x1B


def valid(check: list):
    return len(check) == 6 and set(check) == set(NUMS)

def is_solved(board: list):
    # check rows
    for row in board:
        if not valid(row):
            return False

    # check cols
    rotated = [list(row) for row in zip(*board)][::-1]
    for row in rotated:
        if not valid(row):
            return False

    # check boxes
    for box_r in range(3):
        for box_c in range(2):
            nums = []
            nums.append(board[box_r*2+0][box_c*3+0])
            nums.append(board[box_r*2+0][box_c*3+1])
            nums.append(board[box_r*2+0][box_c*3+2])
            nums.append(board[box_r*2+1][box_c*3+0])
            nums.append(board[box_r*2+1][box_c*3+1])
            nums.append(board[box_r*2+1][box_c*3+2])
            if not valid(nums):
                return False
    return True

def can_place(board: list, r: int, c: int, ch: str):
    # row and column
    for i in range(6):
        if board[r][i] == ch or board[i][c] == ch:
            return False

    # 2x3 box
    box_r = (r // 2) * 2
    box_c = (c // 3) * 3
    for dr in range(2):
        for dc in range(3):
            if board[box_r+dr][box_c+dc] == ch:
                return False
    return True

def solve(board: list, r: int = 0, c: int = 0):
    if r == 6:
        return board
    nr, nc = (r, c + 1) if c < 5 else (r + 1, 0)

    if board[r][c] != "0":
        return solve(board, nr, nc)

    for ch in NUMS:
        if can_place(board, r, c, ch):
            board[r][c] = ch
            result = solve(board, nr, nc)
            if result is not None:
                return result
            board[r][c] = "0"
    return None


def parse_row(raw: str):
    """Turn one line of manual input into a six-character board row."""
    raw = raw.strip().replace(" ", "").replace(".", "0").replace("_", "0")
    if len(raw) != GRID_SIZE or any(ch not in "0123456" for ch in raw):
        return None
    return raw


def read_manual_board():
    print("Enter the six rows. Use 1-6 for givens; use 0 or . for blanks.")
    board = []
    for r in range(GRID_SIZE):
        while True:
            raw = input(f"Row {r + 1}: ")
            row = parse_row(raw)
            if row is None:
                print("Enter exactly 6 characters using 1-6; use 0 or . for blanks.")
                continue
            board.append(list(row))
            break
    return board


def edit_board(board: list):
    print("Enter a corrected row, or press Enter to keep the current row.")
    for r in range(GRID_SIZE):
        current = "".join(board[r]).replace("0", ".")
        while True:
            raw = input(f"Row {r + 1} [{current}]: ")
            if not raw.strip():
                break
            row = parse_row(raw)
            if row is None:
                print("Enter exactly 6 characters using 1-6; use 0 or . for blanks.")
                continue
            board[r] = list(row)
            break


def has_conflicts(board: list):
    for r in range(GRID_SIZE):
        values = [value for value in board[r] if value != "0"]
        if len(values) != len(set(values)):
            return True

    for c in range(GRID_SIZE):
        values = [board[r][c] for r in range(GRID_SIZE) if board[r][c] != "0"]
        if len(values) != len(set(values)):
            return True

    for box_r in range(0, GRID_SIZE, 2):
        for box_c in range(0, GRID_SIZE, 3):
            values = [
                board[r][c]
                for r in range(box_r, box_r + 2)
                for c in range(box_c, box_c + 3)
                if board[r][c] != "0"
            ]
            if len(values) != len(set(values)):
                return True

    return False


def display_board(board: list, uncertain: list):
    uncertain_cells = {(r, c) for r, c, _text, _confidence in uncertain}
    print("\nDetected board:")
    for r, row in enumerate(board):
        if r in (2, 4):
            print("  ------+------")
        cells = []
        for c, value in enumerate(row):
            if (r, c) in uncertain_cells:
                cells.append("?")
            else:
                cells.append("." if value == "0" else value)
        print("  " + " ".join(cells[:3]) + " | " + " ".join(cells[3:]))


def review_board(board: list, uncertain: list):
    uncertain = list(uncertain)
    while True:
        display_board(board, uncertain)

        if uncertain:
            print("\nUncertain cells:")
            for r, c, text, confidence in uncertain:
                if text is None:
                    print(f"  R{r + 1}C{c + 1}: ink found but no digit recognized")
                else:
                    print(f"  R{r + 1}C{c + 1}: read as {text} ({confidence:.0%} confidence)")

        print("\n[Enter] accept   [e] edit rows   [r] recapture   [m] manual entry   [q] quit")
        choice = input("Choice: ").strip().lower()

        if choice in ("", "y", "yes"):
            missing = [cell for cell in uncertain if cell[2] is None]
            if missing:
                cells = ", ".join(f"R{r + 1}C{c + 1}" for r, c, _text, _confidence in missing)
                print(f"These cells contain ink but no digit was recognized: {cells}.")
                print("Please edit those rows or recapture before accepting.")
                continue
            if has_conflicts(board):
                print("Duplicate numbers found in a row, column, or box. Please edit or recapture.")
                continue
            return "accept", board

        if choice == "e":
            edit_board(board)
            uncertain = []
            continue

        if choice == "r":
            return "recapture", board

        if choice == "m":
            return "manual", board

        if choice == "q":
            return "quit", board

        print("Invalid choice.")


def _beep(frequency: int = 1000, duration: int = 100):
    try:
        import winsound

        winsound.Beep(frequency, duration)
    except Exception:
        print("\a", end="", flush=True)


def _flash_console():
    if sys.platform != "win32":
        return
    try:
        window = ctypes.windll.kernel32.GetConsoleWindow()
        if window:
            ctypes.windll.user32.FlashWindow(window, True)
    except Exception:
        pass


def wait_for_capture_key():
    """Wait globally for F8 or Esc. Returns 'f8', 'esc', or 'enter'."""
    if sys.platform != "win32":
        input("Press ENTER to capture the current mouse position...")
        return "enter"

    user32 = ctypes.windll.user32
    while True:
        if user32.GetAsyncKeyState(VK_F8) & 0x8000:
            key, name = VK_F8, "f8"
            break
        if user32.GetAsyncKeyState(VK_ESC) & 0x8000:
            key, name = VK_ESC, "esc"
            break
        time.sleep(0.02)

    # Wait for the key to be released so it does not trigger the next capture.
    while user32.GetAsyncKeyState(key) & 0x8000:
        time.sleep(0.02)

    return name


def capture_corner(label: str):
    print(f"\nHover the mouse over the OUTER {label} corner of the 6x6 grid.")
    print("Press F8 to capture, or Esc to cancel.")
    key = wait_for_capture_key()
    if key == "esc":
        print("Cancelled.")
        return None

    position = pag.position()
    _beep(1200 if label == "top-left" else 800, 80)
    print(f"Captured {label} at ({position.x}, {position.y}).")
    return (position.x, position.y)


def select_grid_region():
    print("\nSelect the full 6x6 grid.")
    while True:
        top_left = capture_corner("top-left")
        if top_left is None:
            return None

        bottom_right = capture_corner("bottom-right")
        if bottom_right is None:
            return None

        left, right = sorted((top_left[0], bottom_right[0]))
        top, bottom = sorted((top_left[1], bottom_right[1]))
        width = right - left + 1
        height = bottom - top + 1

        if width < 120 or height < 120:
            print(f"The selected area is too small ({width}x{height}). Please try again.")
            continue

        ratio = width / height
        if not (0.75 <= ratio <= 1.33):
            print(f"The selected area is {width}x{height}, which is not roughly square. Please try again.")
            continue

        print(f"Selected region: ({left}, {top}) to ({right}, {bottom}) [{width}x{height}]")
        return (left, top, right, bottom)


def capture_region(region: tuple):
    left, top, right, bottom = region
    time.sleep(0.25)
    return ImageGrab.grab(bbox=(left, top, right + 1, bottom + 1), all_screens=True)


def _normalize_ocr_text(text: str):
    text = "".join(ch for ch in text if ch.isalnum())
    return (
        text.replace("I", "1")
        .replace("l", "1")
        .replace("S", "5")
        .replace("s", "5")
        .replace("G", "6")
        .replace("b", "6")
        .replace("O", "0")
        .replace("o", "0")
    )


def classify_cell(cell, ocr):
    try:
        result = ocr.classification(cell, probability=True)
    except Exception as exc:
        print(f"OCR error: {exc}")
        return "", 0.0

    if isinstance(result, str):
        return _normalize_ocr_text(result), 1.0

    text = _normalize_ocr_text(str(result.get("text", "")))
    confidence = 0.0
    try:
        values = [p for step in result.get("probabilities", []) for p in step[0]]
        if values:
            confidence = max(values)
    except (IndexError, TypeError):
        pass
    return text, confidence


def has_ink(cell):
    """Return True when a cell contains something besides its background."""
    gray = cell.convert("L")
    histogram = gray.histogram()
    total = sum(histogram)
    if total == 0:
        return False

    background = max(range(256), key=histogram.__getitem__)
    darker = sum(histogram[: max(0, background - 40)])
    lighter = sum(histogram[min(255, background + 40) + 1 :])
    return max(darker, lighter) / total >= 0.02


def read_board_from_image(image, ocr):
    board = []
    uncertain = []
    inset = 0.14
    cell_width = image.width / GRID_SIZE
    cell_height = image.height / GRID_SIZE

    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            left = round(c * cell_width + cell_width * inset)
            top = round(r * cell_height + cell_height * inset)
            right = round((c + 1) * cell_width - cell_width * inset)
            bottom = round((r + 1) * cell_height - cell_height * inset)
            cell = image.crop((left, top, right, bottom))

            if min(cell.size) < 48:
                scale = max(2, 64 // min(cell.size))
                cell = cell.resize(
                    (cell.width * scale, cell.height * scale),
                    Image.Resampling.LANCZOS,
                )

            text, confidence = classify_cell(cell, ocr)
            if text in DIGITS:
                row.append(text)
                if confidence < 0.90:
                    uncertain.append((r, c, text, confidence))
            elif has_ink(cell):
                row.append("0")
                uncertain.append((r, c, None, confidence))
            else:
                row.append("0")
        board.append(row)

    return board, uncertain


def _solve_manual():
    board = read_manual_board()
    solved = solve([row[:] for row in board])
    if solved is None:
        print("No solution exists")
        return None
    return board, solved


def auto_mode():
    if Image is None or ImageGrab is None:
        print("Auto-detect requires Pillow and ddddocr.")
        print("Install them with: python -m pip install -r requirements.txt")
        print("\nFalling back to manual entry.")
        return _solve_manual()

    try:
        import ddddocr
    except Exception as exc:
        print("Auto-detect requires Pillow and ddddocr.")
        print("Install them with: python -m pip install -r requirements.txt")
        print(f"Details: {exc}")
        print("\nFalling back to manual entry.")
        return _solve_manual()

    print("Loading OCR engine...")
    try:
        ocr = ddddocr.DdddOcr(show_ad=False)
    except Exception as exc:
        print(f"Could not initialize the OCR engine: {exc}")
        print("Falling back to manual entry.")
        return _solve_manual()

    while True:
        region = select_grid_region()
        if region is None:
            return None

        print("Capturing selected area...")
        try:
            image = capture_region(region)
        except Exception as exc:
            print(f"Could not capture the screen: {exc}")
            print("Falling back to manual entry.")
            return _solve_manual()

        print("Reading board...")
        try:
            board, uncertain = read_board_from_image(image, ocr)
        except Exception as exc:
            print(f"Could not read the board: {exc}")
            print("Falling back to manual entry.")
            return _solve_manual()
        _flash_console()
        _beep()
        print("Switch to this terminal to review the detected board.")

        while True:
            action, board = review_board(board, uncertain)

            if action == "quit":
                return None
            if action == "recapture":
                break
            if action == "manual":
                return _solve_manual()

            solved = solve([row[:] for row in board])
            if solved is None:
                print("No solution exists for this board. The OCR may have misread a cell.")
                print("Please edit the board or recapture.")
                uncertain = []
                continue
            return board, solved


def main():
    print("How do you want to enter the board?")
    print("  1. Auto-detect from screen (default)")
    print("  2. Manual entry")
    choice = input("Choice [1]: ").strip().lower()

    if choice in ("2", "m", "manual"):
        result = _solve_manual()
    else:
        result = auto_mode()

    if result is None:
        return

    _board, solved = result

    if not is_solved(solved):
        raise AssertionError("Solver produced an invalid board")

    print("Solved board:")
    for row in solved:
        print("".join(row))

    print()
    input("Press ENTER to fill solution in 4 seconds (click the top-left cell) ")
    pag.sleep(4)
    for r, row in enumerate(solved):
        for c, ch in enumerate(row):
            pag.press(ch)
            if c < 5:
                pag.press("right")
            elif r < 5:
                pag.press("down")
                pag.press("left", presses=5)

if __name__ == "__main__":
    main()
