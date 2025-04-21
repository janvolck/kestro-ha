from . import create_app
from .config import DevelopmentConfig

if __name__ == "__main__":

    app = create_app()
    app.config.from_object(DevelopmentConfig)
    app.run(host="0.0.0.0", use_reloader=False)
