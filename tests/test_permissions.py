"""اختبارات utils/permissions.py"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakeUser:
    def __init__(self, role, authenticated=True):
        self.role = role
        self.is_authenticated = authenticated


def test_roles_required_allows_matching_role(monkeypatch):
    import flask
    from utils.permissions import roles_required

    app = flask.Flask(__name__)

    @app.route("/test")
    @roles_required("admin", "accountant")
    def protected():
        return "ok"

    with app.test_request_context("/test"):
        import flask_login
        monkeypatch.setattr(flask_login.utils, "_get_user", lambda: FakeUser("accountant"))
        response = protected()
        assert response == "ok"


def test_roles_required_blocks_viewer(monkeypatch):
    import flask
    from utils.permissions import roles_required
    from werkzeug.exceptions import Forbidden

    app = flask.Flask(__name__)
    app.config["SECRET_KEY"] = "test"

    @app.route("/test")
    @roles_required("admin", "accountant")
    def protected():
        return "ok"

    with app.test_request_context("/test"):
        import flask_login
        monkeypatch.setattr(flask_login.utils, "_get_user", lambda: FakeUser("viewer"))
        try:
            protected()
            assert False, "المفروض يرفض viewer"
        except Forbidden:
            pass
