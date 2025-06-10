import pygame
import math
import random
import os
import sys

pygame.init()

# =======================
# Thiết lập màn hình
# =======================
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Astrocrash")
clock = pygame.time.Clock()
FPS = 60

# =======================
# Đường dẫn tới thư mục assets
# =======================
BASE_PATH = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_PATH, "assets")

def resource_path(relative_path):
    """Hỗ trợ khi đóng gói PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = BASE_PATH
    return os.path.join(base_path, "assets", relative_path)

# =======================
# Thiết lập icon cửa sổ
# =======================
icon = pygame.image.load(resource_path("icon.png"))
pygame.display.set_icon(icon)

# =======================
# Load âm thanh
# =======================
laser_sound = pygame.mixer.Sound(resource_path("laser.ogg"))          # Tiếng bắn tên lửa
boom_sound = pygame.mixer.Sound(resource_path("explosion.ogg"))      # Tiếng nổ khi trúng asteroid
pygame.mixer.music.load(resource_path("music.ogg"))                   # Nhạc nền
pygame.mixer.music.set_volume(0.5)

# =======================
# Load ảnh cho game
# =======================
ship_img = pygame.image.load(resource_path("Character_Spaceship.png")).convert_alpha()
ship_img = pygame.transform.scale(ship_img, (50, 50))  # Đổi kích thước tàu

asteroid_imgs = []
for i in range(1, 5):
    img = pygame.image.load(resource_path(f"alien_{i}.png")).convert_alpha()
    img = pygame.transform.scale(img, (60, 60))
    asteroid_imgs.append(img)

explosion_img = pygame.image.load(resource_path("explosion.png")).convert_alpha()
explosion_img = pygame.transform.scale(explosion_img, (60, 60))

# =======================
# Load ảnh nền
# =======================
bg_menu = pygame.image.load(resource_path("nen_menu.png")).convert()
bg_menu = pygame.transform.scale(bg_menu, (WIDTH, HEIGHT))

bg_game = pygame.image.load(resource_path("nen_choi.png")).convert()
bg_game = pygame.transform.scale(bg_game, (WIDTH, HEIGHT))

# =======================
# Lớp Ship - Tàu người chơi
# =======================
class Ship:
    def __init__(self):
        self.image_orig = ship_img  # Ảnh gốc (chưa xoay)
        self.image = self.image_orig
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.pos = pygame.Vector2(self.rect.center)  # Vị trí trung tâm
        self.angle = 0
        self.rotation_speed = 3
        self.acceleration = 0.2
        self.velocity = pygame.Vector2(0, 0)  # Vận tốc hiện tại
    
    def rotate(self, direction):
        self.angle += self.rotation_speed * direction
        self.image = pygame.transform.rotate(self.image_orig, -self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
    
    def move(self):
        rad_angle = math.radians(self.angle)
        direction = pygame.Vector2(math.cos(rad_angle), math.sin(rad_angle))
        self.velocity += direction * self.acceleration
        if self.velocity.length() > 5:
            self.velocity.scale_to_length(5)
        self.pos += self.velocity
        self.rect.center = self.pos

        # Giới hạn trong màn hình
        if self.rect.left < 0:
            self.pos.x = self.rect.width // 2
        if self.rect.right > WIDTH:
            self.pos.x = WIDTH - self.rect.width // 2
        if self.rect.top < 0:
            self.pos.y = self.rect.height // 2
        if self.rect.bottom > HEIGHT:
            self.pos.y = HEIGHT - self.rect.height // 2
        self.rect.center = self.pos

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# =======================
# Lớp Missile - Tên lửa bắn ra
# =======================
class Missile:
    def __init__(self, pos, angle):
        self.pos = pygame.Vector2(pos)
        self.speed = 10
        self.angle = angle
        rad = math.radians(angle)
        self.velocity = pygame.Vector2(math.cos(rad), math.sin(rad)) * self.speed
        self.radius = 4

    def update(self):
        self.pos += self.velocity

    def off_screen(self):
        return self.pos.x < 0 or self.pos.x > WIDTH or self.pos.y < 0 or self.pos.y > HEIGHT

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), (int(self.pos.x), int(self.pos.y)), self.radius)

    def get_rect(self):
        return pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius*2, self.radius*2)

# =======================
# Lớp Asteroid - Quái vật
# =======================
class Asteroid:
    def __init__(self):
        self.image = random.choice(asteroid_imgs)
        self.rect = self.image.get_rect()
        self.pos = pygame.Vector2(random.randrange(WIDTH), random.randrange(HEIGHT))
        self.rect.center = self.pos
        angle = random.uniform(0, 360)
        speed = random.uniform(1, 3)
        rad = math.radians(angle)
        self.velocity = pygame.Vector2(math.cos(rad), math.sin(rad)) * speed

    def update(self):
        self.pos += self.velocity
        if self.pos.x < 0:
            self.pos.x = WIDTH
        elif self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.y < 0:
            self.pos.y = HEIGHT
        elif self.pos.y > HEIGHT:
            self.pos.y = 0
        self.rect.center = self.pos

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# =======================
# Lớp Explosion - Hiệu ứng nổ
# =======================
class Explosion:
    def __init__(self, pos):
        self.pos = pos
        self.timer = 15
        self.done = False

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.done = True

    def draw(self, screen):
        rect = explosion_img.get_rect(center=self.pos)
        screen.blit(explosion_img, rect)

# =======================
# Đọc và ghi điểm cao
# =======================
def load_highscore():
    try:
        with open("highscore.txt", "r") as f:
            return int(f.read())
    except:
        return 0

def save_highscore(score):
    highscore = load_highscore()
    if score > highscore:
        with open("highscore.txt", "w") as f:
            f.write(str(score))

# =======================
# Hiển thị menu chính
# =======================
def show_menu():
    font_big = pygame.font.SysFont(None, 72)
    font_small = pygame.font.SysFont(None, 36)
    title = font_big.render("ASTROCRASH", True, (255, 255, 255))
    option1 = font_small.render("Press ENTER to Start", True, (255, 255, 255))
    option2 = font_small.render("Press ESC to Quit", True, (255, 255, 255))
    highscore = load_highscore()
    highscore_text = font_small.render(f"High Score: {highscore}", True, (255, 255, 0))

    while True:
        screen.blit(bg_menu, (0, 0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
        screen.blit(option1, (WIDTH//2 - option1.get_width()//2, 300))
        screen.blit(option2, (WIDTH//2 - option2.get_width()//2, 350))
        screen.blit(highscore_text, (WIDTH//2 - highscore_text.get_width()//2, 450))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        clock.tick(FPS)

# =======================
# Game Over màn hình
# =======================
def show_game_over(score):
    font_big = pygame.font.SysFont(None, 72)
    font_small = pygame.font.SysFont(None, 36)
    over_text = font_big.render("GAME OVER", True, (255, 0, 0))
    score_text = font_small.render(f"Your Score: {score}", True, (255, 255, 255))
    prompt = font_small.render("Press ENTER to return to menu", True, (255, 255, 255))

    while True:
        screen.fill((0, 0, 0))
        screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, 200))
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 300))
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, 400))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return
        clock.tick(FPS)

# =======================
# Hàm chính chạy game
# =======================
def main():
    pygame.mixer.music.play(-1)

    ship = Ship()
    missiles = []
    asteroids = [Asteroid() for _ in range(5)]
    explosions = []

    score = 0
    running = True

    # ====== Thời gian game ======
    start_ticks = pygame.time.get_ticks()  # thời gian bắt đầu
    game_duration = 3 * 60  # 3 phút = 180 giây

    while running:
        clock.tick(FPS)

        # ====== Tính thời gian còn lại ======
        seconds_passed = (pygame.time.get_ticks() - start_ticks) // 1000
        time_left = max(0, game_duration - seconds_passed)

        if time_left == 0:
            save_highscore(score)
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_highscore(score)
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    save_highscore(score)
                    running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            ship.rotate(-1)
        if keys[pygame.K_RIGHT]:
            ship.rotate(1)
        if keys[pygame.K_UP]:
            ship.move()
        if keys[pygame.K_SPACE]:
            if len(missiles) < 5:
                laser_sound.play()
                missiles.append(Missile(ship.pos, ship.angle))

        for missile in missiles[:]:
            missile.update()
            if missile.off_screen():
                missiles.remove(missile)

        for asteroid in asteroids:
            asteroid.update()

        for missile in missiles[:]:
            missile_rect = missile.get_rect()
            for asteroid in asteroids[:]:
                if missile_rect.colliderect(asteroid.rect):
                    boom_sound.play()
                    explosions.append(Explosion(asteroid.pos))
                    score += 10
                    missiles.remove(missile)
                    asteroids.remove(asteroid)
                    asteroids.append(Asteroid())
                    break

        for exp in explosions[:]:
            exp.update()
            if exp.done:
                explosions.remove(exp)

        screen.blit(bg_game, (0, 0))
        ship.draw(screen)
        for missile in missiles:
            missile.draw(screen)
        for asteroid in asteroids:
            asteroid.draw(screen)
        for exp in explosions:
            exp.draw(screen)

        # ====== Hiển thị điểm và thời gian ======
        font = pygame.font.SysFont(None, 30)
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        minutes = time_left // 60
        seconds = time_left % 60
        time_text = font.render(f"Time: {minutes:02}:{seconds:02}", True, (255, 255, 255))
        screen.blit(time_text, (WIDTH - 150, 10))

        pygame.display.flip()

    show_game_over(score)


# =======================
# Chạy game
# =======================
if __name__ == "__main__":
    while True:
        show_menu()
        main()
