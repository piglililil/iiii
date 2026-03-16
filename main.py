"""
main.py — Blind Chess Android App (Kivy)
Features:
  - Blind mode (no board shown by default)
  - Show Board button (ASCII popup)
  - Move log with toggle (on/off)
  - Save game history as TXT
  - Export board as PNG (text-based)
  - 5 AI difficulty levels
  - New Game button
"""

import os
import chess
from chess_ai import get_ai_move
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.switch import Switch
from kivy.core.window import Window
from kivy.metrics import sp, dp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
from kivy.core.clipboard import Clipboard

# ── Colours ────────────────────────────────────────────────────────────────
BG_DARK    = (0.10, 0.10, 0.14, 1)
BG_PANEL   = (0.14, 0.14, 0.20, 1)
BG_INPUT   = (0.18, 0.18, 0.26, 1)
ACCENT     = (0.40, 0.60, 1.00, 1)
ACCENT2    = (0.20, 0.75, 0.50, 1)
RED        = (0.85, 0.25, 0.25, 1)
TEXT_WHITE = (0.95, 0.95, 0.95, 1)
TEXT_GREY  = (0.55, 0.55, 0.65, 1)

# ── Piece Assets ──────────────────────────────────────────────────────────
PIECE_ASSETS = {
    (chess.PAWN,   chess.WHITE): 'assets/wP.png',
    (chess.KNIGHT, chess.WHITE): 'assets/wN.png',
    (chess.BISHOP, chess.WHITE): 'assets/wB.png',
    (chess.ROOK,   chess.WHITE): 'assets/wR.png',
    (chess.QUEEN,  chess.WHITE): 'assets/wQ.png',
    (chess.KING,   chess.WHITE): 'assets/wK.png',
    (chess.PAWN,   chess.BLACK): 'assets/bP.png',
    (chess.KNIGHT, chess.BLACK): 'assets/bN.png',
    (chess.BISHOP, chess.BLACK): 'assets/bB.png',
    (chess.ROOK,   chess.BLACK): 'assets/bR.png',
    (chess.QUEEN,  chess.BLACK): 'assets/bQ.png',
    (chess.KING,   chess.BLACK): 'assets/bK.png',
}

DIFFICULTY_MAP = {
    'Уровень 1 (Новичок)':    1,
    'Уровень 2 (Лёгкий)':     2,
    'Уровень 3 (Средний)':    3,
    'Уровень 4 (Сложный)':    4,
    'Уровень 5 (Гроссмейстер)': 5,
}

# ── Square Colors (Match the reference image) ───────────────────────────────
COLOR_LIGHT = (0.94, 0.85, 0.71, 1) # #f0d9b5
COLOR_DARK  = (0.71, 0.53, 0.39, 1) # #b58863
PIECE_WHITE = (1.00, 1.00, 1.00, 1)
PIECE_BLACK = (0.00, 0.00, 0.00, 1)


