import streamlit as st
import random
import numpy as np
from PIL import Image
import io
import base64

# Configure page
st.set_page_config(
    page_title="Yahtzee Bingo Prototype",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
.game-board {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    max-width: 600px;
    margin: 0 auto;
}

.board-cell {
    aspect-ratio: 1;
    border: 3px solid #ccc;
    border-radius: 15px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 10px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    min-height: 120px;
}

.cell-normal {
    background: linear-gradient(145deg, #ff9a56, #ff7043);
    color: white;
    border-color: #e64a19;
}

.cell-multiplier {
    background: linear-gradient(145deg, #ff5722, #d32f2f);
    color: white;
    border-color: #b71c1c;
}

.cell-blocked {
    background: linear-gradient(145deg, #666, #333);
    color: white;
    border-color: #000;
}

.cell-filled {
    background: linear-gradient(145deg, #4caf50, #388e3c);
    color: white;
    border-color: #2e7d32;
}

.cell-selected {
    border-color: #2196f3 !important;
    border-width: 4px !important;
    box-shadow: 0 0 15px rgba(33, 150, 243, 0.5);
}

.dice-container {
    display: flex;
    justify-content: center;
    gap: 15px;
    margin: 20px 0;
}

.die {
    width: 60px;
    height: 60px;
    border: 2px solid #333;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
}

.die-normal {
    background: white;
    color: black;
}

.die-held {
    background: #ffcdd2;
    color: #d32f2f;
    border-color: #d32f2f;
}

.score-display {
    background: linear-gradient(145deg, #ffc107, #ff8f00);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'dice' not in st.session_state:
        st.session_state.dice = [1, 1, 1, 1, 1]
    if 'held_dice' not in st.session_state:
        st.session_state.held_dice = [False] * 5
    if 'rolls_left' not in st.session_state:
        st.session_state.rolls_left = 3
    if 'has_rolled' not in st.session_state:
        st.session_state.has_rolled = False
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'board' not in st.session_state:
        st.session_state.board = generate_board()
    if 'selected_cell' not in st.session_state:
        st.session_state.selected_cell = None
    if 'bingos' not in st.session_state:
        st.session_state.bingos = 0

# Yahtzee categories and scoring
def get_categories():
    return {
        'ones': {
            'name': 'Ones',
            'icon': '⚀',
            'score': lambda dice: sum(d for d in dice if d == 1)
        },
        'twos': {
            'name': 'Twos', 
            'icon': '⚁',
            'score': lambda dice: sum(d for d in dice if d == 2)
        },
        'threes': {
            'name': 'Threes',
            'icon': '⚂', 
            'score': lambda dice: sum(d for d in dice if d == 3)
        },
        'fours': {
            'name': 'Fours',
            'icon': '⚃',
            'score': lambda dice: sum(d for d in dice if d == 4)
        },
        'fives': {
            'name': 'Fives',
            'icon': '⚄',
            'score': lambda dice: sum(d for d in dice if d == 5)
        },
        'sixes': {
            'name': 'Sixes',
            'icon': '⚅',
            'score': lambda dice: sum(d for d in dice if d == 6)
        },
        'chance': {
            'name': 'Chance',
            'icon': '❓',
            'score': lambda dice: sum(dice)
        },
        'yahtzee': {
            'name': 'Yahtzee',
            'icon': '🎲',
            'score': lambda dice: 50 if len(set(dice)) == 1 else 0
        },
        'full_house': {
            'name': 'Full House',
            'icon': '🏠',
            'score': lambda dice: 25 if is_full_house(dice) else 0
        },
        'small_straight': {
            'name': 'Small',
            'icon': '📊',
            'score': lambda dice: 30 if is_small_straight(dice) else 0
        },
        'large_straight': {
            'name': 'Large', 
            'icon': '📈',
            'score': lambda dice: 40 if is_large_straight(dice) else 0
        },
        'evens': {
            'name': 'Evens',
            'icon': '2️⃣',
            'score': lambda dice: sum(d for d in dice if d % 2 == 0)
        },
        'odds': {
            'name': 'Odds',
            'icon': '1️⃣', 
            'score': lambda dice: sum(d for d in dice if d % 2 == 1)
        },
        'pair': {
            'name': 'Pair',
            'icon': '👥',
            'score': lambda dice: get_best_pair(dice)
        },
        'multiplier_3x': {
            'name': '3x',
            'icon': '3️⃣',
            'type': 'multiplier',
            'multiplier': 3,
            'score': lambda dice: sum(dice) * 3
        },
        'multiplier_4x': {
            'name': '4x',
            'icon': '4️⃣', 
            'type': 'multiplier',
            'multiplier': 4,
            'score': lambda dice: sum(dice) * 4
        }
    }

# Scoring helper functions
def is_full_house(dice):
    counts = {}
    for d in dice:
        counts[d] = counts.get(d, 0) + 1
    values = list(counts.values())
    return 3 in values and 2 in values

def is_small_straight(dice):
    unique_sorted = sorted(set(dice))
    if len(unique_sorted) < 4:
        return False
    
    for i in range(len(unique_sorted) - 3):
        if (unique_sorted[i] + 1 == unique_sorted[i+1] and 
            unique_sorted[i+1] + 1 == unique_sorted[i+2] and 
            unique_sorted[i+2] + 1 == unique_sorted[i+3]):
            return True
    return False

def is_large_straight(dice):
    unique_sorted = sorted(set(dice))
    return unique_sorted in [[1,2,3,4,5], [2,3,4,5,6]]

def get_best_pair(dice):
    counts = {}
    for d in dice:
        counts[d] = counts.get(d, 0) + 1
    
    pairs = [value for value, count in counts.items() if count >= 2]
    return max(pairs) * 2 if pairs else 0

# Generate random board
def generate_board():
    categories = get_categories()
    category_keys = list(categories.keys())
    random.shuffle(category_keys)
    
    # Take 15 categories + 1 blocked cell
    selected_categories = category_keys[:15]
    
    board = []
    cat_index = 0
    
    for row in range(4):
        board_row = []
        for col in range(4):
            # Place blocked cell at position (2,2)
            if row == 2 and col == 2:
                board_row.append({
                    'type': 'blocked',
                    'name': 'X',
                    'icon': '❌',
                    'filled': True,
                    'score': 0
                })
            else:
                cat_key = selected_categories[cat_index]
                cat = categories[cat_key]
                board_row.append({
                    'type': cat.get('type', 'normal'),
                    'category_key': cat_key,
                    'name': cat['name'],
                    'icon': cat['icon'],
                    'filled': False,
                    'score': 0,
                    'score_func': cat['score']
                })
                cat_index += 1
        board.append(board_row)
    
    return board

# Roll dice
def roll_dice():
    if st.session_state.rolls_left > 0:
        new_dice = []
        for i in range(5):
            if st.session_state.held_dice[i]:
                new_dice.append(st.session_state.dice[i])
            else:
                new_dice.append(random.randint(1, 6))
        
        st.session_state.dice = new_dice
        st.session_state.rolls_left -= 1
        st.session_state.has_rolled = True

# Toggle dice hold
def toggle_dice_hold(index):
    if st.session_state.has_rolled and st.session_state.rolls_left > 0:
        st.session_state.held_dice[index] = not st.session_state.held_dice[index]

# Select cell
def select_cell(row, col):
    cell = st.session_state.board[row][col]
    if cell['type'] != 'blocked' and not cell['filled']:
        st.session_state.selected_cell = (row, col)

# Submit to cell
def submit_to_cell():
    if st.session_state.selected_cell and st.session_state.has_rolled:
        row, col = st.session_state.selected_cell
        cell = st.session_state.board[row][col]
        
        if not cell['filled']:
            # Calculate score
            score = cell['score_func'](st.session_state.dice)
            
            # Update cell
            st.session_state.board[row][col]['filled'] = True
            st.session_state.board[row][col]['score'] = score
            
            # Update total score
            st.session_state.score += score
            
            # Check for bingos
            check_bingos()
            
            # Reset turn
            reset_turn()

def check_bingos():
    bingos = 0
    board = st.session_state.board
    
    # Check rows
    for row in range(4):
        if all(board[row][col]['filled'] for col in range(4)):
            bingos += 1
    
    # Check columns  
    for col in range(4):
        if all(board[row][col]['filled'] for row in range(4)):
            bingos += 1
    
    # Check diagonals
    if all(board[i][i]['filled'] for i in range(4)):
        bingos += 1
    if all(board[i][3-i]['filled'] for i in range(4)):
        bingos += 1
    
    st.session_state.bingos = bingos

def reset_turn():
    st.session_state.dice = [1, 1, 1, 1, 1]
    st.session_state.held_dice = [False] * 5
    st.session_state.rolls_left = 3
    st.session_state.has_rolled = False
    st.session_state.selected_cell = None

def reset_game():
    st.session_state.dice = [1, 1, 1, 1, 1]
    st.session_state.held_dice = [False] * 5
    st.session_state.rolls_left = 3
    st.session_state.has_rolled = False
    st.session_state.score = 0
    st.session_state.board = generate_board()
    st.session_state.selected_cell = None
    st.session_state.bingos = 0

# Main app
def main():
    init_session_state()
    
    st.title("🎲 Yahtzee Bingo Prototype")
    
    # Header with score and controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="score-display">
            <h3>Score: {st.session_state.score}</h3>
            <p>Bingos: {st.session_state.bingos}/10</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Game Controls")
        if st.button("🎲 Roll Dice", disabled=(st.session_state.rolls_left == 0)):
            roll_dice()
            st.rerun()
        
        st.write(f"Rolls left: {st.session_state.rolls_left}")
    
    with col3:
        if st.button("🔄 New Game"):
            reset_game()
            st.rerun()
    
    # Dice display
    st.markdown("### 🎲 Dice")
    dice_cols = st.columns(5)
    
    for i, die_value in enumerate(st.session_state.dice):
        with dice_cols[i]:
            held_style = "die-held" if st.session_state.held_dice[i] else "die-normal"
            if st.button(f"{die_value}", key=f"die_{i}", 
                        disabled=not st.session_state.has_rolled or st.session_state.rolls_left == 0):
                toggle_dice_hold(i)
                st.rerun()
    
    if st.session_state.has_rolled:
        st.info("Click dice to hold/unhold them before next roll")
    
    # Game board
    st.markdown("### 🎯 Game Board")
    
    # Display board as a grid using columns
    for row in range(4):
        cols = st.columns(4)
        for col in range(4):
            cell = st.session_state.board[row][col]
            
            with cols[col]:
                # Determine cell style
                if cell['type'] == 'blocked':
                    cell_class = 'blocked'
                elif cell['filled']:
                    cell_class = 'filled'
                elif cell['type'] == 'multiplier':
                    cell_class = 'multiplier'
                else:
                    cell_class = 'normal'
                
                # Check if selected
                selected = st.session_state.selected_cell == (row, col)
                
                # Calculate potential score
                potential_score = 0
                if not cell['filled'] and st.session_state.has_rolled and cell['type'] != 'blocked':
                    potential_score = cell['score_func'](st.session_state.dice)
                
                # Display cell
                cell_content = f"""
                <div style="text-align: center; padding: 10px; border: 2px solid {'#2196f3' if selected else '#ccc'}; 
                     border-radius: 10px; background: {'#e3f2fd' if selected else '#f5f5f5'}; min-height: 100px;
                     display: flex; flex-direction: column; justify-content: center;">
                    <div style="font-size: 24px;">{cell['icon']}</div>
                    <div style="font-weight: bold; margin: 5px 0;">{cell['name']}</div>
                    {f'<div style="color: green; font-weight: bold;">Score: {cell["score"]}</div>' if cell['filled'] else ''}
                    {f'<div style="color: blue; font-size: 12px;">Would score: {potential_score}</div>' if potential_score > 0 else ''}
                </div>
                """
                
                st.markdown(cell_content, unsafe_allow_html=True)
                
                if st.button(f"Select", key=f"cell_{row}_{col}", 
                           disabled=cell['filled'] or cell['type'] == 'blocked'):
                    select_cell(row, col)
                    st.rerun()
    
    # Submit button
    if st.session_state.selected_cell and st.session_state.has_rolled:
        row, col = st.session_state.selected_cell
        cell = st.session_state.board[row][col]
        potential_score = cell['score_func'](st.session_state.dice)
        
        st.success(f"Selected: {cell['name']} - Will score {potential_score} points")
        
        if st.button("✅ Submit Score", type="primary"):
            submit_to_cell()
            st.rerun()
    
    # Instructions
    with st.expander("📖 How to Play"):
        st.markdown("""
        1. **Roll the dice** up to 3 times per turn
        2. **Hold dice** by clicking them between rolls
        3. **Select a cell** on the board that matches your dice
        4. **Submit** your score to fill that cell
        5. **Get bingos** by completing rows, columns, or diagonals
        6. **Special cells:**
           - 🏠 Full House: 3 of one number + 2 of another = 25 points
           - 📊 Small Straight: 4 in a row = 30 points  
           - 📈 Large Straight: 5 in a row = 40 points
           - 🎲 Yahtzee: All same number = 50 points
           - 3️⃣/4️⃣ Multipliers: Multiply your dice sum by 3x or 4x
        """)

if __name__ == "__main__":
    main()
