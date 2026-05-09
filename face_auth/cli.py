"""
cli.py
------
Command-line interface for the Face Authentication System.
Provides a clean, menu-driven terminal UI for all operations.
"""

import sys
import logging
from datetime import datetime

from .database import init_db, list_users, delete_user, get_audit_log, log_event
from .recognition import enroll, verify

# --- Logging setup ---
logging.basicConfig(
    filename="logs/faceauth.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# --- Terminal colours ---
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    DIM    = "\033[2m"


BANNER = f"""
{C.CYAN}{C.BOLD}
  ███████╗ █████╗  ██████╗███████╗      █████╗ ██╗   ██╗████████╗██╗  ██╗
  ██╔════╝██╔══██╗██╔════╝██╔════╝     ██╔══██╗██║   ██║╚══██╔══╝██║  ██║
  █████╗  ███████║██║     █████╗       ███████║██║   ██║   ██║   ███████║
  ██╔══╝  ██╔══██║██║     ██╔══╝       ██╔══██║██║   ██║   ██║   ██╔══██║
  ██║     ██║  ██║╚██████╗███████╗     ██║  ██║╚██████╔╝   ██║   ██║  ██║
  ╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝    ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝
{C.RESET}{C.DIM}  Biometric Authentication System  |  AES-256 Encrypted  |  Liveness Detection
{C.RESET}"""

MENU = f"""
{C.BOLD}  ── MAIN MENU ──────────────────────────────{C.RESET}
  {C.GREEN}[1]{C.RESET}  Verify identity
  {C.GREEN}[2]{C.RESET}  Enrol a new user
  {C.GREEN}[3]{C.RESET}  List enrolled users
  {C.GREEN}[4]{C.RESET}  Delete a user
  {C.GREEN}[5]{C.RESET}  View audit log
  {C.GREEN}[6]{C.RESET}  Verify without liveness check {C.DIM}(testing only){C.RESET}
  {C.RED}[q]{C.RESET}  Quit
  {C.BOLD}────────────────────────────────────────────{C.RESET}
"""


def _separator():
    print(f"{C.DIM}  {'─' * 44}{C.RESET}")


def _header(title: str):
    print(f"\n{C.BOLD}{C.CYAN}  ── {title.upper()} {'─' * max(0, 38 - len(title))}{C.RESET}")


def cmd_verify(liveness: bool = True):
    _header("Identity Verification")
    success, name = verify(require_liveness=liveness)
    _separator()
    if success:
        print(f"\n  {C.GREEN}{C.BOLD}✓ ACCESS GRANTED{C.RESET}")
        print(f"  Welcome, {C.BOLD}{name}{C.RESET}.")
        print(f"  {C.DIM}Authenticated at {datetime.now().strftime('%H:%M:%S on %d %b %Y')}{C.RESET}\n")
    else:
        print(f"\n  {C.RED}{C.BOLD}✗ ACCESS DENIED{C.RESET}")
        print(f"  {C.DIM}Face not recognised or verification timed out.{C.RESET}\n")


def cmd_enroll():
    _header("Enrol New User")
    name = input(f"  {C.BOLD}Enter name for this user:{C.RESET} ").strip()
    if not name:
        print(f"  {C.YELLOW}[!] Name cannot be empty.{C.RESET}")
        return
    if not name.replace(" ", "").replace("-", "").replace("_", "").isalnum():
        print(f"  {C.YELLOW}[!] Name must contain only letters, numbers, spaces, hyphens, underscores.{C.RESET}")
        return
    enroll(name)


def cmd_list_users():
    _header("Enrolled Users")
    users = list_users()
    if not users:
        print(f"  {C.YELLOW}No users enrolled yet.{C.RESET}\n")
        return
    print(f"  {C.DIM}{'NAME':<25} {'ENROLLED AT'}{C.RESET}")
    _separator()
    for u in users:
        enrolled = u["enrolled_at"].replace("T", " ")[:19]
        print(f"  {C.BOLD}{u['name']:<25}{C.RESET} {C.DIM}{enrolled}{C.RESET}")
    print(f"\n  {C.DIM}Total: {len(users)} user(s){C.RESET}\n")


def cmd_delete_user():
    _header("Delete User")
    cmd_list_users()
    name = input(f"  {C.BOLD}Enter name to delete:{C.RESET} ").strip()
    if not name:
        return
    confirm = input(f"  {C.RED}Delete '{name}'? This cannot be undone. (yes/no):{C.RESET} ").strip().lower()
    if confirm != "yes":
        print(f"  {C.YELLOW}Cancelled.{C.RESET}")
        return
    if delete_user(name):
        print(f"  {C.GREEN}[✓] '{name}' deleted successfully.{C.RESET}")
        log_event("USER_DELETED", user=name, success=True)
    else:
        print(f"  {C.RED}[!] User '{name}' not found.{C.RESET}")


def cmd_audit_log():
    _header("Audit Log (Last 20 Events)")
    entries = get_audit_log(limit=20)
    if not entries:
        print(f"  {C.YELLOW}No audit events recorded yet.{C.RESET}\n")
        return
    print(f"  {C.DIM}{'TIMESTAMP':<22} {'EVENT':<22} {'USER':<20} {'OK'}{C.RESET}")
    _separator()
    for e in entries:
        ts = e["timestamp"].replace("T", " ")[:19]
        user = e["user"] or "—"
        ok = f"{C.GREEN}✓{C.RESET}" if e["success"] else f"{C.RED}✗{C.RESET}"
        print(f"  {C.DIM}{ts:<22}{C.RESET} {e['event']:<22} {user:<20} {ok}")
    print()


def main():
    # Ensure logs directory exists
    import os
    os.makedirs("logs", exist_ok=True)

    init_db()
    print(BANNER)

    handlers = {
        "1": lambda: cmd_verify(liveness=True),
        "2": cmd_enroll,
        "3": cmd_list_users,
        "4": cmd_delete_user,
        "5": cmd_audit_log,
        "6": lambda: cmd_verify(liveness=False),
    }

    while True:
        print(MENU)
        choice = input(f"  {C.BOLD}Select option:{C.RESET} ").strip().lower()

        if choice == "q":
            print(f"\n  {C.DIM}Goodbye.{C.RESET}\n")
            sys.exit(0)

        handler = handlers.get(choice)
        if handler:
            try:
                handler()
            except KeyboardInterrupt:
                print(f"\n  {C.YELLOW}[!] Interrupted. Returning to menu.{C.RESET}")
            except Exception as e:
                logger.exception("Unexpected error in handler")
                print(f"\n  {C.RED}[!] Unexpected error: {e}{C.RESET}")
        else:
            print(f"  {C.YELLOW}[!] Invalid option. Please choose 1–6 or q.{C.RESET}")


if __name__ == "__main__":
    main()
