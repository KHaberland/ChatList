import sys
from PIL import Image, ImageDraw

# Словарь цветов
COLORS = {
    "синий": (30, 144, 255),      # DodgerBlue
    "красный": (220, 20, 60),     # Crimson
    "желтый": (255, 215, 0),      # Gold
}

def draw_circle(draw, coords, color):
    """Рисует круг."""
    draw.ellipse(coords, fill=color)

def draw_square(draw, coords, color):
    """Рисует квадрат."""
    draw.rectangle(coords, fill=color)

def draw_triangle(draw, coords, color):
    """Рисует треугольник."""
    x1, y1, x2, y2 = coords
    # Вершины треугольника: верхняя точка, левый нижний угол, правый нижний угол
    center_x = (x1 + x2) // 2
    points = [
        (center_x, y1),      # Верхняя вершина
        (x1, y2),            # Левый нижний угол
        (x2, y2),            # Правый нижний угол
    ]
    draw.polygon(points, fill=color)

# Словарь функций рисования
SHAPES = {
    "круг": draw_circle,
    "квадрат": draw_square,
    "треугольник": draw_triangle,
}

def draw_icon(size, bg_shape, bg_color, fg_shape, fg_color):
    """Рисует иконку с заданными фигурами и цветами."""
    # Создаем изображение с белым фоном
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Координаты для фоновой фигуры (весь размер с небольшим отступом)
    bg_padding = int(size * 0.02)
    bg_coords = [bg_padding, bg_padding, size - bg_padding, size - bg_padding]
    
    # Рисуем фоновую фигуру
    SHAPES[bg_shape](draw, bg_coords, COLORS[bg_color])
    
    # Координаты для фигуры на переднем плане (с отступом 20%)
    fg_padding = int(size * 0.2)
    fg_coords = [fg_padding, fg_padding, size - fg_padding, size - fg_padding]
    
    # Рисуем фигуру на переднем плане
    SHAPES[fg_shape](draw, fg_coords, COLORS[fg_color])
    
    return img

def select_option(prompt, options):
    """Выбор опции из списка."""
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    while True:
        try:
            choice = input("Введите номер (1-3): ").strip()
            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]
            print("[!] Неверный номер. Попробуйте снова.")
        except ValueError:
            print("[!] Введите число от 1 до 3.")

def print_usage():
    """Выводит справку по использованию."""
    print("Использование: python create_icon.py [фон_фигура] [фон_цвет] [фигура] [цвет]")
    print("")
    print("Фигуры: круг, квадрат, треугольник (или 1, 2, 3)")
    print("Цвета:  синий, красный, желтый (или 1, 2, 3)")
    print("")
    print("Примеры:")
    print("  python create_icon.py квадрат красный круг синий")
    print("  python create_icon.py 2 2 1 1")
    print("")
    print("Без аргументов - интерактивный режим")

def parse_arg(arg, options):
    """Преобразует аргумент в опцию."""
    # Если это число
    if arg.isdigit():
        index = int(arg) - 1
        if 0 <= index < len(options):
            return options[index]
    # Если это название
    if arg.lower() in options:
        return arg.lower()
    return None

def main():
    shapes = ["круг", "квадрат", "треугольник"]
    colors = ["синий", "красный", "желтый"]
    
    # Проверка аргументов командной строки
    if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help", "?"]:
        print_usage()
        return
    
    if len(sys.argv) == 5:
        # Режим с аргументами: python create_icon.py фон_фигура фон_цвет фигура цвет
        bg_shape = parse_arg(sys.argv[1], shapes)
        bg_color = parse_arg(sys.argv[2], colors)
        fg_shape = parse_arg(sys.argv[3], shapes)
        fg_color = parse_arg(sys.argv[4], colors)
        
        if not all([bg_shape, bg_color, fg_shape, fg_color]):
            print("[!] Неверные аргументы!")
            print_usage()
            return
    elif len(sys.argv) == 1:
        # Интерактивный режим
        print("=" * 50)
        print("    ГЕНЕРАТОР ИКОНОК")
        print("=" * 50)
        
        bg_shape = select_option("Выберите фигуру для ФОНА:", shapes)
        bg_color = select_option(f"Выберите цвет фона ({bg_shape}):", colors)
        fg_shape = select_option("Выберите фигуру НА ФОНЕ:", shapes)
        fg_color = select_option(f"Выберите цвет фигуры ({fg_shape}):", colors)
    else:
        print("[!] Неверное количество аргументов!")
        print_usage()
        return
    
    print("\n" + "=" * 50)
    print(f"Ваш выбор:")
    print(f"   Фон: {bg_color} {bg_shape}")
    print(f"   Фигура: {fg_color} {fg_shape}")
    print("=" * 50)
    
    # Размеры иконок
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    print("\nГенерация иконки...")
    
    # Рисуем иконки всех размеров
    icons = [draw_icon(s, bg_shape, bg_color, fg_shape, fg_color) for s, _ in sizes]
    
    # Сохраняем в формате ICO
    try:
        icons[0].save(
            "app.ico",
            format="ICO",
            sizes=sizes,
            append_images=icons[1:]
        )
        print("\n[OK] Иконка 'app.ico' создана!")
        print(f"     Дизайн: {fg_color} {fg_shape} на {bg_color} {bg_shape}")
    except Exception as e:
        print(f"[!] Ошибка при сохранении: {e}")
        # Альтернативный способ
        print("Попытка альтернативного метода...")
        icons[0].save("app.ico", format="ICO")
        print("[OK] Иконка 'app.ico' создана (только один размер)")

if __name__ == "__main__":
    main()
