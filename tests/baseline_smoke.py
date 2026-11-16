#!/usr/bin/env python3
"""Exercise a built package with isolated state and a loopback model fixture."""

import argparse
import errno
import fcntl
import json
import os
import pty
import select
import signal
import struct
import subprocess
import tempfile
import termios
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def is_title_request(request):
    for item in request.get("input", []):
        if item.get("type") != "message" or item.get("role") != "user":
            continue
        content = item.get("content", [])
        texts = [content] if isinstance(content, str) else [part.get("text", "") for part in content]
        if any(text.startswith("Generate a concise, single-line task title") for text in texts):
            return True
    return False


class FixtureServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), FixtureHandler)
        self.requests = []


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        body = b'{"data":[]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path != "/v1/responses":
            self.send_error(404)
            return
        request = json.loads(body)
        self.server.requests.append(request)
        sequence = len(self.server.requests)
        response_id = f"baseline-{sequence}"
        title = is_title_request(request)
        primary_sequence = sum(not is_title_request(item) for item in self.server.requests)
        if not title and primary_sequence == 1:
            arguments = {
                "cmd": "set -e; command -v rg; rg --version; printf 'CODEX_NATIVE_TOOL_OK\\n'",
                "login": False,
                "yield_time_ms": 10000,
            }
            item = {
                "type": "custom_tool_call",
                "call_id": "baseline-tool",
                "name": "exec",
                "input": f"text(JSON.stringify(await tools.exec_command({json.dumps(arguments)})))",
            }
        else:
            item = {
                "type": "message",
                "id": "baseline-message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "Baseline task" if title else "BASELINE_OK_169"}],
            }
        events = [
            {"type": "response.created", "response": {"id": response_id}},
            {"type": "response.output_item.done", "item": item},
            {"type": "response.completed", "response": {
                "id": response_id,
                "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            }},
        ]
        payload = "".join(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n" for event in events).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def run_tui(binary, workspace, environment):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 38, 110, 0, 0))
    process = subprocess.Popen(
        [str(binary), "--dangerously-bypass-approvals-and-sandbox", "Run the local baseline fixture."],
        cwd=workspace, env=environment, stdin=slave, stdout=slave, stderr=slave,
        start_new_session=True,
    )
    os.close(slave)
    captured = bytearray()
    probes = {
        b"\x1b[6n": b"\x1b[1;1R",
        b"\x1b]11;?": b"\x1b]11;rgb:0000/0000/0000\x1b\\",
        b"\x1b]10;?": b"\x1b]10;rgb:ffff/ffff/ffff\x1b\\",
        b"\x1b[?u": b"\x1b[?0u",
    }
    answered = dict.fromkeys(probes, 0)
    deadline = time.monotonic() + 60
    try:
        while time.monotonic() < deadline and process.poll() is None:
            if not select.select([master], [], [], 0.5)[0]:
                continue
            try:
                data = os.read(master, 65536)
            except OSError as error:
                if error.errno == errno.EIO:
                    break
                raise
            if not data:
                break
            captured.extend(data)
            for probe, answer in probes.items():
                count = captured.count(probe)
                if count > answered[probe]:
                    os.write(master, answer * (count - answered[probe]))
                    answered[probe] = count
            if b"BASELINE_OK_169" in captured:
                os.write(master, b"\x04")
                process.wait(timeout=15)
                assert process.returncode == 0, process.returncode
                return
        raise AssertionError("TUI did not render the fixture answer:\n" + captured[-6000:].decode(errors="replace"))
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        os.close(master)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    metadata = json.loads((package / "codex-package.json").read_text())
    assert metadata["version"] == "0.169.0", metadata
    assert metadata["target"] == "aarch64-unknown-linux-gnu", metadata
    binary = package / "bin/codex"

    with tempfile.TemporaryDirectory(prefix="codex-touch-baseline-") as temporary:
        root = Path(temporary)
        state = root / "state"
        workspace = root / "workspace"
        state.mkdir()
        workspace.mkdir()
        # Deliberately construct the child environment without API credentials.
        environment = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(root),
            "CODEX_HOME": str(state),
            "LANG": "C.UTF-8",
            "TERM": "xterm-256color",
            "NO_PROXY": "127.0.0.1,localhost",
            "TMPDIR": str(root),
        }

        def run(arguments, *, input_text=None):
            process = subprocess.Popen(
                [str(x) for x in arguments], cwd=workspace, env=environment,
                stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                start_new_session=True,
            )
            try:
                stdout, stderr = process.communicate(input=input_text, timeout=60)
                if process.returncode:
                    raise AssertionError(f"{arguments[0]} exited {process.returncode}:\n{stderr[-6000:]}")
                return subprocess.CompletedProcess(arguments, process.returncode, stdout, stderr)
            except BaseException:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
                raise

        assert run([binary, "--version"]).stdout.strip() == "codex-cli 0.169.0"
        assert "Usage:" in run([binary, "--help"]).stdout
        for relative in ["bin/codex-code-mode-host", "bin/codex-exec-server"]:
            assert "Usage:" in run([package / relative, "--help"]).stdout
        assert "ripgrep" in run([package / "codex-path/rg", "--version"]).stdout
        assert "bubblewrap" in run([package / "codex-resources/bwrap", "--version"]).stdout
        print("PASS: package layout, version, and helper startup.")

        request = {"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "codex-touch-baseline", "version": "0.1.0"},
            "capabilities": {"experimentalApi": True},
        }}
        handshake = run([binary, "app-server"], input_text=json.dumps(request) + "\n")
        replies = [json.loads(line) for line in handshake.stdout.splitlines()]
        assert any(reply.get("id") == 1 and "result" in reply for reply in replies), replies
        print("PASS: app-server initialization.")

        server = FixtureServer()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            (state / "config.toml").write_text(f'''model = "baseline-smoke"
model_provider = "baseline"
approval_policy = "never"
sandbox_mode = "danger-full-access"
suppress_unstable_features_warning = true
[model_providers.baseline]
name = "local baseline fixture"
base_url = "http://127.0.0.1:{server.server_port}/v1"
wire_api = "responses"
requires_openai_auth = false
request_max_retries = 0
stream_max_retries = 0
[features]
code_mode_only = true
code_mode_host = true
memories = false
apps = false
plugins = false
[analytics]
enabled = false
[otel]
exporter = "none"
trace_exporter = "none"
metrics_exporter = "none"
[projects.{json.dumps(str(workspace))}]
trust_level = "trusted"
''')
            execution = run([
                binary, "exec", "--skip-git-repo-check", "--ephemeral", "--json",
                "--dangerously-bypass-approvals-and-sandbox", "Run the local baseline fixture.",
            ])
            assert "BASELINE_OK_169" in execution.stdout, execution.stdout[-6000:]
            outputs = [item for request in server.requests for item in request.get("input", [])
                       if item.get("type") == "custom_tool_call_output" and item.get("call_id") == "baseline-tool"]
            assert outputs, "No result returned from the code-mode host"
            output = json.dumps(outputs, ensure_ascii=False)
            assert "CODEX_NATIVE_TOOL_OK" in output, output
            assert str(package / "codex-path/rg") in output, output
            print("PASS: loopback model -> V8 code-mode host -> shell/ripgrep -> final answer.")
            server.requests.clear()
            try:
                run_tui(binary, workspace, environment)
                tui_outputs = json.dumps([item for request in server.requests for item in request.get("input", [])
                                          if item.get("type") == "custom_tool_call_output" and item.get("call_id") == "baseline-tool"])
                assert "CODEX_NATIVE_TOOL_OK" in tui_outputs, tui_outputs
                assert "ripgrep" in tui_outputs, tui_outputs
                print("TUI fixture request count:", len(server.requests))
                print("PASS: default-daemon TUI renders the completed tool turn in an isolated PTY.")
            finally:
                run([binary, "app-server", "daemon", "stop"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
    print("PASS: baseline smoke; isolated state and temporary files removed.")


if __name__ == "__main__":
    main()
