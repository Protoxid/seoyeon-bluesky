"""Explicit operator tools. No outbound network requests or social messages."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("pending", help="List delivery IDs and reserved costs without private content")
    export = commands.add_parser("export-work", help="Export public creative artifacts only")
    export.add_argument("directory", type=Path)
    billing = commands.add_parser("reconcile-cost", help="Apply a cost verified in the provider dashboard")
    billing.add_argument("reservation_id")
    billing.add_argument("actual_cost", type=float)
    billing.add_argument("--evidence", required=True, help="Provider receipt/reference; no secrets")
    resolve = commands.add_parser("resolve-delivery", help="Record a manually verified delivery or abandon an uncertain action")
    resolve.add_argument("action_id")
    resolve.add_argument("--receipt", help="Verified remote URI or message ID")
    resolve.add_argument("--abandon", action="store_true")
    resolve.add_argument("--evidence", required=True)
    args = parser.parse_args()
    from agent.config import DATA_DIR
    from agent.storage import file_lock, read_json
    with file_lock(DATA_DIR / "runtime"):
        from agent.vault import vault
        if vault.enc_file.exists() and not vault.load_vault():
            return 1
        from agent.delivery import Outbox
        from agent.budget_manager import budget_manager
        outbox = Outbox()
        if args.command == "pending":
            print(json.dumps({"deliveries": {key: {"endpoint": item["endpoint"], "status": item["status"]}
                  for key, item in outbox.pending().items()}, "reservations": budget_manager.get_active_reservations()}, indent=2))
        elif args.command == "export-work":
            from agent.continuity import ContinuityStore
            args.directory.mkdir(parents=True, exist_ok=True)
            count = 0
            for key, item in ContinuityStore().load()["artifacts"].items():
                if item["scope"] != "public":
                    continue
                import hashlib
                filename = hashlib.sha256(key.encode()).hexdigest()[:16] + ".md"
                (args.directory / filename).write_text(
                    f'# {item["title"]}\n\nFictional AI persona creative work. Version {item["version"]}.\n\n'
                    + item["content"] + "\n\nEvidence IDs: " + ", ".join(item["source_ids"]) + "\n", encoding="utf-8")
                count += 1
            print(f"Exported {count} public creative artifacts.")
        elif args.command == "reconcile-cost":
            reservation = budget_manager.get_active_reservations().get(args.reservation_id)
            if not reservation:
                parser.error("Unknown active reservation")
            budget_manager.reconcile(args.reservation_id, args.actual_cost,
                model=reservation.get("model", ""), action_type=reservation.get("action_type", "llm_generation"),
                details="operator verified: " + args.evidence)
        elif args.command == "resolve-delivery":
            if bool(args.receipt) == bool(args.abandon):
                parser.error("Choose exactly one of --receipt and --abandon")
            item = read_json(outbox.path, {}).get(args.action_id)
            if not item or item["status"] not in {"prepared", "uncertain"}:
                parser.error("Unknown or already resolved action")
            receipt = {"uri" if args.receipt and args.receipt.startswith("at://") else "id": args.receipt}
            outbox.update(args.action_id, status="abandoned" if args.abandon else "delivered",
                          receipt=None if args.abandon else receipt, operator_evidence=args.evidence)
        vault.save_vault()
    return 0


if __name__ == "__main__":
    sys.exit(main())
