#!/usr/bin/env python3
"""SGR mouse -> real TUI -> async answer delivery, using only synthetic local data."""
import codecs
import errno
import fcntl
import json
import os
import pty
import re
import select
import signal
import struct
import subprocess
import tempfile
import termios
import threading
import time
import unicodedata
from http.server import ThreadingHTTPServer
from pathlib import Path

from baseline_smoke import FixtureHandler, is_title_request


class Screen:
    """Small cell decoder for the VT cursor/erase output used by this fixture.

    It does not emulate a phone. Test coordinates always come from painted text.
    """
    def __init__(self, width, height):
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.pending = ""
        self.mouse = False
        self.resize(width, height)

    def resize(self, width, height):
        self.width, self.height = width, height
        self.cells = [[" "] * width for _ in range(height)]
        self.x = self.y = 0

    def feed(self, data):
        self.pending += self.decoder.decode(data)
        while self.pending:
            if self.pending.startswith("\x1b["):
                match = re.match(r"\x1b\[([0-?]*)([ -/]*)([@-~])", self.pending)
                if not match:
                    return
                raw, _, op = match.groups()
                self.pending = self.pending[match.end():]
                args = [int(n) if n else 0 for n in raw.lstrip("?<>=").split(";") if n.isdigit() or not n]
                n = (args[0] if args else 0) or 1
                if op in "hl" and raw.startswith("?"):
                    if any(mode in args for mode in (1000,1002,1003)):
                        self.mouse = op == "h"
                    if 1049 in args and op == "h":
                        self.resize(self.width, self.height)
                elif op in "Hf": self.y, self.x = n-1, ((args[1] if len(args)>1 else 1) or 1)-1
                elif op == "G": self.x = n-1
                elif op == "d": self.y = n-1
                elif op == "A": self.y -= n
                elif op == "B": self.y += n
                elif op == "C": self.x += n
                elif op == "D": self.x -= n
                elif op == "E": self.y += n; self.x = 0
                elif op == "F": self.y -= n; self.x = 0
                elif op == "J":
                    mode = args[0] if args else 0
                    for y in range(self.height):
                        for x in range(self.width):
                            if mode in (2,3) or (mode == 0 and (y,x) >= (self.y,self.x)) or (mode == 1 and (y,x) <= (self.y,self.x)):
                                self.cells[y][x] = " "
                elif op in "KX":
                    mode = args[0] if args else 0
                    start = 0 if op == "K" and mode in (1,2) else self.x
                    end = self.x+1 if op == "K" and mode == 1 else self.width if op == "K" else min(self.width,self.x+n)
                    self.cells[self.y][start:end] = [" "]*(end-start)
                elif op == "S":
                    for _ in range(min(n,self.height)): self.cells.pop(0); self.cells.append([" "]*self.width)
                self.x=max(0,min(self.x,self.width-1));self.y=max(0,min(self.y,self.height-1))
            elif self.pending.startswith(("\x1b]", "\x1bP")):
                end = re.search("\x07|\x1b\\\\", self.pending)
                if not end: return
                self.pending = self.pending[end.end():]
            elif self.pending.startswith("\x1b"):
                if len(self.pending)<2: return
                count = 3 if self.pending[1] in "()" else 2
                if len(self.pending)<count: return
                self.pending=self.pending[count:]
            else:
                ch,self.pending=self.pending[0],self.pending[1:]
                if ch == "\r": self.x=0
                elif ch == "\n": self.y=min(self.y+1,self.height-1)
                elif ch == "\b": self.x=max(0,self.x-1)
                elif ch >= " " and not unicodedata.combining(ch):
                    width=2 if unicodedata.east_asian_width(ch) in "WF" else 1
                    if self.x>=self.width: self.x=0;self.y=min(self.y+1,self.height-1)
                    self.cells[self.y][self.x]=ch
                    if width==2 and self.x+1<self.width:self.cells[self.y][self.x+1]=""
                    self.x+=width

    def find(self, text):
        # Searching cell prefixes preserves wide-character coordinates.
        for y in reversed(range(self.height)):
            row = self.cells[y]
            for x in range(self.width):
                if "".join(row[x:]).startswith(text): return (x+1,y+1)
        return None

    def text(self): return "\n".join("".join(row) for row in self.cells)


