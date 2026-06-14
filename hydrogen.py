import pygame
import random
import sys
import os
import math
from PIL import ImageGrab

# Configuration
FPS = 60
PHASE_DURATION = 7000  # 7 seconds per visual phase
DOUBLE_CLICK_TIME = 500  # Milliseconds allowed between clicks
SURFACE_UPDATE_INTERVAL = 120  # Frames between work_surface updates
MELT_STRIPS = 15  # Number of strips in melt effect
CHAOS_EFFECT_THRESHOLD = 0.60  # Probability threshold for chaos effects

# Color Palette
COLORS = {
    'bg': (240, 240, 240),
    'border': (30, 144, 255),
    'accent': (255, 69, 0),
    'text': (255, 255, 255),
    'text_shadow': (0, 0, 0, 150),
    'grid': (100, 100, 100)
}

class FullHydrogenSimulation:
    def __init__(self):
        try:
            pygame.init()
        except Exception as e:
            print(f"Failed to initialize Pygame: {e}")
            sys.exit(1)
        
        # 1. Capture the exact state of the desktop
        try:
            self.screenshot = ImageGrab.grab(all_screens=True)
        except Exception as e:
            print(f"Failed to capture screen: {e}")
            sys.exit(1)
        
        # 2. Get display dimensions
        self.info = pygame.display.Info()
        self.width = self.info.current_w
        self.height = self.info.current_h
        
        # 3. Create a borderless, full-screen overlay
        os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        pygame.display.set_caption("Hydrogen Full Simulation")
        
        # 4. Convert desktop capture to Pygame surface
        try:
            self.bg_surface = pygame.image.fromstring(
                self.screenshot.tobytes(), self.screenshot.size, self.screenshot.mode
            ).convert()
        except Exception as e:
            print(f"Failed to convert screenshot to surface: {e}")
            sys.exit(1)
        
        self.work_surface = self.bg_surface.copy()
        
        # Animation & Timing variables
        self.clock = pygame.time.Clock()
        self.running = True
        self.frame_count = 0
        self.start_ticks = 0
        
        # State Management
        # "desktop" = waiting for double click | "payload" = running the glitch effects
        self.state = "desktop" 
        self.last_click_time = 0
        
        # Icon Configuration (Positioned at top-left with padding)
        self.icon_rect = pygame.Rect(40, 40, 70, 70)
        self.font = pygame.font.SysFont("arial", 14, bold=True)
        
        # Movement offsets
        self.scroll_x = 0
        self.scroll_y = 0
        
        # Phase tracking
        self.phases = ["scroll", "melt", "tunnel", "wave", "chaos", "calm_flash"]
        
        # Calm flashing lights configuration
        self.flash_cycle = 0
        self.soft_colors = [
            (100, 150, 200, 100),  # Soft blue
            (150, 100, 200, 100),  # Soft purple
            (200, 150, 100, 100),  # Soft orange
            (100, 200, 150, 100),  # Soft cyan
        ]
        self.intense_colors = [
            (255, 150, 0, 180),    # Bright orange
            (150, 0, 255, 180),    # Bright purple
            (0, 200, 255, 180),    # Bright cyan
            (255, 0, 150, 180),    # Bright pink
        ]

    def get_current_phase(self, current_time):
        """Calculates which phase the simulation should be in based on elapsed time since payload started."""
        idx = (current_time // PHASE_DURATION) % len(self.phases)
        return self.phases[idx]

    def draw_desktop_icon(self):
        """Renders the fake 'hydrogen' app icon over the desktop capture."""
        # Draw the base clean desktop
        self.screen.blit(self.bg_surface, (0, 0))
        
        # Draw a generic "executable" style icon box
        pygame.draw.rect(self.screen, COLORS['bg'], self.icon_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['border'], self.icon_rect, 3, border_radius=8)
        
        # Draw a little internal symbol (atom/hydrogen design placeholder)
        pygame.draw.circle(self.screen, COLORS['accent'], (self.icon_rect.centerx, self.icon_rect.centery - 5), 10)
        pygame.draw.circle(self.screen, COLORS['border'], (self.icon_rect.centerx + 12, self.icon_rect.centery + 8), 5)
        pygame.draw.line(self.screen, COLORS['grid'], (self.icon_rect.centerx, self.icon_rect.centery - 5), (self.icon_rect.centerx + 12, self.icon_rect.centery + 8), 2)

        # Render Text Label underneath the icon
        text_surf = self.font.render("hydrogen", True, COLORS['text'])
        
        # Create a tiny text drop-shadow container for visibility against light backgrounds
        text_bg = pygame.Surface((text_surf.get_width() + 10, text_surf.get_height() + 4), pygame.SRCALPHA)
        text_bg.fill(COLORS['text_shadow']) 
        
        bg_x = self.icon_rect.centerx - (text_bg.get_width() // 2)
        bg_y = self.icon_rect.bottom + 8
        
        self.screen.blit(text_bg, (bg_x, bg_y))
        self.screen.blit(text_surf, (bg_x + 5, bg_y + 2))

    # --- VISUAL PAYLOAD METHODS ---
    def effect_scroll(self):
        """Creates a scrolling/tiling distortion effect."""
        self.scroll_x = (self.scroll_x + 4) % self.width
        self.scroll_y = (self.scroll_y + 2) % self.height
        self.screen.blit(self.work_surface, (self.scroll_x, self.scroll_y))
        self.screen.blit(self.work_surface, (self.scroll_x - self.width, self.scroll_y))
        self.screen.blit(self.work_surface, (self.scroll_x, self.scroll_y - self.height))
        self.screen.blit(self.work_surface, (self.scroll_x - self.width, self.scroll_y - self.height))
        
        # Add subtle calm flash overlay
        self._add_calm_flash_overlay(intensity=0.3)

    def effect_melt(self):
        """Creates a melting/dripping distortion effect by vertically displacing random strips."""
        self.screen.blit(self.bg_surface, (0, 0))
        for _ in range(MELT_STRIPS):
            strip_w = random.randint(10, 40)
            strip_h = self.height
            strip_x = random.randint(0, max(1, self.width - strip_w))
            strip_y_offset = random.randint(2, 8)
            slice_surf = pygame.Surface((strip_w, strip_h))
            slice_surf.blit(self.bg_surface, (0, 0), (strip_x, 0, strip_w, strip_h))
            self.screen.blit(slice_surf, (strip_x, strip_y_offset))
        
        # Add subtle calm flash overlay
        self._add_calm_flash_overlay(intensity=0.35)

    def effect_tunnel(self):
        """Creates a tunnel/vortex effect with shrinking and subtle rotation."""
        scale_factor = 0.98
        new_w = int(self.width * scale_factor)
        new_h = int(self.height * scale_factor)
        shrunk_surf = pygame.transform.smoothscale(self.screen, (new_w, new_h))
        if self.frame_count % 3 == 0:
            shrunk_surf = pygame.transform.rotate(shrunk_surf, random.choice([-2, -1, 1, 2]))
            new_w, new_h = shrunk_surf.get_size()
        x_pos = (self.width - new_w) // 2
        y_pos = (self.height - new_h) // 2
        temp_surface = self.bg_surface.copy()
        temp_surface.blit(shrunk_surf, (x_pos, y_pos))
        self.screen.blit(temp_surface, (0, 0))
        
        # Add subtle calm flash overlay
        self._add_calm_flash_overlay(intensity=0.25)

    def effect_wave(self):
        """Creates a sinusoidal wave distortion effect across horizontal rows."""
        self.screen.fill((0, 0, 0))
        amplitude = 25
        frequency = 0.05
        speed = 0.2
        row_height = 4
        for y in range(0, self.height, row_height):
            offset_x = int(amplitude * math.sin(frequency * y + self.frame_count * speed))
            self.screen.blit(self.bg_surface, (offset_x, y), (0, y, self.width, row_height))
        
        # Add subtle calm flash overlay
        self._add_calm_flash_overlay(intensity=0.4)

    def effect_chaos(self):
        """Combines multiple effects randomly: scrolling, inverted color glitches, and displacement.
        Also adds intense flashing lights for a more dramatic effect."""
        if random.random() > 0.5:
            self.effect_scroll()
        else:
            self.screen.blit(self.bg_surface, (0, 0))
            
        if random.random() > CHAOS_EFFECT_THRESHOLD:
            rect_w = random.randint(100, 500)
            rect_h = random.randint(100, 400)
            rect_x = random.randint(0, max(1, self.width - rect_w))
            rect_y = random.randint(0, max(1, self.height - rect_h))
            
            # Validate bounds before subsurface operation
            if rect_x + rect_w <= self.width and rect_y + rect_h <= self.height:
                glitch_slice = self.screen.subsurface((rect_x, rect_y, rect_w, rect_h)).copy()
                inv_mask = pygame.Surface((rect_w, rect_h))
                inv_mask.fill((255, 255, 255))
                glitch_slice.blit(inv_mask, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
                self.screen.blit(glitch_slice, (rect_x + random.randint(-50, 50), rect_y + random.randint(-10, 10)))
        
        # Add intense flashing lights overlay on top of chaos effects
        self.draw_intense_flash_overlay()

    def effect_calm_flash(self):
        """Creates gentle, safe flashing lights (2 Hz, low contrast, soft colors) that won't trigger photosensitive epilepsy.
        Uses muted colors with fade transitions and localized light orbs."""
        self.screen.blit(self.bg_surface, (0, 0))
        self.flash_cycle = (self.flash_cycle + 1) % 30  # 30 frames = 2 Hz at 60 FPS
        
        # Calculate alpha for smooth fade in/out (sine wave between 80-200 alpha for visibility)
        alpha_intensity = int(80 + 70 * math.sin(self.flash_cycle * math.pi / 15))
        
        # Draw 5-6 gentle pulsing light orbs at fixed positions for stability
        positions = [
            (self.width * 0.2, self.height * 0.2),
            (self.width * 0.8, self.height * 0.2),
            (self.width * 0.5, self.height * 0.5),
            (self.width * 0.2, self.height * 0.8),
            (self.width * 0.8, self.height * 0.8),
        ]
        
        for i, (pos_x, pos_y) in enumerate(positions):
            light_size = 60 + random.randint(20, 50)
            
            # Pick a soft color from palette, cycling through
            color_idx = (i + (self.frame_count // 15)) % len(self.soft_colors)
            soft_color = self.soft_colors[color_idx]
            
            # Create semi-transparent surface for the light glow
            glow_surface = pygame.Surface((light_size * 2, light_size * 2), pygame.SRCALPHA)
            
            # Draw gradient-like glow circles with more layers for visibility
            for radius in range(light_size, 0, -2):
                alpha = int((alpha_intensity * (light_size - radius)) / light_size)
                glow_color = (*soft_color[:3], alpha)
                pygame.draw.circle(glow_surface, glow_color, (light_size, light_size), radius)
            
            # Blit the glow onto screen
            self.screen.blit(glow_surface, (int(pos_x - light_size), int(pos_y - light_size)))

    def draw_intense_flash_overlay(self):
        """Draws high-contrast flashing overlay for chaos effect (safe but intense)."""
        # Faster flash cycle for chaos (4 Hz)
        flash_frame = (self.frame_count % 15)
        
        # Create on/off flashing with fade
        if flash_frame < 7:
            alpha = int(150 * (flash_frame / 7))  # Fade in
        else:
            alpha = int(150 * ((15 - flash_frame) / 8))  # Fade out
        
        if alpha > 0:
            # Draw bright flashes at corners and center
            flash_positions = [
                (0, 0, self.width // 3, self.height // 3),
                (self.width - self.width // 3, 0, self.width // 3, self.height // 3),
                (self.width // 3, self.height - self.height // 3, self.width // 3, self.height // 3),
                (self.width // 2 - 100, self.height // 2 - 100, 200, 200),
            ]
            
            color_idx = (self.frame_count // 5) % len(self.intense_colors)
            intense_color = self.intense_colors[color_idx]
            
            for x, y, w, h in flash_positions:
                flash_surface = pygame.Surface((w, h), pygame.SRCALPHA)
                flash_surface.fill((*intense_color[:3], alpha))
                self.screen.blit(flash_surface, (x, y))

    def _add_calm_flash_overlay(self, intensity=0.5):
        """Adds a subtle calm flashing overlay to the current screen.
        intensity: value from 0.0 (invisible) to 1.0 (fully visible)"""
        self.flash_cycle = (self.flash_cycle + 1) % 30
        
        # Calculate alpha for smooth fade
        base_alpha = int(100 * intensity)
        alpha_intensity = int(base_alpha * (0.5 + 0.5 * math.sin(self.flash_cycle * math.pi / 15)))
        
        if alpha_intensity > 0:
            color_idx = (self.frame_count // 15) % len(self.soft_colors)
            soft_color = self.soft_colors[color_idx]
            
            # Create full-screen subtle flash
            flash_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash_surface.fill((*soft_color[:3], alpha_intensity))
            self.screen.blit(flash_surface, (0, 0))

    def run(self):
        while self.running:
            current_ticks = pygame.time.get_ticks()
            self.frame_count += 1
            
            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
                
                # Double Click Detection (Only active on desktop state)
                if self.state == "desktop" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.icon_rect.collidepoint(event.pos):
                        time_since_last_click = current_ticks - self.last_click_time
                        
                        if time_since_last_click < DOUBLE_CLICK_TIME:
                            # DOUBLE CLICK CONFIRMED: Reset timeline and launch payload
                            self.state = "payload"
                            self.start_ticks = pygame.time.get_ticks()
                        else:
                            # First click registered
                            self.last_click_time = current_ticks

            # --- Engine State Update Loop ---
            if self.state == "desktop":
                self.draw_desktop_icon()
            
            elif self.state == "payload":
                elapsed = current_ticks - self.start_ticks
                phase = self.get_current_phase(elapsed)
                
                if phase == "scroll":
                    self.effect_scroll()
                elif phase == "melt":
                    self.effect_melt()
                elif phase == "tunnel":
                    self.effect_tunnel()
                elif phase == "wave":
                    self.effect_wave()
                elif phase == "chaos":
                    self.effect_chaos()
                elif phase == "calm_flash":
                    self.effect_calm_flash()
                    
                # Sync updates back into baseline surface tracker
                if self.frame_count % SURFACE_UPDATE_INTERVAL == 0 and phase not in ["tunnel", "calm_flash"]:
                    self.work_surface.blit(self.screen, (0, 0))
                
            pygame.display.flip()
            self.clock.tick(FPS)
            
        self.cleanup()
    
    def cleanup(self):
        """Properly dispose of resources and exit."""
        try:
            pygame.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            sys.exit()

if __name__ == "__main__":
    # 1.5-second buffer window to allow user to minimize IDE
    pygame.time.wait(1500)
    
    sim = FullHydrogenSimulation()
    sim.run()