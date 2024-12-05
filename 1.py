import pygame
import requests
from io import BytesIO
import random
import time

# Khởi tạo Pygame
pygame.init()

# Kích thước màn hình cho mobile
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720  # Màn hình ngang
CELL_SIZE = 100
GRID_ROWS, GRID_COLS = 5, 9  # Lưới 5x9
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plants vs Zombies - Mobile Edition")

# Màu sắc
WHITE = (255, 255, 255)
BLUE = (0, 200, 0)

clock = pygame.time.Clock()

# Biến ẩn/hiện ô vuông
hide = False

# Tải ảnh từ URL
def load_image(url, size=None):
    response = requests.get(url)
    img = pygame.image.load(BytesIO(response.content))
    if size:
        img = pygame.transform.scale(img, size)
    return img

# Tải hình nền và hình ảnh
BACKGROUND = load_image("https://i.ibb.co/NZPmPy8/maxresdefault-1.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
SEED_IMAGE = load_image("https://i.ibb.co/DQsNcw8/Seeds.png", (CELL_SIZE, CELL_SIZE))
PEASHOOTER_IMAGE = load_image("https://i.ibb.co/zGMSFX2/dgg7728-99309691-6245-4d73-9f64-2b0a21e14989.png", (CELL_SIZE, CELL_SIZE))
ZOMBIE_IMAGE = load_image("https://static.wikia.nocookie.net/plantsvszombies/images/a/a6/ZombieHD.png/revision/latest?cb=20141029062941", (CELL_SIZE, CELL_SIZE))
PEA_IMAGE = load_image("https://static.wikia.nocookie.net/plantsvszombies/images/3/38/Pea_2.png/revision/latest?cb=20150924144852", (90, 90))  # Kích thước đạn 90x90

# Class Plant
class Plant(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = PEASHOOTER_IMAGE
        self.rect = self.image.get_rect(topleft=(x, y))
        self.last_shot_time = time.time()  # Thời gian bắn gần nhất
        self.health = 100  # Máu của Peashooter

    def shoot(self, zombies):
        for zombie in zombies:
            if zombie.rect.y // CELL_SIZE == self.rect.y // CELL_SIZE:  # Kiểm tra cùng hàng
                if abs(self.rect.x - zombie.rect.x) <= CELL_SIZE * 9:  # Khoảng cách trong 9 ô
                    current_time = time.time()
                    if current_time - self.last_shot_time >= 0.8:  # Bắn mỗi 0.8 giây
                        bullet = Bullet(self.rect.centerx, self.rect.centery)
                        bullets.add(bullet)
                        self.last_shot_time = current_time
                        return True
        return False

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()  # Peashooter chết

# Class Zombie
class Zombie(pygame.sprite.Sprite):
    def __init__(self, row):
        super().__init__()
        self.image = ZOMBIE_IMAGE
        self.rect = self.image.get_rect(topleft=(SCREEN_WIDTH, row * CELL_SIZE + 150))  # Spawn từ bên phải
        self.health = 300  # Máu của Zombie
        self.last_attack_time = time.time()

    def move(self, plants):
        # Kiểm tra có Peashooter ở gần
        for plant in plants:
            if plant.rect.y // CELL_SIZE == self.rect.y // CELL_SIZE:  # Cùng hàng
                if abs(self.rect.x - plant.rect.x) <= CELL_SIZE:  # Gần trong 1 ô
                    current_time = time.time()
                    if current_time - self.last_attack_time >= 1:  # Tấn công mỗi giây
                        plant.take_damage(10)
                        self.last_attack_time = current_time
                    return  # Đứng yên
        self.rect.x -= 1  # Di chuyển sang trái

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()  # Zombie chết

# Class Bullet
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = PEA_IMAGE  # Đạn có kích thước 90x90
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 10

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > SCREEN_WIDTH:
            self.kill()  # Hết màn hình

        # Kiểm tra va chạm với Zombie
        for zombie in zombies:
            if self.rect.colliderect(zombie.rect):
                zombie.take_damage(50)  # Zombie mất 50 HP
                self.kill()  # Đạn biến mất

# Sprite Groups
plants = pygame.sprite.Group()
zombies = pygame.sprite.Group()
bullets = pygame.sprite.Group()

# Vẽ lưới ô vuông
def draw_grid():
    if hide:
        return
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = col * CELL_SIZE + 220
            y = row * CELL_SIZE + 150
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, WHITE, rect, 1)

# Thêm cây vào lưới
def add_plant(row, col):
    x = col * CELL_SIZE + 220
    y = row * CELL_SIZE + 150
    plant = Plant(x, y)
    plants.add(plant)

# Spawn Zombie
def spawn_zombie():
    row = random.randint(0, GRID_ROWS - 1)
    zombie = Zombie(row)
    zombies.add(zombie)

# Main Loop
running = True
dragging = False  # Trạng thái kéo thả
hover_pos = None
dragged_seed = None  # Hình ảnh hạt giống được kéo
last_zombie_spawn_time = time.time()

while running:
    screen.blit(BACKGROUND, (0, 0))
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Xử lý sự kiện
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Bắt đầu kéo
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            # Kiểm tra click vào thanh chọn Seeds
            rect = pygame.Rect(10, 10, CELL_SIZE, CELL_SIZE)
            if rect.collidepoint(x, y):
                dragging = True
                dragged_seed = pygame.transform.scale(SEED_IMAGE, (CELL_SIZE, CELL_SIZE * 2))  # Tăng kích thước

        # Kết thúc kéo
        elif event.type == pygame.MOUSEBUTTONUP and dragging:
            dragging = False
            if 220 <= mouse_x <= 220 + GRID_COLS * CELL_SIZE and 150 <= mouse_y <= 150 + GRID_ROWS * CELL_SIZE:
                col = (mouse_x - 220) // CELL_SIZE
                row = (mouse_y - 150) // CELL_SIZE
                add_plant(row, col)

    # Kiểm tra spawn zombie mỗi 5s
    if time.time() - last_zombie_spawn_time >= 5:
        spawn_zombie()
        last_zombie_spawn_time = time.time()

    # Di chuyển và xử lý Zombie
    for zombie in zombies:
        zombie.move(plants)

    # Xử lý bắn đạn
    for plant in plants:
        plant.shoot(zombies)

    # Cập nhật đạn
    bullets.update()

    # Vẽ lưới
    draw_grid()

    # Vẽ cây, zombie, và đạn
    plants.draw(screen)
    zombies.draw(screen)
    bullets.draw(screen)

    # Nếu đang kéo hạt giống, vẽ theo con trỏ chuột
    if dragging and dragged_seed:
        screen.blit(dragged_seed, (mouse_x - CELL_SIZE // 2, mouse_y - CELL_SIZE // 2))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
