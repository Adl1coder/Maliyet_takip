import pygame
import time
import os
import pandas as pd
import matplotlib.pyplot as plt

# Pygame başlat
pygame.init()

# Ekran boyutları
WIDTH, HEIGHT = 1200, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mouse Montaj Süreci")

# Renkler
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
RED = (200, 0, 0)

# Matplotlib canlı grafik modu
plt.ion()
fig, ax = plt.subplots()

# Pygame font
pygame.font.init()
font = pygame.font.SysFont("Arial", 16)


# Parça sınıfı
class Parca:
    def __init__(self, ad, maliyet, image_path, omur):
        self.ad = ad
        self.maliyet = maliyet
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.omur = omur


# Mouse montaj sınıfı
class MouseAssembly:
    def __init__(self):
        self.parcalar = []
        self.toplam_maliyet = 0
        self.maliyet_tarihi = []
        self.parca_sirasi = []

    def parca_ekle(self, parca):
        if parca in self.parcalar:
            return
        self.parcalar.append(parca)
        self.toplam_maliyet += parca.maliyet
        self.maliyet_tarihi.append(self.toplam_maliyet)
        self.parca_sirasi.append(len(self.parcalar))
        self.guncelle()

    def guncelle(self):
        screen.fill(WHITE)
        pygame.draw.rect(screen, BLACK, (30, 30, 650, 500), 2)

        for i, parca in enumerate(self.parcalar):
            x_pos = 50 + (i % 4) * 150
            y_pos = 50 + (i // 4) * 150
            screen.blit(parca.image, (x_pos, y_pos))
            text_surface = font.render(f"{parca.ad} ({parca.maliyet} TL)", True, BLACK)
            screen.blit(text_surface, (x_pos, y_pos + 110))

        pygame.draw.rect(screen, RED, (300, 600, 150, 40))
        birlestir_text = font.render("Birleştir", True, WHITE)
        screen.blit(birlestir_text, (330, 610))
        pygame.display.update()

    def maliyet_grafik(self):
        ax.clear()
        ax.plot(self.parca_sirasi, self.maliyet_tarihi, marker='o', linestyle='-', color='b')
        ax.set_xlabel("Eklenen Parça Sayısı")
        ax.set_ylabel("Toplam Maliyet (TL)")
        ax.set_title("Maliyet Akışı")
        ax.grid(True)
        plt.draw()
        plt.show()


# Parça verileri
parca_listesi = [
    Parca("Üst Kapak", 50, "top_cover.png", 5000),
    Parca("Sol Tık", 30, "left_click.png", 3000),
    Parca("Sağ Tık", 30, "right_click.png", 3000),
    Parca("Tekerlek", 40, "scroll_wheel.png", 4000),
    Parca("Sensör", 150, "sensor.png", 10000),
    Parca("Devre Kartı", 200, "pcb_board.png", 8000),
    Parca("USB Kablo", 60, "usb_cable.png", 6000)
]

# Ana döngü
mouse = MouseAssembly()
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLACK, (30, 30, 650, 500), 2)

    y_offset = 50
    for i, parca in enumerate(parca_listesi):
        pygame.draw.rect(screen, GRAY, (WIDTH - 280, y_offset, 230, 110))
        screen.blit(parca.image, (WIDTH - 270, y_offset + 5))
        text_surface = font.render(f"{parca.ad} - {parca.maliyet} TL", True, BLACK)
        screen.blit(text_surface, (WIDTH - 170, y_offset + 10))

        button_surface = font.render("Ekle", True, BLACK)
        pygame.draw.rect(screen, GREEN, (WIDTH - 170, y_offset + 40, 100, 30))
        screen.blit(button_surface, (WIDTH - 150, y_offset + 50))
        y_offset += 120

    pygame.draw.rect(screen, BLUE, (50, 600, 200, 40))
    link_text = font.render("Maliyet Grafiğini Göster", True, WHITE)
    screen.blit(link_text, (70, 610))
    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if 50 <= x <= 250 and 600 <= y <= 640:
                mouse.maliyet_grafik()
            elif 300 <= x <= 450 and 600 <= y <= 640 and len(mouse.parcalar) >= 2:
                birlesik_parca = Parca(" + ".join([p.ad for p in mouse.parcalar[:2]]),
                                       sum(p.maliyet for p in mouse.parcalar[:2]), "sensor.png",
                                       min(p.omur for p in mouse.parcalar[:2]))
                mouse.parcalar = [birlesik_parca] + mouse.parcalar[2:]
                mouse.guncelle()
            for i, parca in enumerate(parca_listesi):
                if WIDTH - 170 <= x <= WIDTH - 70 and (50 + i * 120 + 40) <= y <= (50 + i * 120 + 70):
                    mouse.parca_ekle(parca)

    clock.tick(60)

pygame.quit()
