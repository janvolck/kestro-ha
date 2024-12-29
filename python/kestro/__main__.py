from kestro import create_app

if __name__ == "__main__":

    app = create_app()
    app.config.update(
        ENV='development',
        DEBUG=True
    )
    app.run(host='0.0.0.0', use_reloader=False)
