from flask import Flask, render_template, Response
from flask_cors import CORS


class EndpointAction(object):

    def __init__(self, action):
        self.action = action

    def __call__(self, *args):
        # Perform the action
        answer = self.action()
        # Create the answer (bundle it in a correctly formatted HTTP answer)
        self.response = Response(answer, status=200, headers={})
        # Send it
        return self.response


class WebServer:

    def __init__(self, name):
        self.app = Flask(
            name, static_url_path='/', static_folder='webapp/static', template_folder='webapp/templates')

        CORS(self.app)
        self.app.add_url_rule('/', '/', EndpointAction(self.index))
        self.app.add_url_rule('/dashboard', '/dashboard', EndpointAction(self.index))

    def add_controller(self, controller):
        self.app.register_blueprint(controller)

    def index(self):
        return render_template('index.html')

