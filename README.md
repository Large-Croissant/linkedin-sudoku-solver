# LinkedIn Sudoku Solver

A small 6x6 Sudoku solver. It can read the board from the screen with OCR or accept it manually, then types the solution into the game with PyAutoGUI.

## Setup

1. Install Python 3.10 or newer.
2. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Run the script:

   ```powershell
   python main.py
   ```

## Usage

### Auto-detect

Choose `1` (or press Enter) at the prompt.

1. Hover the mouse over the **outer top-left corner** of the 6x6 grid and press **F8**.
2. Hover the mouse over the **outer bottom-right corner** and press **F8**.
3. Review the detected board:
   - **Enter** accepts
   - **e** edits rows
   - **r** recaptures
   - **m** switches to manual entry
   - **q** quits
4. After solving, switch to the game and click the top-left cell within the 2-second countdown.

Press **Esc** while selecting corners to cancel.

### Manual entry

Choose `2` at the prompt and enter six rows. Use `1`–`6` for givens and `0` or `.` for blanks. Spaces are ignored, so `1 2 . . . 3` works.

## Notes

- Auto-detect requires the whole grid to be visible and unobstructed.
- The solver is built for the 6x6 / 2x3-box layout.
- OCR uses `ddddocr`; no separate OCR engine needs to be installed.