class Handler(FixtureHandler):
    def do_POST(self):
        request=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append(request)
        title=is_title_request(request)
        primary=sum(not is_title_request(r) for r in self.server.requests)
        self.send_response(200);self.send_header("Content-Type","text/event-stream");self.end_headers()
        def emit(event):
            self.wfile.write(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode());self.wfile.flush()
        try:
            emit({"type":"response.created","response":{"id":f"touch-{primary}"}})
            if not title and "TOUCH_HOLD_INTERRUPT" in json.dumps(request.get("input", [])):
                self.server.interrupt_started.set()
                if not any(self.server.interrupt_release.wait(55) for _ in range(2)): return
            elif not title and primary==1:
                item={"type":"function_call","call_id":"touch-questions","namespace":"functions","name":"request_user_input_async","arguments":json.dumps({"questions":[
                    {"title":"Choose a route","options":["Alpha with a deliberately long description for wrapping on a narrow terminal", "Beta selected"]},
                    {"title":"Choose another route","options":["Named answer"]},
                    {"title":"Write a final note"},
                ]})}
                emit({"type":"response.output_item.done","item":item})
            elif not title and primary==2:
                self.server.continuation.set()
                # Bound each wait while allowing slower phone setup/interaction.
                if not any(self.server.release.wait(55) for _ in range(3)): return
            else:
                emit({"type":"response.output_item.done","item":{"type":"message","id":"touch-final","role":"assistant","content":[{"type":"output_text","text":"Touch fixture" if title else "TOUCH_PTY_OK"}]}})
            emit({"type":"response.completed","response":{"id":f"touch-{primary}","usage":{"input_tokens":1,"output_tokens":1,"total_tokens":2}}})
        except (BrokenPipeError,ConnectionResetError): pass


