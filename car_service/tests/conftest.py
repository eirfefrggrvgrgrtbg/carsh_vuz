import sys
import os

# Добавляем путь к car_service в начало sys.path
service_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if service_path not in sys.path:
    sys.path.insert(0, service_path)

# Удаляем закэшированные модули app, чтобы избежать конфликтов
modules_to_remove = [key for key in sys.modules.keys() if key == 'app' or key.startswith('app.')]
for mod in modules_to_remove:
    del sys.modules[mod]
