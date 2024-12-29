from kestro import create_app

def main():
    app = create_app()
    app.config.update(
        ENV='development',
        DEBUG=True
    )
    app.run(host='0.0.0.0')
