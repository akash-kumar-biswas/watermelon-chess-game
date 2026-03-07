import math
import os
import sys
import pygame
from watermelon_chess import State, actions, result, utility, minimax, monte_carlo


# Window / Theme
W, H = 680, 770

BLACK = (12, 16, 20)
WHITE = (245, 248, 250)

# Exact requested token base colours
RED_BASE = (255, 0, 0)       
GREEN_BASE = (0, 128, 0)     

# UI accents
BG_FILL = (22, 30, 34)
TEXT_PRIMARY = (247, 250, 252)
TEXT_SECONDARY = (216, 225, 230)

PANEL_DARK = (13, 20, 25, 195)
PANEL_SOFT = (18, 28, 34, 165)
SHADOW = (0, 0, 0, 88)

BOARD_LINE = (13, 18, 20)
BOARD_RING = (22, 164, 102)
BOARD_OUTER_LIGHT = (219, 255, 231)
BOARD_PULP = (241, 76, 108)
BOARD_PULP_LIGHT = (255, 124, 147)
SEED = (38, 38, 38)

EMPTY_FILL = (229, 237, 242)
EMPTY_OUTLINE = (118, 132, 140)

GOLD = (255, 205, 70)

BTN_IDLE = (32, 44, 52)
BTN_BORDER = (122, 150, 165)
BTN_RED = (180, 36, 36)
BTN_GREEN = (18, 120, 60)
BTN_START = (20, 138, 72)
BTN_START_OFF = (66, 83, 94)

LINE_W = 7
NODE_R = 16
CLICK_R = 26

CX, CY = W // 2, H // 2 - 8   # 340, 377

Ro = 230
Ri = 74
ALPHA = 19


# Geometry
def oc(deg):
    a = math.radians(deg - 90)
    return (CX + Ro * math.cos(a), CY + Ro * math.sin(a))


def make_bump(deg1, deg2):
    p1 = oc(deg1)
    p2 = oc(deg2)
    bcx = (p1[0] + p2[0]) / 2
    bcy = (p1[1] + p2[1]) / 2
    br = math.hypot(p1[0] - p2[0], p1[1] - p2[1]) / 2
    dx, dy = CX - bcx, CY - bcy
    d = math.hypot(dx, dy)
    apex = (bcx + dx / d * br, bcy + dy / d * br)
    return p1, p2, bcx, bcy, br, apex


N01, N03, TBcx, TBcy, TBr, top_apex = make_bump(360 - ALPHA, ALPHA)
N23, N21, BBcx, BBcy, BBr, bot_apex = make_bump(180 - ALPHA, 180 + ALPHA)
N20, N00, LBcx, LBcy, LBr, lft_apex = make_bump(270 - ALPHA, 270 + ALPHA)
N04, N24, RBcx, RBcy, RBr, rgt_apex = make_bump(90 - ALPHA, 90 + ALPHA)


def ch_int(cx, cy, r, y):
    dy = abs(y - cy)
    if dy > r:
        return []
    h = math.sqrt(r * r - dy * dy)
    return [(cx - h, y), (cx + h, y)]


N02 = (float(CX), float(CY - Ro))
N22 = (float(CX), float(CY + Ro))
N10 = (float(CX - Ro), float(CY))
N16 = (float(CX + Ro), float(CY))
N05 = top_apex
N25 = bot_apex
N11 = lft_apex
N15 = rgt_apex
N06 = (float(CX), float(CY - Ri))
N26 = (float(CX), float(CY + Ri))
_ic = sorted(ch_int(CX, CY, Ri, CY), key=lambda p: p[0])
N12, N14 = _ic[0], _ic[1]
N13 = (float(CX), float(CY))

NODE_POS = {
    (0, 0): N00, (0, 1): N01, (0, 2): N02, (0, 3): N03, (0, 4): N04,
    (0, 5): N05, (0, 6): N06,
    (1, 0): N10, (1, 1): N11, (1, 2): N12, (1, 3): N13, (1, 4): N14,
    (1, 5): N15, (1, 6): N16,
    (2, 0): N20, (2, 1): N21, (2, 2): N22, (2, 3): N23, (2, 4): N24,
    (2, 5): N25, (2, 6): N26,
}


# Assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_PATH = os.path.join(BASE_DIR, "assets", "watermelon_ui_bg.png")


