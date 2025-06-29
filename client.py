import pygame
import socket
import pickle
import threading
import time
import ssl
import random
import math

WIDTH, HEIGHT = 800, 600
CAR_WIDTH, CAR_HEIGHT = 40, 60
BASE_VEL = 5
TRACK_WIDTH = 160
COIN_RADIUS = 10
TOTAL_COINS = 20
NITRO_DURATION_MS = 5000
OBSTACLE_COUNT = 10
OBSTACLE_WIDTH = TRACK_WIDTH // 3

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.check_hostname = False
context.verify_mode = ssl.CERT_REQUIRED
context.load_verify_locations(cafile='cert.pem')
raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_sock = context.wrap_socket(raw_sock)
ssl_sock.connect(("192.168.1.3", 5555))
player_id, positions, shared_obstacles = pickle.loads(ssl_sock.recv(2048))
print(f"You are Player {player_id + 1}")

pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2 Player Car Racing Game")
font = pygame.font.SysFont(None, 72)
small_font = pygame.font.SysFont(None, 24)

car1 = pygame.image.load("car1.png")
car2 = pygame.image.load("car2.png")
car1 = pygame.transform.scale(car1, (CAR_WIDTH, CAR_HEIGHT))
car2 = pygame.transform.scale(car2, (CAR_WIDTH, CAR_HEIGHT))
cars = [car1, car2]

title_coin = pygame.Surface((COIN_RADIUS*2, COIN_RADIUS*2), pygame.SRCALPHA)
pygame.draw.circle(title_coin, (255, 223, 0), (COIN_RADIUS, COIN_RADIUS), COIN_RADIUS)

class ProfessionalParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice([
            (212, 175, 55),
            (192, 192, 192),
            (176, 224, 230),
            (50, 50, 120),
            (128, 0, 32),
            (34, 139, 34),
            (75, 0, 130),
            (25, 25, 25)
        ])
        self.alpha = 255
        self.shape = random.choice(["diamond", "circle", "sparkle"])
        self.size = random.randint(3, 8)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-7, -3)
        self.gravity = 0.15
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-3, 3)
        self.life = random.randint(60, 120)
        self.original_life = self.life
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.rotation += self.rotation_speed
        self.life -= 1
        self.alpha = int(255 * (self.life / self.original_life))
        self.vx += random.uniform(-0.05, 0.05)
        self.rotation_speed *= 0.98
    
    def draw(self, surface):
        particle_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, self.alpha)
        
        if self.shape == "diamond":
            points = [
                (self.size, 0),
                (self.size*2, self.size),
                (self.size, self.size*2),
                (0, self.size)
            ]
            pygame.draw.polygon(particle_surf, color_with_alpha, points)
        elif self.shape == "circle":
            pygame.draw.circle(particle_surf, color_with_alpha, (self.size, self.size), self.size)
        else:
            length = self.size
            center = (self.size, self.size)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                end_x = center[0] + math.cos(rad) * length
                end_y = center[1] + math.sin(rad) * length
                pygame.draw.line(particle_surf, color_with_alpha, center, (end_x, end_y), 2)
        
        if self.rotation != 0:
            particle_surf = pygame.transform.rotate(particle_surf, self.rotation)
        
        rect = particle_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(particle_surf, rect)

