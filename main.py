import pyautogui as pag

NUMS = list("123456")

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

    if board[r][c] != '0':
        return solve(board, nr, nc)

    for ch in NUMS:
        if can_place(board, r, c, ch):
            board[r][c] = ch
            result = solve(board, nr, nc)
            if result is not None:
                return result
            board[r][c] = '0'
    return None

def main():
    board = []
    for _ in range(6):
        row = input("Enter row (0 for blanks): ").strip().replace(" ", "0")
        if len(row) != 6:
            raise ValueError("Invalid row length")
        for l in row:
            if l not in "0123456":
                raise ValueError("One or more number is invalid")
        board.append(list(row))

    solved = solve(board)
    if solved is None:
        print("No solution exists")
    else:
        if not is_solved(solved):
            raise AssertionError("Solver produced an invalid board")
        for row in solved:
            print(''.join(row))

        input("Press ENTER to fill solution in 2 seconds (select top left box) ")
        pag.sleep(2)
        for r, row in enumerate(solved):
            for c, ch in enumerate(row):
                pag.press(ch)
                if c < 5:
                    pag.press('right')
                elif r < 5:
                    pag.press('down')
                    pag.press('left', presses=5)

if __name__ == "__main__":
    main()