def load_background():
    surf = pygame.Surface((W, H))
    surf.fill(BG_FILL)

    try:
        img = pygame.image.load(BG_PATH).convert()
        iw, ih = img.get_size()

        scale = min(W / iw, H / ih)
        nw, nh = int(iw * scale), int(ih * scale)
        scaled = pygame.transform.smoothscale(img, (nw, nh))

        surf.blit(scaled, ((W - nw) // 2, (H - nh) // 2))
    except pygame.error:
        pass

    return surf


# Helpers
def ipt(p):
    return (int(round(p[0])), int(round(p[1])))


def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def make_panel(size, color, radius=24, outline=None, outline_w=2):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surf, color, surf.get_rect(), border_radius=radius)
    if outline is not None:
        pygame.draw.rect(surf, outline, surf.get_rect(), outline_w, border_radius=radius)
    return surf


def blit_shadowed_panel(screen, rect, color, radius=24, outline=None, offset=(6, 8)):
    shadow = make_panel((rect.w, rect.h), SHADOW, radius)
    screen.blit(shadow, (rect.x + offset[0], rect.y + offset[1]))
    panel = make_panel((rect.w, rect.h), color, radius, outline=outline)
    screen.blit(panel, rect.topleft)


def draw_arc(surf, bcx, bcy, br, p1, p2, apex, color=BOARD_LINE, width=LINE_W):
    def ang(p):
        return math.atan2(-(p[1] - bcy), p[0] - bcx)

    def norm(a):
        return a % (2 * math.pi)

    a1, a2, am = ang(p1), ang(p2), ang(apex)
    na1, na2, nm = norm(a1), norm(a2), norm(am)
    span = norm(na2 - na1)
    pos = norm(nm - na1)
    start, stop = (na1, na2) if pos < span else (na2, na1)
    if stop < start:
        stop += 2 * math.pi

    steps = max(32, int(abs(stop - start) * br))
    points = []
    for i in range(steps + 1):
        t = start + (stop - start) * i / steps
        px = int(bcx + br * math.cos(t))
        py = int(bcy - br * math.sin(t))
        points.append((px, py))

    if len(points) >= 2:
        pygame.draw.lines(surf, color, False, points, width)


def nearest_node(mx, my):
    best, best_d = None, CLICK_R
    for pos, (px, py) in NODE_POS.items():
        d = math.hypot(mx - px, my - py)
        if d < best_d:
            best, best_d = pos, d
    return best


# Drawing
def draw_background(screen, background):
    screen.blit(background, (0, 0))

    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((7, 14, 20, 72))
    screen.blit(overlay, (0, 0))


def draw_board_base(surf):
    board_shadow = pygame.Surface((W, H), pygame.SRCALPHA)
    for rad in (Ro + 24, Ro + 18, Ro + 12):
        pygame.draw.circle(board_shadow, (0, 0, 0, 18), (CX + 2, CY + 7), rad, 12)
    surf.blit(board_shadow, (0, 0))

    pygame.draw.circle(surf, BOARD_RING, (CX, CY), Ro + 17)
    pygame.draw.circle(surf, BOARD_OUTER_LIGHT, (CX, CY), Ro + 7)
    pygame.draw.circle(surf, BOARD_PULP, (CX, CY), Ro - 1)
    pygame.draw.circle(surf, BOARD_PULP_LIGHT, (CX, CY), Ro - 13)
    pygame.draw.circle(surf, BOARD_PULP, (CX, CY), Ro - 24)

    # subtle seed marks
    for ang in range(0, 360, 24):
        a = math.radians(ang)
        r = Ro - 62 if ang % 48 == 0 else Ro - 98
        x = int(CX + r * math.cos(a))
        y = int(CY + r * math.sin(a))
        pygame.draw.ellipse(surf, SEED, (x - 4, y - 2, 8, 4))

    pygame.draw.circle(surf, BOARD_LINE, (CX, CY), Ro, LINE_W)
    pygame.draw.circle(surf, BOARD_LINE, (CX, CY), Ri, LINE_W)
    pygame.draw.line(surf, BOARD_LINE, ipt(N10), ipt(N16), LINE_W)
    pygame.draw.line(surf, BOARD_LINE, ipt(N02), ipt(N22), LINE_W)
    draw_arc(surf, TBcx, TBcy, TBr, N01, N03, top_apex)
    draw_arc(surf, BBcx, BBcy, BBr, N21, N23, bot_apex)
    draw_arc(surf, LBcx, LBcy, LBr, N00, N20, lft_apex)
    draw_arc(surf, RBcx, RBcy, RBr, N04, N24, rgt_apex)


def draw_token(
    surf, x, y, val,
    selected=False,
    valid_dest=False,
    last_moved=False,
    last_moved_from=False,
    trapped_flash=False,
    ticks=0,
):
    pulse = (math.sin(ticks * 0.006) + 1) / 2

    if trapped_flash and val == 0:
        gr = NODE_R + 5 + int(pulse * 7)
        gs = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (200, 45, 45, int(160 + pulse * 90)), (gr, gr), gr)
        surf.blit(gs, (x - gr, y - gr))

    if selected:
        pygame.draw.circle(surf, GOLD, (x, y), NODE_R + 13)
        pygame.draw.circle(surf, WHITE, (x, y), NODE_R + 9, 2)

    if val == 0:
        if valid_dest:
            r = 8 + int(pulse * 3)
            pygame.draw.circle(surf,(255, 165, 0), (x, y), r)
        return  # empty node — no token circle

    # token shadow
    pygame.draw.circle(surf, (18, 18, 18), (x + 2, y + 3), NODE_R + 4)

    # different outer border by piece type
    if val == 1:
        border_color = (0, 100, 0)      # darker green border
    else:
        border_color = (140, 0, 0)      # darker red border

    pygame.draw.circle(surf, border_color, (x, y), NODE_R + 4)

    if val == 1:
        green_dark = GREEN_BASE
        green_ring = lerp(GREEN_BASE, (255, 255, 255), 0.72)

        pygame.draw.circle(surf, green_dark, (x, y), NODE_R)
        pygame.draw.circle(surf, green_ring, (x, y), NODE_R - 4, 2)

    elif val == -1:
        red_dark = RED_BASE
        red_ring = lerp(RED_BASE, (255, 255, 255), 0.72)

        pygame.draw.circle(surf, red_dark, (x, y), NODE_R)
        pygame.draw.circle(surf, red_ring, (x, y), NODE_R - 4, 2)

    # empty nodes: no circle drawn — just a line intersection point

    if last_moved and val != 0:
        rr = NODE_R + 8 + int(pulse * 5)
        glow = pygame.Surface((rr * 2 + 8, rr * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 168, 40, int(130 + pulse * 90)), (rr + 4, rr + 4), rr, 4)
        surf.blit(glow, (x - rr - 4, y - rr - 4))

    if last_moved_from:
        rr = NODE_R + 8 + int(pulse * 5)
        glow = pygame.Surface((rr * 2 + 8, rr * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(glow, (60, 220, 100, int(130 + pulse * 90)), (rr + 4, rr + 4), rr, 4)
        surf.blit(glow, (x - rr - 4, y - rr - 4))

def draw_status_panel(surf, state, ft, fs, thinking=False):
    board = state.board
    red_n = sum(board[r][c] == -1 for r in range(3) for c in range(7))
    green_n = sum(board[r][c] == 1 for r in range(3) for c in range(7))

    turn_color = RED_BASE if state.player == -1 else GREEN_BASE
    turn_label = ("RED" if state.player == -1 else "GREEN") + "'s TURN"
    if thinking:
        turn_label += "  •  thinking..."

    t1 = ft.render(turn_label, True, turn_color)
    t2 = ft.render(f"Red: {red_n}   •   Green: {green_n}", True, BLACK)
    t3 = ft.render("Click token → move   •   R = setup   •   ESC = quit", True, BLACK)

    # align left edge of t3 (hint line), stack t2+t1 row above it
    x0 = CX - t3.get_width() // 2
    row1_y = H - 113
    surf.blit(t2, (x0, row1_y))
    surf.blit(t1, (x0 + t2.get_width() + 32, row1_y))
    surf.blit(t3, (x0, H - 83))


def draw_header(screen, title_font, sub_font):
    title = title_font.render("Watermelon Chess", True, TEXT_PRIMARY)
    screen.blit(title, (CX - title.get_width() // 2, 42))

def draw_board(
    screen,
    background,
    state,
    selected,
    valid_dests,
    ft,
    fs,
    title_font,
    thinking=False,
    last_moved_to=None,
    last_moved_from=None,
    trapped_cells=None,
):
    trapped_cells = trapped_cells or set()
    ticks = pygame.time.get_ticks()

    draw_background(screen, background)
    draw_header(screen, title_font, fs)
    draw_board_base(screen)

    for (r, c), pos in NODE_POS.items():
        x, y = ipt(pos)
        draw_token(
            screen,
            x,
            y,
            state.board[r][c],
            selected=(selected == (r, c)),
            valid_dest=((r, c) in valid_dests),
            last_moved=(last_moved_to == (r, c)),
            last_moved_from=((r, c) == last_moved_from),
            trapped_flash=((r, c) in trapped_cells),
            ticks=ticks,
        )

    draw_status_panel(screen, state, ft, fs, thinking)


def draw_game_over(screen, winner, ft, fL, fs):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 156))
    screen.blit(overlay, (0, 0))

    if winner == 1:
        msg, col = "GREEN WINS!", GREEN_BASE
    elif winner == -1:
        msg, col = "RED WINS!", RED_BASE
    else:
        msg, col = "DRAW!", GOLD

    card = pygame.Rect(100, H // 2 - 96, W - 200, 190)
    blit_shadowed_panel(screen, card, PANEL_DARK, radius=26, outline=(255, 255, 255, 36))

    t1 = fL.render(msg, True, col)
    t2 = ft.render("Press R to return to setup", True, TEXT_PRIMARY)
    t3 = fs.render("Press ESC to quit", True, TEXT_SECONDARY)

    screen.blit(t1, (CX - t1.get_width() // 2, card.y + 28))
    screen.blit(t2, (CX - t2.get_width() // 2, card.y + 112))
    screen.blit(t3, (CX - t3.get_width() // 2, card.y + 148))


# Setup Screen
HUMAN = "Human"
MM_AI = "Minimax"
MC_AI = "Monte Carlo"

P_TYPES = [HUMAN, MM_AI, MC_AI]
AI_FUNC = {
    MM_AI: minimax,
    MC_AI: monte_carlo,
}

BTN_W, BTN_H = 188, 46

def btn_rect(col, row):
    x = 68 if col == 0 else 424
    y = 292 + row * 62
    return pygame.Rect(x, y, BTN_W, BTN_H)


START_RECT = pygame.Rect(W // 2 - 94, 500, 188, 48)


def draw_setup(screen, background, choices, ft, fT, fs):
    draw_background(screen, background)

    hero = pygame.Rect(44, 100, W - 88, 100)
    blit_shadowed_panel(screen, hero, PANEL_SOFT, radius=24, outline=(255, 255, 255, 34))

    title = fT.render("Watermelon Chess", True, TEXT_PRIMARY)
    screen.blit(title, (CX - title.get_width() // 2, 114))

    # Left panel: x=22, w=280  /  Right panel: x=W-302=378, w=280
    left  = pygame.Rect(22,  238, 280, 240)
    right = pygame.Rect(W - 302, 238, 280, 240)

    blit_shadowed_panel(screen, left,  PANEL_DARK, radius=22, outline=(255, 255, 255, 24))
    blit_shadowed_panel(screen, right, PANEL_DARK, radius=22, outline=(255, 255, 255, 24))

    th_r = ft.render("Player 1  •  Red",   True, RED_BASE)
    th_g = ft.render("Player 2  •  Green", True, GREEN_BASE)

    screen.blit(th_r, (left.centerx  - th_r.get_width() // 2, left.y  + 14))
    screen.blit(th_g, (right.centerx - th_g.get_width() // 2, right.y + 14))

    for col, player in enumerate([-1, 1]):
        sel = choices[player]
        active_color = BTN_RED if player == -1 else BTN_GREEN
        for row, ptype in enumerate(P_TYPES):
            rect  = btn_rect(col, row)
            color = active_color if sel == ptype else BTN_IDLE
            pygame.draw.rect(screen, color,      rect, border_radius=12)
            pygame.draw.rect(screen, BTN_BORDER, rect, 2, border_radius=12)
            txt = ft.render(ptype, True, TEXT_PRIMARY)
            screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                               rect.centery - txt.get_height() // 2))

    # Start button 
    ready = all(v is not None for v in choices.values())
    pygame.draw.rect(screen, BTN_START if ready else BTN_START_OFF,
                     START_RECT, border_radius=14)
    pygame.draw.rect(screen, BTN_BORDER, START_RECT, 2, border_radius=14)
    st = ft.render("Start Game", True, TEXT_PRIMARY if ready else (150, 165, 175))
    screen.blit(st, (START_RECT.centerx - st.get_width()  // 2,
                     START_RECT.centery - st.get_height() // 2))


# Main
def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Watermelon Chess")

    background = load_background()

    ft = pygame.font.SysFont("segoeui", 22, bold=True)
    fs = pygame.font.SysFont("segoeui", 17)
    fT = pygame.font.SysFont("segoeui", 38, bold=True)
    fL = pygame.font.SysFont("segoeui", 50, bold=True)

    clock = pygame.time.Clock()

    SETUP_SCR = "setup"
    PLAY_SCR = "playing"
    OVER_SCR = "over"

    mode = SETUP_SCR
    choices = {-1: None, 1: None}

    state = None
    selected = None
    valid_dests = set()
    legal = set()
    winner = None
    ai_turn = False
    last_moved_to = None
    last_moved_from = None
    trapped_cells = set()

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if ev.key == pygame.K_r:
                    mode = SETUP_SCR
                    choices = {-1: None, 1: None}
                    selected = None
                    valid_dests = set()
                    legal = set()
                    winner = None
                    ai_turn = False
                    last_moved_to = None
                    last_moved_from = None
                    trapped_cells = set()

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos

                if mode == SETUP_SCR:
                    for col, player in enumerate([-1, 1]):
                        for row, ptype in enumerate(P_TYPES):
                            if btn_rect(col, row).collidepoint(mx, my):
                                choices[player] = ptype

                    if START_RECT.collidepoint(mx, my) and all(v is not None for v in choices.values()):
                        state = State()
                        selected = None
                        valid_dests = set()
                        winner = None
                        legal = actions(state)
                        ai_turn = choices[state.player] != HUMAN
                        last_moved_to = None
                        last_moved_from = None
                        trapped_cells = set()
                        mode = PLAY_SCR

                elif mode == PLAY_SCR and not ai_turn:
                    if choices[state.player] == HUMAN:
                        clicked = nearest_node(mx, my)

                        if clicked is None:
                            selected = None
                            valid_dests = set()

                        elif selected is None:
                            r, c = clicked
                            if state.board[r][c] == state.player:
                                frm = {a for a in legal if a[0] == clicked}
                                if frm:
                                    selected = clicked
                                    valid_dests = {a[1] for a in frm}

                        elif clicked == selected:
                            selected = None
                            valid_dests = set()

                        elif clicked in valid_dests:
                            action = (selected, clicked)
                            old_state = state
                            state = result(old_state, action)

                            last_moved_from = selected
                            last_moved_to = clicked
                            trapped_cells = {
                                (r, c)
                                for r in range(3)
                                for c in range(7)
                                if old_state.board[r][c] == -old_state.player
                                and state.board[r][c] == 0
                            }

                            selected = None
                            valid_dests = set()
                            legal = actions(state)

                            w = utility(state)
                            if w is not None:
                                winner = w
                                mode = OVER_SCR
                            else:
                                ai_turn = choices[state.player] != HUMAN

                        else:
                            r, c = clicked
                            if state.board[r][c] == state.player:
                                frm = {a for a in legal if a[0] == clicked}
                                if frm:
                                    selected = clicked
                                    valid_dests = {a[1] for a in frm}
                                else:
                                    selected = None
                                    valid_dests = set()
                            else:
                                selected = None
                                valid_dests = set()

        if mode == SETUP_SCR:
            draw_setup(screen, background, choices, ft, fT, fs)

        elif mode == PLAY_SCR:
            if ai_turn:
                draw_board(
                    screen,
                    background,
                    state,
                    None,
                    set(),
                    ft,
                    fs,
                    fT,
                    thinking=True,
                    last_moved_to=last_moved_to,
                    last_moved_from=last_moved_from,
                    trapped_cells=trapped_cells,
                )
                pygame.display.flip()

                ptype = choices[state.player]
                action = AI_FUNC[ptype](state)

                if action:
                    old_state = state
                    state = result(old_state, action)

                    last_moved_from = action[0]
                    last_moved_to = action[1]
                    trapped_cells = {
                        (r, c)
                        for r in range(3)
                        for c in range(7)
                        if old_state.board[r][c] == -old_state.player
                        and state.board[r][c] == 0
                    }

                    legal = actions(state)
                    w = utility(state)

                    if w is not None:
                        winner = w
                        mode = OVER_SCR
                        ai_turn = False
                    else:
                        ai_turn = choices[state.player] != HUMAN
                else:
                    winner = utility(state) or 0
                    mode = OVER_SCR
                    ai_turn = False
            else:
                draw_board(
                    screen,
                    background,
                    state,
                    selected,
                    valid_dests,
                    ft,
                    fs,
                    fT,
                    thinking=False,
                    last_moved_to=last_moved_to,
                    last_moved_from=last_moved_from,
                    trapped_cells=trapped_cells,
                )

        elif mode == OVER_SCR:
            draw_board(screen, background, state, None, set(), ft, fs, fT)
            draw_game_over(screen, winner, ft, fL, fs)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()