class FireworkShell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 4
        self.color = (255, 250, 240)
        self.trail_color = (200, 200, 150, 120)
        self.trail = []
        self.vel = random.uniform(-14, -10)
        self.gravity = 0.2
        self.wobble = random.uniform(-0.6, 0.6)
        self.exploded = False
        self.particles = []
        self.max_trail_length = 15
        self.glow_radius = 12
        self.glow_color = (255, 255, 200, 30)
    
    def update(self):
        if not self.exploded:
            self.trail.append((self.x, self.y))
            if len(self.trail) > self.max_trail_length:
                self.trail.pop(0)
            
            self.x += self.wobble
            self.y += self.vel
            self.vel += self.gravity
            self.wobble *= 0.95
            
            if self.vel >= -0.7:
                self.explode()
        else:
            for particle in self.particles[:]:
                particle.update()
                if particle.life <= 0:
                    self.particles.remove(particle)
    
    def explode(self):
        self.exploded = True
        color_scheme = random.choice([
            [(212, 175, 55), (255, 215, 0), (184, 134, 11)],
            [(192, 192, 192), (220, 220, 220), (169, 169, 169)],
            [(70, 130, 180), (30, 144, 255), (135, 206, 250)],
            [(255, 0, 0), (178, 34, 34), (220, 20, 60)],
            [(50, 205, 50), (34, 139, 34), (0, 128, 0)],
            [(148, 0, 211), (186, 85, 211), (216, 191, 216)]
        ])
        
        for ring in range(3):
            num_particles = 12 + ring * 8
            for i in range(num_particles):
                angle = (i / num_particles) * 2 * math.pi
                velocity = 2 + ring * 1.5
                
                particle = ProfessionalParticle(self.x, self.y)
                particle.vx = math.cos(angle) * velocity
                particle.vy = math.sin(angle) * velocity
                particle.vx += random.uniform(-0.5, 0.5)
                particle.vy += random.uniform(-0.5, 0.5)
                particle.color = random.choice(color_scheme)
                
                self.particles.append(particle)
        
        for _ in range(15):
            particle = ProfessionalParticle(self.x, self.y)
            particle.shape = "sparkle"
            particle.size = random.randint(4, 10)
            particle.color = (255, 255, 220)
            particle.vx = random.uniform(-3, 3)
            particle.vy = random.uniform(-3, 3)
            self.particles.append(particle)
    
    def draw(self, surface):
        if not self.exploded:
            glow_surf = pygame.Surface((self.glow_radius*2, self.glow_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, self.glow_color, (self.glow_radius, self.glow_radius), self.glow_radius)
            surface.blit(glow_surf, (int(self.x - self.glow_radius), int(self.y - self.glow_radius)))
            
            for i, pos in enumerate(self.trail):
                alpha = int(120 * (i / len(self.trail)))
                trail_color = (*self.trail_color[:3], alpha)
                trail_size = 2 * (i / len(self.trail))
                pygame.draw.circle(surface, trail_color, (int(pos[0]), int(pos[1])), max(1, int(trail_size)))
            
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
        else:
            for particle in self.particles:
                particle.draw(surface)

class ChampagneEffect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.particles = []
        self.active = True
        self.timer = 0
        self.duration = 100
        self.base_color = (247, 231, 206)
    
    def update(self):
        self.timer += 1
        
        if self.timer <= self.duration:
            for _ in range(random.randint(3, 5)):
                angle = random.uniform(-0.5, 0.5)
                speed = random.uniform(3, 6)
                
                particle = ProfessionalParticle(self.x, self.y)
                particle.color = self.get_champagne_color()
                particle.shape = "circle"
                particle.size = random.uniform(1.5, 4)
                particle.vx = math.sin(angle) * speed
                particle.vy = -math.cos(angle) * speed
                self.particles.append(particle)
        
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)
        
        if self.timer > self.duration and len(self.particles) == 0:
            self.active = False
    
    def get_champagne_color(self):
        variation = random.randint(-15, 15)
        r = max(0, min(255, self.base_color[0] + variation))
        g = max(0, min(255, self.base_color[1] + variation))
        b = max(0, min(255, self.base_color[2]))
        return (r, g, b)
    
    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)

def generate_track_layout():
    layout = []
    for _ in range(60):
        offset = random.choice([-1, 0, 1]) * 40
        layout.append(offset)
    return layout
track_layout = generate_track_layout()
full_track_height = len(track_layout) * 120
track_surface = pygame.Surface((WIDTH, full_track_height))

