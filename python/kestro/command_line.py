from kestro import create_app

def main():
    app = create_app()
    app.config.update(
        ENV='production',
        DEBUG=False
    )
    app.run(host='0.0.0.0')
