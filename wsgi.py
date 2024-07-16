from app import app
import threading
from app import periodic_check

if __name__ == "__main__":
    threading.Thread(target=periodic_check, daemon=True).start()
    app.run(host='0.0.0.0', port=8000)