class ChessSquare(BoxLayout):
    def __init__(self, bg_color, piece_path='', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(2)
        with self.canvas.before:
            self.canvas_color = Color(*bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        
        if piece_path:
            self.add_widget(Image(source=piece_path, allow_stretch=True, keep_ratio=True))
            
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


def board_to_ascii(board):
    """Return pretty ASCII art of the chess board."""
    # Local mapping for ASCII symbols as we now use images for the main board
    ascii_map = {
        (chess.KING,   chess.WHITE): 'K', (chess.QUEEN,  chess.WHITE): 'Q',
        (chess.ROOK,   chess.WHITE): 'R', (chess.BISHOP, chess.WHITE): 'B',
        (chess.KNIGHT, chess.WHITE): 'N', (chess.PAWN,   chess.WHITE): 'P',
        (chess.KING,   chess.BLACK): 'k', (chess.QUEEN,  chess.BLACK): 'q',
        (chess.ROOK,   chess.BLACK): 'r', (chess.BISHOP, chess.BLACK): 'b',
        (chess.KNIGHT, chess.BLACK): 'n', (chess.PAWN,   chess.BLACK): 'p',
    }
    lines = []
    lines.append('  ┌───┬───┬───┬───┬───┬───┬───┬───┐')
    for rank in range(7, -1, -1):
        row = f'{rank + 1} │'
        for file in range(8):
            sq = chess.square(file, rank)
            piece = board.piece_at(sq)
            if piece:
                sym = ascii_map.get((piece.piece_type, piece.color), '?')
            else:
                sym = '·' if (rank + file) % 2 == 0 else ' '
            row += f' {sym} │'
        lines.append(row)
        if rank > 0:
            lines.append('  ├───┼───┼───┼───┼───┼───┼───┼───┤')
    lines.append('  └───┴───┴───┴───┴───┴───┴───┴───┘')
    lines.append('    a   b   c   d   e   f   g   h  ')
    return '\n'.join(lines)


def prepare_game_report(board, move_log):
    """Return a plain text move history to save as .txt."""
    header = f"Слепые шахматы — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    header += "=" * 45 + "\n\n"
    history = "История ходов:\n"
    for i, entry in enumerate(move_log):
        history += f"  {i + 1}. {entry}\n"
    footer = "\n" + "=" * 45
    return header + history + footer


def styled_btn(text, bg=BG_PANEL, fg=TEXT_WHITE, size_hint_x=1, bold=False):
    btn = Button(
        text=text,
        size_hint_x=size_hint_x,
        size_hint_y=None,
        height=dp(48),
        background_normal='',
        background_color=bg,
        color=fg,
        font_size=sp(14),
        bold=bold,
    )
    return btn


class BlindChessApp(App):
    def build(self):
        Window.clearcolor = BG_DARK
        self.board = chess.Board()
        self.move_log = []          # list of "Белые: e2e4" strings
        self.show_log = False       # Hidden by default as requested
        self.player_color = chess.WHITE   # human plays white
        self.game_over = False

        root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))

        # ── Header ───────────────────────────────────────────────────────
        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        title = Label(
            text='Слепые шахматы',
            font_size=sp(20),
            bold=True,
            color=ACCENT,
            size_hint_x=0.6,
        )
        self.difficulty_spinner = Spinner(
            text='Уровень 3 (Средний)',
            values=list(DIFFICULTY_MAP.keys()),
            size_hint=(0.4, None),
            height=dp(44),
            background_normal='',
            background_color=BG_PANEL,
            color=TEXT_WHITE,
            font_size=sp(12),
        )
        header.add_widget(title)
        header.add_widget(self.difficulty_spinner)
        root.add_widget(header)

        # ── Status label ─────────────────────────────────────────────────
        self.status_label = Label(
            text='Ваш ход (Белые). Введите ход:',
            size_hint_y=None,
            height=dp(32),
            color=ACCENT2,
            font_size=sp(14),
            halign='left',
            text_size=(Window.width, None),
        )
        root.add_widget(self.status_label)

        # ── Move input row ────────────────────────────────────────────────
        input_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        self.move_input = TextInput(
            hint_text='Введите ход (e2e4 или e4)',
            multiline=False,
            size_hint_x=0.65,
            background_color=BG_INPUT,
            foreground_color=TEXT_WHITE,
            hint_text_color=TEXT_GREY,
            cursor_color=ACCENT,
            font_size=sp(16),
            padding=[dp(10), dp(10)],
        )
        self.move_input.bind(on_text_validate=self.on_move_submit)
        make_btn = styled_btn('Ход ▶', bg=ACCENT, size_hint_x=0.35, bold=True)
        make_btn.bind(on_release=self.on_move_submit)
        input_row.add_widget(self.move_input)
        input_row.add_widget(make_btn)
        root.add_widget(input_row)

        # ── Action buttons ────────────────────────────────────────────────
        btn_row1 = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))

        show_board_btn = styled_btn('👁 Показать доску', bg=(0.25, 0.30, 0.50, 1))
        show_board_btn.bind(on_release=self.show_board_popup)

        self.log_toggle_btn = styled_btn('📋 Лог: ВКЛ', bg=BG_PANEL)
        self.log_toggle_btn.bind(on_release=self.toggle_log)

        btn_row1.add_widget(show_board_btn)
        btn_row1.add_widget(self.log_toggle_btn)
        root.add_widget(btn_row1)

        btn_row2 = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        copy_btn = styled_btn('📋 Копировать историю', bg=(0.20, 0.35, 0.25, 1))
        copy_btn.bind(on_release=self.copy_history)

        new_game_btn = styled_btn('🔄 Новая игра', bg=RED, bold=True)
        new_game_btn.bind(on_release=self.new_game)

        btn_row2.add_widget(copy_btn)
        btn_row2.add_widget(new_game_btn)
        root.add_widget(btn_row2)

        # ── Last move display (always visible) ───────────────────────────
        self.last_move_label = Label(
            text='Ходов ещё не было.',
            size_hint_y=None,
            height=dp(40),
            color=TEXT_WHITE,
            font_size=sp(15),
            bold=True,
            halign='center',
        )
        root.add_widget(self.last_move_label)

        # ── Log area ──────────────────────────────────────────────────────
        self.log_scroll = ScrollView(size_hint=(1, 1))
        self.log_label = Label(
            text='',
            size_hint_y=None,
            color=TEXT_GREY,
            font_size=sp(13),
            halign='left',
            valign='top',
            text_size=(Window.width - dp(30), None),
            markup=True,
        )
        self.log_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        self.log_scroll.add_widget(self.log_label)
        root.add_widget(self.log_scroll)

        return root

    # ── Move handling ─────────────────────────────────────────────────────

    def on_move_submit(self, *args):
        if self.game_over:
            return
        raw = self.move_input.text.strip()
        self.move_input.text = ''
        if not raw:
            return
        self._try_player_move(raw)

    def _try_player_move(self, raw):
        move = None
        # Try UCI first (e2e4), then SAN (e4, Nf3)
        try:
            move = chess.Move.from_uci(raw)
            if move not in self.board.legal_moves:
                move = None
        except Exception:
            pass

        if move is None:
            try:
                move = self.board.parse_san(raw)
            except Exception:
                pass

        if move is None or move not in self.board.legal_moves:
            self.status_label.text = f'[color=ff4444]Нелегальный ход: {raw}[/color]'
            self.status_label.markup = True
            return

        san = self.board.san(move)
        self.board.push(move)
        entry = f'Белые: {san}'
        self.move_log.append(entry)
        self.last_move_label.text = f'Ваш ход: [b]{san}[/b]'
        self.last_move_label.markup = True
        self._update_log()

        if self._check_game_over():
            return

        # AI responds after a tiny delay so UI updates first
        Clock.schedule_once(lambda dt: self._ai_move(), 0.15)

    def _ai_move(self):
        difficulty = DIFFICULTY_MAP.get(self.difficulty_spinner.text, 3)
        move = get_ai_move(self.board, difficulty)
        if move is None:
            return
        san = self.board.san(move)
        self.board.push(move)
        entry = f'Чёрные: {san}'
        self.move_log.append(entry)
        self.last_move_label.text = f'Ход ИИ: [b]{san}[/b]'
        self.last_move_label.markup = True
        self._update_log()

        if not self._check_game_over():
            self.status_label.text = 'Ваш ход (Белые). Введите ход:'
            self.status_label.markup = False

    def _check_game_over(self):
        if self.board.is_game_over():
            self.game_over = True
            result = self.board.result()
            if self.board.is_checkmate():
                winner = 'Чёрные победили!' if self.board.turn == chess.WHITE else 'Белые победили!'
                msg = f'Мат! {winner}'
            elif self.board.is_stalemate():
                msg = 'Пат — ничья!'
            elif self.board.is_insufficient_material():
                msg = 'Недостаточно материала — ничья!'
            elif self.board.is_seventyfive_moves():
                msg = 'Правило 75 ходов — ничья!'
            else:
                msg = f'Игра окончена: {result}'

            self.status_label.text = f'🏁 {msg}'
            self.status_label.markup = False
            self._show_info_popup('Игра окончена', msg)
            return True
        return False

    # ── UI actions ────────────────────────────────────────────────────────

    def toggle_log(self, *args):
        self.show_log = not self.show_log
        self.log_scroll.opacity = 0.6 if self.show_log else 0
        self.log_scroll.size_hint_y = 1 if self.show_log else None
        if not self.show_log:
            self.log_scroll.height = 0
        self.log_toggle_btn.text = '📋 Лог: ВКЛ' if self.show_log else '📋 Лог: ВЫКЛ'

    def _update_log(self):
        if not self.move_log:
            self.log_label.text = ''
            return
        lines = []
        for i in range(0, len(self.move_log), 2):
            move_num = i // 2 + 1
            white = self.move_log[i] if i < len(self.move_log) else ''
            black = self.move_log[i + 1] if i + 1 < len(self.move_log) else ''
            lines.append(f'[b]{move_num}.[/b]  {white}    {black}')
        self.log_label.markup = True
        self.log_label.text = '\n'.join(lines)

    def show_board_popup(self, *args):
        turn = 'Белые' if self.board.turn == chess.WHITE else 'Чёрные'
        
        # Container for the popup
        content = BoxLayout(orientation='vertical', padding=dp(5), spacing=dp(5))
        
        # Info Label
        content.add_widget(Label(
            text=f'Ход: {turn}   |   Полуходов: {self.board.halfmove_clock}',
            size_hint_y=None, height=dp(30), color=ACCENT2, font_size=sp(14), bold=True
        ))

        # ── Graphical Board ──────────────────────────────────────────────────
        # We need a fixed aspect ratio for the board
        board_container = BoxLayout(padding=dp(2), size_hint=(1, 1))
        
        # Main layout: Ranks (Label) + [Files (Label) + Board Grid]
        # To simplify, we'll use a 9x9 grid where:
        # Col 0 is 8..1, Row 8 is a..h
        board_layout = GridLayout(cols=9, rows=9, spacing=0)
        
        # Helper to get piece info
        def get_p(f, r):
            sq = chess.square(f, r)
            piece = self.board.piece_at(sq)
            if piece:
                return PIECE_ASSETS.get((piece.piece_type, piece.color), '')
            return ''

        # Build rows from 8 down to 1
        for r in range(7, -1, -1):
            # Rank label
            board_layout.add_widget(Label(text=str(r+1), size_hint_x=None, width=dp(20), color=TEXT_GREY, font_size=sp(12)))
            for f in range(8):
                is_light = (r + f) % 2 != 0
                bg = COLOR_LIGHT if is_light else COLOR_DARK
                path = get_p(f, r)
                board_layout.add_widget(ChessSquare(bg_color=bg, piece_path=path))
        
        # Bottom row: empty corner + file labels (a-h)
        board_layout.add_widget(Label(size_hint_x=None, width=dp(20)))
        for f in range(8):
            board_layout.add_widget(Label(text=chess.FILE_NAMES[f], size_hint_y=None, height=dp(20), color=TEXT_GREY, font_size=sp(12)))

        board_container.add_widget(board_layout)
        content.add_widget(board_container)

        # Action Buttons
        close_btn = styled_btn('Закрыть', bg=ACCENT, bold=True)
        content.add_widget(close_btn)

        popup = Popup(
            title='Текущая позиция',
            content=content,
            size_hint=(0.98, 0.85),
            background_color=BG_DARK,
            title_color=ACCENT,
            separator_color=ACCENT,
        )
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def copy_history(self, *args):
        """Copy game history to the device clipboard."""
        text = prepare_game_report(self.board, self.move_log)
        Clipboard.put(text)
        self._show_info_popup('Готово!', 'История ходов скопирована в буфер обмена.')

    def new_game(self, *args):
        self.board = chess.Board()
        self.move_log = []
        self.game_over = False
        self.last_move_label.text = 'Ходов ещё не было.'
        self.last_move_label.markup = False
        self.status_label.text = 'Ваш ход (Белые). Введите ход:'
        self.status_label.markup = False
        self.log_label.text = ''

    def _show_info_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        content.add_widget(Label(
            text=message,
            color=TEXT_WHITE,
            font_size=sp(14),
            halign='center',
        ))
        close_btn = styled_btn('OK', bg=ACCENT, bold=True)
        content.add_widget(close_btn)
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.4),
            background_color=BG_DARK,
            title_color=ACCENT,
            separator_color=ACCENT,
        )
        close_btn.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == '__main__':
    try:
        BlindChessApp().run()
    except Exception as e:
        # Emergency logging for Android startup crashes
        import traceback
        import os
        from kivy.app import App
        try:
            log_dir = App.get_running_app().user_data_dir if App.get_running_app() else "."
        except:
            log_dir = "."
        
        with open(os.path.join(log_dir, 'error_log.txt'), 'w') as f:
            f.write(str(e))
            f.write('\n')
            f.write(traceback.format_exc())
