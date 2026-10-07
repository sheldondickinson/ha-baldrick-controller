import subprocess


def test_xml_upload_disarmed_session_and_failure_cleanup():
    subprocess.run(["node", "tests/upload_frontend.cjs"], check=True)
