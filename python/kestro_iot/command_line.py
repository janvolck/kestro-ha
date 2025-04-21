from . import create_app
from .config import ProductionConfig


def main():
    app = create_app()
    app.config.from_object(ProductionConfig)
    app.run(host="0.0.0.0")
