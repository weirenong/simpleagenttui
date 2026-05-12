import sys
languages = [
    "Hello World",
    "Bonjour le monde",
    "Hallo Welt",
    "Ciao mondo",
    "HALLO WELT",
    "مرحبا بالعالم",
    "Привет мир",
    "你好世界",
    "வணக்கம் உலகம்",
    "こんにちは世界",
    "안녕하세요 세계",
    "สวัสดีชาวโลก",
    "Hej världen"
]
idx = 0
while True:
    line = sys.stdin.readline()
    if not line:
        break
    print(languages[idx])
    idx = (idx + 1) % len(languages)
