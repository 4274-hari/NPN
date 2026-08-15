from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db, bcrypt

from routes.auth import auth_bp
from routes.users import users_bp
from routes.tweets import tweets_bp
from routes.notifications import notifications_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(tweets_bp, url_prefix="/api/tweets")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "app": "Nextweet API"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0", use_reloader=False)