def exercise(package, extended=False):
    binary=package/"bin/codex"
    with tempfile.TemporaryDirectory(prefix="codex-touch-pty-") as directory:
        root=Path(directory); state=root/"state";state.mkdir();workspace=root/"workspace";workspace.mkdir()
        model={"slug":"touch-fixture","display_name":"touch-fixture","description":"Local synthetic fixture","base_instructions":"Use only the local synthetic tools.",
               "default_reasoning_level":"medium","supported_reasoning_levels":[{"effort":level,"description":level} for level in ("low","medium","high")],
               "shell_type":"shell_command","visibility":"list","supported_in_api":True,"priority":0,
               "additional_speed_tiers":[],"service_tiers":[],"default_service_tier":None,"availability_nux":None,
               "upgrade":None,"default_reasoning_summary":"none","support_verbosity":False,"default_verbosity":None,
               "apply_patch_tool_type":None,"truncation_policy":{"mode":"bytes","limit":10000},
               "supports_image_detail_original":False,"context_window":272000,"tool_mode":"code_mode_only",
               "experimental_supported_tools":["request_user_input_async"]}
        catalog=root/"models.json";catalog.write_text(json.dumps({"models":[model]}))
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler);server.daemon_threads=True
        server.requests=[];server.continuation=threading.Event();server.release=threading.Event()
        server.interrupt_started=threading.Event();server.interrupt_release=threading.Event()
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        (state/"config.toml").write_text(f'''model = "touch-fixture"
model_catalog_json = {json.dumps(str(catalog))}
model_provider = "fixture"
approval_policy = "never"
sandbox_mode = "danger-full-access"
suppress_unstable_features_warning = true
[model_providers.fixture]
name = "local synthetic fixture"
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
[tui.keymap.editor]
insert_newline = "shift-enter"
[tui.keymap.global]
find_transcript = "ctrl-x f3"
[tui.keymap.agents]
search = "ctrl-x f4"
[tui.keymap.chat]
increase_reasoning_effort = "shift-up"
decrease_reasoning_effort = "shift-down"
[analytics]
enabled = false
[otel]
exporter = "none"
trace_exporter = "none"
metrics_exporter = "none"
[projects.{json.dumps(str(workspace))}]
trust_level = "trusted"
''')
        env={"PATH":"/usr/local/bin:/usr/bin:/bin","HOME":str(root),"CODEX_HOME":str(state),"LANG":"C.UTF-8",
             "TERM":"xterm-256color","NO_PROXY":"127.0.0.1,localhost","TMPDIR":str(root),"CODEX_TOUCH":"1"}
        master,slave=pty.openpty();saved=termios.tcgetattr(slave)
        screen=Screen(110,38)
        fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack("HHHH",38,110,0,0))
        process=subprocess.Popen([str(binary),"--dangerously-bypass-approvals-and-sandbox","Run the local touch fixture."],cwd=workspace,env=env,stdin=slave,stdout=slave,stderr=slave,start_new_session=True)
        raw=bytearray();answered={};started=time.monotonic();shortcut_phase=False
        probes={b"\x1b[6n":b"\x1b[1;1R",b"\x1b]11;?":b"\x1b]11;rgb:0000/0000/0000\x1b\\",b"\x1b]10;?":b"\x1b]10;rgb:ffff/ffff/ffff\x1b\\",b"\x1b[?u":b"\x1b[?0u"}
        def pump(timeout=.2):
            if select.select([master],[],[],timeout)[0]:
                try:data=os.read(master,65536)
                except OSError as error:
                    if error.errno==errno.EIO:return
                    raise
                raw.extend(data);screen.feed(data)
                for probe,reply in probes.items():
                    count=raw.count(probe);previous=answered.get(probe,0)
                    if count>previous:os.write(master,reply*(count-previous));answered[probe]=count
        def until(predicate,description,timeout=30):
            end=time.monotonic()+timeout
            while time.monotonic()<end:
                pump()
                if predicate():
                    print(f"{time.monotonic()-started:.1f}s: {description}: passed", flush=True)
                    return
                if process.poll() is not None:break
            raise AssertionError(description+f" (requests={len(server.requests)}, exit={process.poll()})\n"+screen.text()+"\nraw tail: "+repr(bytes(raw[-1200:])))
        def mouse(pos,code=0,up=False):os.write(master,f"\x1b[<{code};{pos[0]};{pos[1]}{'m' if up else 'M'}".encode())
        def click(label):
            until(lambda:screen.find(label),f"Missing {label}")
            if not shortcut_phase:
                pos=screen.find(label);mouse(pos);mouse(pos,up=True)
                return
            # The renderer may be between frames or processing queued model replies.
            # Click one stable painted target; never retry a cancelled/failed click.
            stable_since=time.monotonic();last=None;deadline=stable_since+5
            while time.monotonic()<deadline:
                pump(.05)
                pos=screen.find(label)
                current=(pos, "".join(screen.cells[pos[1]-1]) if pos else None, len(server.requests))
                if current!=last:stable_since=time.monotonic();last=current
                if pos and time.monotonic()-stable_since>=.25:
                    mouse(pos);mouse(pos,up=True)
                    return
            raise AssertionError(f"Hint did not settle: {label}\n"+screen.text())
        try:
            until(lambda:screen.find("3 questions") and server.continuation.is_set(),"No async summary",timeout=120)
            assert screen.mouse,"Mouse reporting must be enabled"
            click("3 questions")
            until(lambda:screen.find("1 of 3") and screen.find("submit"),"Summary did not expand")
            assert screen.mouse,"Expanded questions disabled mouse reporting"
            # Resize uses actual terminal signals. Locate the repaint, never fixed coordinates.
            screen.resize(42,32);fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack("HHHH",32,42,0,0));os.killpg(process.pid,signal.SIGWINCH)
            until(lambda:screen.find("Beta selected") and screen.find("submit"),"Resize lost choices")
            pos=screen.find("Beta selected");mouse(pos);mouse((pos[0]+1,pos[1]),32);mouse(pos,up=True)
            # A keyboard event provides a new observable repaint after the gesture.
            os.write(master,b"\x1b[B")
            until(lambda:screen.find("› 2. Beta selected") and screen.find("1 of 3"),"Drag submitted an answer")
            # Existing Shift navigation must work by tapping its text as well.
            click("next question")
            until(lambda:screen.find("2 of 3") and screen.find("Named answer"),"Next hint did not navigate")
            click("prev question")
            until(lambda:screen.find("1 of 3") and screen.find("Beta selected"),"Previous hint did not navigate")
            click("Beta selected")
            until(lambda:screen.find("1 of 2"),"Choice was not accepted")
            click("Other")
            os.write(master,b"\x1b[200~TOUCH_OTHER_NOTE\x1b[201~")
            until(lambda:screen.find("TOUCH_OTHER_NOTE"),"Other did not enter editing")
            click("submit")
            until(lambda:screen.find("Type your answer"),"Other answer was not accepted")
            os.write(master,b"\x1b[200~TOUCH_FREEFORM_NOTE\x1b[201~")
            until(lambda:screen.find("TOUCH_FREEFORM_NOTE"),"Freeform input missing")
            click("submit")
            # Wait for the TUI to accept the release before completing the model turn.
            # A turn ending first correctly recovers an unsent question draft.
            until(lambda: screen.find("Ask Codex to do anything"),
                  "Last answer was not accepted before turn completion")
            server.release.set()
            expected = ("Beta selected", "TOUCH_OTHER_NOTE", "TOUCH_FREEFORM_NOTE")
            def delivered():
                # Queued replies may start subsequent turns after the first final answer.
                users = [item for request in server.requests for item in request.get("input", [])
                         if item.get("role") == "user"]
                return all(answer in json.dumps(users) for answer in expected)
            until(lambda: delivered() and b"TOUCH_PTY_OK" in raw,
                  "Not all accepted answers were delivered as user input")
            # Drain the final queued model replies before beginning idle composer actions.
            settle_until=time.monotonic()+1
            while time.monotonic()<settle_until:pump(.05)
            shortcut_phase=True
            # At a narrow phone width, mode switching has a direct touch entry.
            until(lambda:screen.find("shift+tab mode"),"Idle mode hint missing")
            pos=screen.find("shift+tab mode")
            mouse(pos);mouse((pos[0]+1,pos[1]),32);mouse(pos,up=True)
            os.write(master,b"\x1b[200~DRAFT_FIRST\x1b[201~")
            until(lambda:screen.find("DRAFT_FIRST") and screen.find("new line"),"Draft lost newline entry")
            assert not screen.find("Plan mode"),"Dragging mode hint activated it"
            click("new line")
            os.write(master,b"\x1b[200~DRAFT_SECOND\x1b[201~")
            until(lambda:screen.find("DRAFT_SECOND"),"Second draft line missing")
            first,second=screen.find("DRAFT_FIRST"),screen.find("DRAFT_SECOND")
            assert first and second and second[1]>first[1],"Click did not insert a newline"
            assert not any("DRAFT_FIRST" in json.dumps(r) for r in server.requests),"Newline submitted draft"
            # Give the existing responsive reference enough height to expose all groups.
            screen.resize(140,45);fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack("HHHH",45,140,0,0));os.killpg(process.pid,signal.SIGWINCH)
            until(lambda:screen.find("for shortcuts") and screen.find("DRAFT_SECOND"),"Draft shortcuts entry missing")
            click("for shortcuts")
            until(lambda:screen.find("Keyboard shortcuts") and screen.find("Change mode"),"Help did not open with draft")
            click("close")
            until(lambda:not screen.find("Keyboard shortcuts") and screen.find("DRAFT_FIRST"),"Close lost draft")
            click("for shortcuts")
            click("Change mode")
            until(lambda:screen.find("Plan mode (") and not screen.find("Keyboard shortcuts"),"Help mode action failed")
            click("Plan mode")
            until(lambda:screen.find("shift+tab mode"),"Footer mode action failed")
            click("for shortcuts")
            click("More reasoning")
            until(lambda:not screen.find("Keyboard shortcuts"),"Reasoning action did not dismiss help")
            click("for shortcuts")
            click("New line")
            until(lambda:not screen.find("Keyboard shortcuts"),"Help newline action did not dismiss help")
            os.write(master,b"\x1b[200~DRAFT_THIRD\x1b[201~")
            until(lambda:screen.find("DRAFT_THIRD"),"Third draft line missing")
            assert screen.find("DRAFT_THIRD")[1]>screen.find("DRAFT_SECOND")[1],"Help newline did not edit draft"
            # A runtime two-stroke binding must travel through the app chord matcher.
            click("for shortcuts")
            click("Find text")
            until(lambda:screen.find("Find:") and not screen.find("Keyboard shortcuts"),"Chord did not open transcript search")
            os.write(master,b"\x1b")
            until(lambda:screen.find("DRAFT_THIRD") and screen.find("for shortcuts"),"Search close lost draft")
            if extended:
                click("for shortcuts")
                click("/keymap")
                until(lambda:screen.find("Type to search shortcuts"),"Customization hint did not open the keymap picker")
                click("esc")
                until(lambda:screen.find("DRAFT_THIRD") and screen.find("for shortcuts"),"Keymap cancel lost the draft")
                # Complete an actual pending prefix via its floating guide.
                os.write(master,b"\x18")
                until(lambda:screen.find("f3") and screen.find("Esc cancel"),"Pending chord guide missing")
                click("f3")
                until(lambda:screen.find("Find:"),"Floating guide tap did not complete the chord")
                os.write(master,b"\x1b")
                until(lambda:screen.find("DRAFT_THIRD") and screen.find("for shortcuts"),"Floating chord search close lost draft")
            # Submit using the help action, then inspect the actual outgoing model input.
            click("for shortcuts")
            click("Send message")
            def draft_request():
                for request in server.requests:
                    for item in request.get("input", []):
                        if item.get("role") != "user":continue
                        content=item.get("content", [])
                        text=content if isinstance(content,str) else "".join(part.get("text", "") for part in content)
                        if "DRAFT_FIRST\nDRAFT_SECOND\nDRAFT_THIRD" in text:return request
                return None
            until(lambda:draft_request() is not None,"Touch send did not deliver the exact multiline draft")
            assert draft_request().get("reasoning", {}).get("effort")=="high","Shift-up hint did not change reasoning"
            until(lambda:screen.find("shift+tab mode"),"Turn did not finish")
            # Exercise a true modal owner, including a runtime chord from its own help.
            os.write(master,b"\x1b[D")
            until(lambda:screen.find("Agent command center") and screen.find("? help"),"Command center did not open")
            click("Working ")
            until(lambda:screen.find("No matching tasks"),"Status tab tap did not filter")
            click("All ")
            until(lambda:not screen.find("No matching tasks"),"All tab did not restore tasks")
            click("? help")
            until(lambda:screen.find("Task shortcuts"),"Center help did not open")
            click("Search")
            until(lambda:screen.find("Search ›") and not screen.find("Task shortcuts"),"Center help chord did not start search")
            click("esc back")
            until(lambda:screen.find("? help") and not screen.find("Search ›"),"Center search back failed")
            click("? help")
            click("esc back")
            until(lambda:screen.find("Agent command center") and not screen.find("Task shortcuts"),"Center help back closed the whole view")
            click("enter open")
            until(lambda:screen.find("shift+tab mode") and not screen.find("Agent command center"),"Center open hint failed")
            if extended:
                # Complete a command by touch; Tab inserts it before Enter executes it.
                os.write(master,b"/res")
                until(lambda:screen.find("/resume"),"Resume completion missing")
                click("/resume")
                until(lambda:screen.find("› /resume"),"Command tap did not complete the draft")
                os.write(master,b"\r")
                until(lambda:screen.find("Resume a previous session") and screen.find("Run the local touch fixture."),"Resume picker missing")
                pos=screen.find("Run the local touch fixture.")
                mouse(pos);mouse((pos[0]+1,pos[1]),32);mouse(pos,up=True)
                end=time.monotonic()+.3
                while time.monotonic()<end:pump(.05)
                assert screen.find("Resume a previous session"),"Row drag resumed a session"
                click("Archived")
                until(lambda:screen.find("No sessions"),"Archived filter failed")
                click("Active")
                until(lambda:screen.find("Run the local touch fixture."),"Active filter did not restore the session")
                click("transcript")
                until(lambda:screen.find("T R A N S C R I P T"),"Preview hint did not open transcript")
                click("close")
                until(lambda:screen.find("Resume a previous session"),"Preview close hint failed")
                click("Run the local touch fixture.")
                until(lambda:not screen.find("Resume a previous session") and screen.find("shift+tab mode"),"Selected row tap did not resume")
                # A generic settings list uses its modal owner's original cancel route.
                os.write(master,b"\x1b[200~/model\x1b[201~")
                until(lambda:screen.find("› /model"),"Model command draft missing")
                os.write(master,b"\r")
                until(lambda:screen.find("Select Model") or screen.find("Select model"),"Model picker missing")
                click("esc")
                until(lambda:screen.find("shift+tab mode") and not screen.find("Select Model") and not screen.find("Select model"),"Model picker cancel hint failed")
            # Hold a fresh synthetic turn until the displayed interrupt hint is tapped.
            os.write(master,b"\x1b[200~TOUCH_HOLD_INTERRUPT\x1b[201~")
            until(lambda:screen.find("TOUCH_HOLD_INTERRUPT"),"Interrupt fixture draft missing")
            os.write(master,b"\r")
            until(lambda:server.interrupt_started.is_set() and screen.find("to interrupt"),"Held interrupt turn did not start")
            pos=screen.find("to interrupt")
            mouse(pos);mouse((pos[0]+1,pos[1]),32);mouse(pos,up=True)
            end=time.monotonic()+.5
            while time.monotonic()<end:pump(.05)
            assert screen.find("to interrupt"),"Dragging interrupted the turn"
            click("to interrupt")
            until(lambda:not screen.find("to interrupt") and screen.find("shift+tab mode"),"Interrupt hint did not stop the held turn")
            assert not server.interrupt_release.is_set(),"Fixture completed before the touch interrupt"
            server.interrupt_release.set()
            os.write(master,b"\x04");until(lambda:process.poll() is not None,"TUI did not exit")
            assert process.returncode==0,process.returncode
            assert termios.tcgetattr(slave)==saved,"TTY attributes not restored"
            assert not screen.mouse,"Mouse reporting not disabled on exit"
            if extended:
                # Re-enter through the CLI startup picker using only the fixture's persisted session.
                raw.clear();answered.clear();screen.resize(140,45)
                process=subprocess.Popen([str(binary),"resume"],cwd=workspace,env=env,stdin=slave,stdout=slave,stderr=slave,start_new_session=True)
                until(lambda:screen.find("Resume a previous session") and screen.find("Run the local touch fixture."),"Startup resume picker missing",timeout=60)
                assert screen.mouse,"Startup resume picker has no mouse reporting"
                click("Run the local touch fixture.")
                until(lambda:not screen.find("Resume a previous session") and screen.find("shift+tab mode"),"Startup row did not resume")
                os.write(master,b"\x04");until(lambda:process.poll() is not None,"Resumed TUI did not exit")
                assert process.returncode==0
                assert termios.tcgetattr(slave)==saved,"Resumed TTY attributes not restored"
                assert not screen.mouse,"Resumed mouse reporting not disabled"
                print("PASS: extended picker PTY (customization, floating chord, command completion, resume row/drag, archive filter, preview/close, modal cancel, startup resume).")
            print("PASS: touch PTY (expand, capture, resize, choice, Other, freeform, footer submit/navigation, draft newline/help/close, mode, reasoning, runtime chord, multiline send, delivery, agent center filter/help/chord/open/back, held turn interrupt, tty cleanup).")
        except BaseException:
            # Only the temporary fixture's isolated logs; never the user's Codex state.
            for diagnostic in state.rglob("*.log"):
                print(f"Fixture diagnostic {diagnostic.relative_to(state)}:\n" + diagnostic.read_text(errors="replace")[-12000:])
            raise
        finally:
            server.release.set()
            server.interrupt_release.set()
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
            os.close(master);os.close(slave)
            subprocess.run([str(binary),"app-server","daemon","stop"],env=env,cwd=workspace,capture_output=True,timeout=15,check=True)
            server.shutdown();server.server_close();thread.join(timeout=2)


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("package",type=Path)
    parser.add_argument("--extended",action="store_true",help="Exercise unreleased picker and modal touch controls")
    args=parser.parse_args()
    exercise(args.package.resolve(),extended=args.extended)
