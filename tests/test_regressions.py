import os
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-only-secret"

import unittest
from contextlib import ExitStack
from unittest.mock import patch
from app import app
from extensions import db
from models import User, Settings
from recon.utils import normalize_domain


class RegressionTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, DEFAULT_DAILY_SCAN_LIMIT=3)
        self.ctx = app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def signup(self, name="FiamrHack", email="owner@example.test"):
        return self.client.post("/signup", data={
            "username": name, "email": email, "password": "test-password-123"
        })

    def login(self, identifier="FiamrHack", password="test-password-123"):
        return self.client.post("/login", data={"identifier": identifier, "password": password})

    def test_existing_mixed_case_username_login(self):
        self.signup()
        for identifier in ["FiamrHack", "fiamrhack", "FIAMRHACK", "OWNER@EXAMPLE.TEST"]:
            self.client.get("/logout")
            self.assertEqual(self.login(identifier).status_code, 302)
            self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_wrong_password_does_not_login(self):
        self.signup()
        self.client.get("/logout")
        self.login(password="wrong")
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_duplicate_case_signup(self):
        self.signup()
        self.client.get("/logout")
        self.signup("fiamrhack", "another@example.test")
        self.assertEqual(User.query.count(), 1)

    def test_non_admin_cannot_access_admin(self):
        self.signup()
        self.client.get("/logout")
        self.signup("second", "second@example.test")
        self.assertEqual(self.client.get("/admin/").status_code, 403)

    def test_blocked_existing_session_is_denied(self):
        self.signup()
        user = User.query.first()
        user.is_active_user = False
        db.session.commit()
        result = self.client.post("/api/recon", json={"target": "example.test"})
        self.assertEqual(result.status_code, 401)
        self.assertTrue(result.is_json)

    def test_api_without_session_is_json(self):
        result = self.client.post("/api/recon", json={"target": "example.test"})
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.json["login_url"], "/login")

    def test_bad_targets_never_start_network(self):
        self.signup()
        with patch("main.get_whois") as whois:
            for payload in [[], ["x"], {"target": []}, {"target": 17},
                            {"target": "postgresql://facebook.com"},
                            {"target": "https://u:p@example.com"}, {"target": "x"},
                            {"target": "example.com:999999"}]:
                result = self.client.post("/api/recon", json=payload)
                self.assertEqual(result.status_code, 400, payload)
                self.assertTrue(result.is_json)
            whois.assert_not_called()

    def test_api_failure_is_json_without_details(self):
        self.signup()
        with patch("main.get_whois", side_effect=RuntimeError("private-internal-detail")):
            result = self.client.post("/api/recon", json={"target": "example.test"})
        self.assertEqual(result.status_code, 500)
        self.assertTrue(result.is_json)
        self.assertNotIn("private-internal-detail", result.get_data(as_text=True))

    def test_scan_result_and_history(self):
        self.signup()
        with ExitStack() as stack:
            for name, value in [("get_whois", {"registrar": "Test"}),
                                ("get_dns_records", {}),
                                ("passive_subdomains", []),
                                ("brute_force_subdomains", []),
                                ("check_live_hosts", [])]:
                stack.enter_context(patch("main." + name, return_value=value))
            result = self.client.post("/api/recon", json={"target": "https://www.example.test/path"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["target"], "example.test")
        self.assertEqual(result.json["scans_today"], 1)
        self.assertIn("example.test", self.client.get("/my-scans").get_data(as_text=True))

    def test_daily_limit_uses_config_and_is_enforced(self):
        self.signup()
        self.assertEqual(Settings.get().daily_scan_limit, 3)
        self.client.get("/logout")
        self.signup("second", "second@example.test")
        Settings.get().daily_scan_limit = 0
        db.session.commit()
        with patch("main.get_whois") as whois:
            result = self.client.post("/api/recon", json={"target": "example.test"})
            self.assertEqual(result.status_code, 429)
            whois.assert_not_called()

    def test_legacy_case_collision_does_not_pick_arbitrary_user(self):
        self.signup()
        other = User(username="fiamrhack", email="other@example.test")
        other.set_password("other-password")
        db.session.add(other)
        db.session.commit()
        self.client.get("/logout")
        self.login("FIAMRHACK")
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        self.assertEqual(self.login("FiamrHack").status_code, 302)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_domain_normalization_and_health(self):
        self.assertEqual(normalize_domain("https://WWW.Example.COM/path?q=1"), "example.com")
        self.assertEqual(normalize_domain("Example.COM."), "example.com")
        self.assertEqual(self.client.get("/healthz").json["status"], "ok")


if __name__ == "__main__":
    unittest.main()
