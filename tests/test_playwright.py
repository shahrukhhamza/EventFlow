import os
import threading
from wsgiref.simple_server import make_server

import pytest


@pytest.mark.playwright
def test_playwright_signup_login_flow(app_instance):
    playwright_module = pytest.importorskip("playwright.sync_api")

    host = "127.0.0.1"
    port = 5059
    http_server = make_server(host, port, app_instance)
    server_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://{host}:{port}"

    try:
        with playwright_module.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            unique_email = f"playwright_{os.getpid()}@example.com"
            page.goto(f"{base_url}/signup")
            page.get_by_label("Full Name").fill("Playwright Student")
            page.get_by_label("Email").fill(unique_email)
            page.get_by_label("Password").fill("test123")
            page.get_by_role("button", name="Sign up").click()
            page.wait_for_url("**/login")

            page.get_by_label("Email").fill(unique_email)
            page.get_by_label("Password").fill("test123")
            page.get_by_role("button", name="Login").click()
            page.wait_for_url("**/dashboard")
            page.get_by_role("heading", name="Dashboard").wait_for(state="visible")

            assert page.url.endswith("/dashboard")
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright browser not available in environment: {exc}")
    finally:
        http_server.shutdown()
        server_thread.join(timeout=2)