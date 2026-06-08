# config.py
import os

# Configurações do Navegador
# Define se o Chrome deve ser executado em modo invisível (sem abrir a janela)
# Pode ser controlado pela variável de ambiente HEADLESS (default: True)
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")

# Quantidade de vídeos a coletar por canal
MAX_VIDEOS = 10

# Lista de URLs de canais do YouTube para raspar
# Idealmente, informe a URL base do canal
CHANNELS = [
"https://www.youtube.com/@manodeyvin",
"https://www.youtube.com/@yudiganeko",
"https://www.youtube.com/@fknight",
"https://www.youtube.com/@rohtuu",
"https://www.youtube.com/@meunomeebero",
"https://www.youtube.com/@AnnaCodesStuff",
"https://www.youtube.com/@boltjz",
"https://www.youtube.com/@TechWithTim",
"https://www.youtube.com/@IAmManware",
"https://www.youtube.com/@CodebyeAngel",
"https://www.youtube.com/@4kkoi",
"https://www.youtube.com/@TheCodingSloth",
"https://www.youtube.com/@bigboxSWE",
"https://www.youtube.com/@shaulinsmb",
"https://www.youtube.com/@Jabrils",
"https://www.youtube.com/@SebastianLague",
"https://www.youtube.com/@clem",
"https://www.youtube.com/@LowLevelTV",
"https://www.youtube.com/@technetiumm",
"https://www.youtube.com/@codegois",
"https://www.youtube.com/@TechEvy",
"https://www.youtube.com/@Mogen_Tech",
"https://www.youtube.com/@realcrin",
]