coin_positions = [[], []]
obstacles = []
obs_segments = random.sample(range(len(track_layout)//2, len(track_layout)), OBSTACLE_COUNT)
for i, offset in enumerate(track_layout):
    base_y = full_track_height - (i + 1) * 120
    centers = [WIDTH//3 + offset, 2*WIDTH//3 + offset]
    for cx in centers:
        pygame.draw.rect(track_surface, (50,50,50), (cx - TRACK_WIDTH//2, base_y, TRACK_WIDTH, 120))
        for y in range(base_y, base_y+120, 30):
            pygame.draw.line(track_surface, (255,255,255), (cx, y), (cx, y+10), 4)
    for x in range(0, WIDTH, 20):
        if all(not (cx - TRACK_WIDTH//2 <= x < cx + TRACK_WIDTH//2) for cx in centers):
            for y in range(base_y, base_y+120, 20):
                shade = random.randint(90,140)
                pygame.draw.rect(track_surface, (0,shade,0), (x, y, 20, 20))
    if i < TOTAL_COINS:
        for pid, cx in enumerate(centers):
            coin_x = cx + random.randint(-TRACK_WIDTH//3, TRACK_WIDTH//3) - COIN_RADIUS
            coin_y = base_y + random.randint(20,100)
            coin_positions[pid].append(pygame.Rect(coin_x, coin_y, COIN_RADIUS*2, COIN_RADIUS*2))
    
    if i in obs_segments:
        for lane_index, cx in enumerate(centers):
            if random.random() < 0.7:
                obstacle_width = TRACK_WIDTH // 4
                
                position_type = random.randint(0, 2)
                
                if position_type == 0:
                    obs_x = cx - TRACK_WIDTH//4 - obstacle_width//2
                elif position_type == 1:
                    obstacle_width = TRACK_WIDTH // 5
                    obs_x = cx - obstacle_width//2
                else:
                    obs_x = cx + TRACK_WIDTH//4 - obstacle_width//2
                
                obs_y = base_y + random.randint(20, 80)
                
                obstacles.append(pygame.Rect(obs_x, obs_y, obstacle_width, 25))

finish_line_y = 50
for cx in [WIDTH//3, 2*WIDTH//3]:
    pygame.draw.rect(track_surface, (255,255,0), (cx - TRACK_WIDTH//2, finish_line_y, TRACK_WIDTH, 10))

def send_pos(pos):
    try: ssl_sock.sendall(pickle.dumps(pos))
    except: pass

def receive_positions():
    global positions, winner, game_over
    while not game_over:
        try:
            data = ssl_sock.recv(2048)
            if not data: break
            positions, winner = pickle.loads(data)
            if winner: game_over = True
        except: break

winner = None
game_over = False
threading.Thread(target=receive_positions, daemon=True).start()

for c in ["3","2","1"]:
    win.fill((0,0,0))
    t = font.render(c, True, (255,255,255))
    win.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2))
    pygame.display.update()
    time.sleep(1)

start_y = full_track_height - 100
positions[0] = (WIDTH//3 - CAR_WIDTH//2, start_y)
positions[1] = (2*WIDTH//3 - CAR_WIDTH//2, start_y)
scroll_y = full_track_height - HEIGHT
coin_counts = [0,0]
nitro_counts = [0,0]
nitro_active = [False, False]
nitro_end = [0,0]
celebration_effects = []
celebration_timer = 0
celebration_duration = 7
victory_effect_interval = 0.25
last_effect_time = 0

clock = pygame.time.Clock()
while True:
    dt = clock.tick(30)
    now_ms = pygame.time.get_ticks()
    for pid in range(2):
        if nitro_active[pid] and now_ms >= nitro_end[pid]:
            nitro_active[pid] = False
    
    win.blit(track_surface, (0, -scroll_y))
    for pid in range(2):
        for coin in coin_positions[pid]:
            win.blit(title_coin, (coin.x, coin.y - scroll_y))
    for obs in obstacles:
        pygame.draw.rect(win, (139,69,19), (obs.x, obs.y-scroll_y, obs.width, obs.height))
    for i,car in enumerate(cars):
        win.blit(car, (positions[i][0], positions[i][1]-scroll_y))
    for pid in range(2):
        x_pos = 10 if pid==0 else WIDTH-180
        win.blit(small_font.render(f"Coins: {coin_counts[pid]}", True, (255,255,255)), (x_pos,10))
        nitro_counts[pid] = coin_counts[pid] // 5
        win.blit(small_font.render(f"Nitro: {nitro_counts[pid]}", True, (255,255,255)), (x_pos,40))
        if pid==player_id:
            win.blit(small_font.render("Press N for nitro",True,(200,200,200)),(x_pos,70))
        if nitro_active[pid]:
            win.blit(small_font.render("Nitro Mode On",True,(255,0,0)),(x_pos,100))
    
    if game_over and winner:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        win.blit(overlay, (0, 0))
        
        win_text = f"{winner} Wins!"
        
        for offset in range(3, 0, -1):
            t_glow = font.render(win_text, True, (200, 180, 60))
            win.blit(t_glow, (WIDTH//2-t_glow.get_width()//2 + offset, HEIGHT//2 + offset))
            win.blit(t_glow, (WIDTH//2-t_glow.get_width()//2 - offset, HEIGHT//2 - offset))
        
        t = font.render(win_text, True, (255, 255, 255))
        win.blit(t, (WIDTH//2-t.get_width()//2, HEIGHT//2))
        
        if celebration_timer == 0:
            celebration_timer = time.time()
        
        current_time = time.time()
        if current_time - celebration_timer < celebration_duration:
            if current_time - last_effect_time >= victory_effect_interval:
                last_effect_time = current_time
                
                celebration_effects.append(FireworkShell(random.randint(100, WIDTH-100), HEIGHT-20))
                
                if random.random() < 0.3:
                    side = random.choice(["left", "right"])
                    x_pos = 100 if side == "left" else WIDTH - 100
                    celebration_effects.append(ChampagneEffect(x_pos, HEIGHT-20))
            
            for effect in celebration_effects[:]:
                effect.update()
                effect.draw(win)
                
                if hasattr(effect, 'active') and not effect.active:
                    celebration_effects.remove(effect)
                elif hasattr(effect, 'particles') and len(effect.particles) == 0:
                    if hasattr(effect, 'exploded') and effect.exploded:
                        celebration_effects.remove(effect)
        else:
            pygame.quit()
            ssl_sock.close()
            exit()
        
        pygame.display.update()
        continue
    
    pygame.display.update()
    
    keys = pygame.key.get_pressed()
    speed = BASE_VEL * (2 if nitro_active[player_id] else 1)
    x,y = positions[player_id]
    nx,ny = x,y
    if keys[pygame.K_LEFT]: nx -= speed
    if keys[pygame.K_RIGHT]: nx += speed
    if keys[pygame.K_UP]: ny -= speed
    if keys[pygame.K_DOWN]: ny += speed
    if keys[pygame.K_n] and nitro_counts[player_id]>0 and not nitro_active[player_id]:
        nitro_active[player_id] = True
        nitro_end[player_id] = now_ms + NITRO_DURATION_MS
        coin_counts[player_id] -= 5
    nx = max(0,min(nx,WIDTH-CAR_WIDTH))
    ny = max(0,min(ny,full_track_height-CAR_HEIGHT))
    
    seg = (full_track_height - ny)//120
    if seg >= len(track_layout):
        seg = len(track_layout) - 1
    offset = track_layout[seg]
    cx_base = WIDTH//3 if player_id==0 else 2*WIDTH//3
    cx = cx_base + offset
    on_road = cx - TRACK_WIDTH//2 <= nx+CAR_WIDTH//2 <= cx + TRACK_WIDTH//2
    
    new_car_rect = pygame.Rect(nx, ny, CAR_WIDTH, CAR_HEIGHT)
    
    hit_obstacle = False
    for obs in obstacles:
        if new_car_rect.colliderect(obs):
            hit_obstacle = True
            break
    
    if on_road and not hit_obstacle:
        positions[player_id] = (nx, ny)
        send_pos((nx, ny))
    else:
        send_pos((x, y))
    
    car_rect = pygame.Rect(positions[player_id][0], positions[player_id][1], CAR_WIDTH, CAR_HEIGHT)
    for coin in coin_positions[player_id][:]:
        if car_rect.colliderect(coin):
            coin_counts[player_id] += 1
            coin_positions[player_id].remove(coin)
    
    scroll_y = max(0, min(full_track_height-HEIGHT, positions[player_id][1]-HEIGHT//2))
    
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            pygame.quit()
            ssl_sock.close()
            exit()