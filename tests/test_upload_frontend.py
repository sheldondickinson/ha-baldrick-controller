import subprocess


def test_xml_upload_disarmed_session_and_failure_cleanup():
    subprocess.run(["node", "tests/upload_frontend.cjs"], check=True)


def test_automatic_output_and_idle_release():
    subprocess.run(["node", "tests/idle_frontend.cjs"], check=True)
