"""Tests for monetization-scaffold render.py. Run: python test_render.py"""
import json, os, sys, tempfile, traceback, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import render  # noqa: E402

MANIFEST = {
    "product_name": "Acme Notes",
    "stack": "node",
    "deploy_target": "vercel",
    "currency": "usd",
    "tiers": [
        {"name": "Free", "price": 0, "limits": "100 notes"},
        {"name": "Pro", "price": 8, "interval": "month", "limits": "unlimited"},
        {"name": "Team", "price": 29, "interval": "month", "limits": "5 seats"},
    ],
}


def test_render_writes_all_files():
    with tempfile.TemporaryDirectory() as d:
        paths = render.render(MANIFEST, d)
        names = {os.path.relpath(p, d).replace("\\", "/") for p in paths}
        for expected in ("Dockerfile", "docker-compose.yml", ".env.example", ".gitignore",
                         "stripe/tiers.json", "stripe/server.js", "stripe/checkout.html",
                         ".github/workflows/ci.yml", "deploy.sh"):
            assert expected in names, f"missing {expected}"


def test_tiers_json_correct():
    with tempfile.TemporaryDirectory() as d:
        render.render(MANIFEST, d)
        with open(os.path.join(d, "stripe", "tiers.json"), encoding="utf-8") as f:
            tiers = json.load(f)
        assert tiers["product"] == "Acme Notes"
        assert len(tiers["tiers"]) == 3
        assert tiers["tiers"][0]["is_free"] is True
        assert tiers["tiers"][1]["price"] == 8
        assert tiers["tiers"][2]["interval"] == "month"


def test_checkout_html_has_all_tier_buttons():
    with tempfile.TemporaryDirectory() as d:
        render.render(MANIFEST, d)
        html = open(os.path.join(d, "stripe", "checkout.html"), encoding="utf-8").read()
        assert "Free" in html and "Pro" in html and "Team" in html
        assert "buy(" in html


def test_dockerfile_varies_by_stack():
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        m_py = {**MANIFEST, "stack": "python"}
        m_node = {**MANIFEST, "stack": "node"}
        render.render(m_py, d1)
        render.render(m_node, d2)
        df_py = open(os.path.join(d1, "Dockerfile"), encoding="utf-8").read()
        df_node = open(os.path.join(d2, "Dockerfile"), encoding="utf-8").read()
        assert "python" in df_py and "node" not in df_py
        assert "node" in df_node


def test_deploy_script_targets_chosen_platform():
    for target, marker in (("vercel", "vercel"), ("railway", "railway"), ("fly", "flyctl")):
        with tempfile.TemporaryDirectory() as d:
            render.render({**MANIFEST, "deploy_target": target}, d)
            sh = open(os.path.join(d, "deploy.sh"), encoding="utf-8").read()
            assert marker in sh, f"{target} deploy script missing {marker}"


def test_env_example_has_stripe_keys():
    with tempfile.TemporaryDirectory() as d:
        render.render(MANIFEST, d)
        env = open(os.path.join(d, ".env.example"), encoding="utf-8").read()
        assert "STRIPE_SECRET_KEY" in env
        assert "STRIPE_WEBHOOK_SECRET" in env


def test_validation_rejects_bad_stack():
    try:
        render.render({**MANIFEST, "stack": "ruby"}, "/tmp/whatever-x")
        assert False, "should have raised"
    except ValueError:
        pass


def test_validation_requires_tiers():
    try:
        render.render({"product_name": "x", "stack": "node", "deploy_target": "vercel", "tiers": []}, "/tmp/whatever-y")
        assert False, "should have raised"
    except ValueError:
        pass


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1; print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{len(fns)-failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
