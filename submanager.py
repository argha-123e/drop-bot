import datetime
import requests

from utils.constants import *
from utils.constants import OWO_PLANS

class SubscriptionManager:
    def __init__(self, db, webhook_url):
        
        self.db = db
        self.webhook_url = webhook_url

    # Fetch subscription info
    def get_sub(self, server_id: int):
        q = self.db.cur.execute("SELECT * FROM subscriptions WHERE server_id = ?", (server_id,))
        row = q.fetchone()
        return dict(row) if row else None

    # Create subscription
    def add_sub(self, server_id: int, sub_type: str, value: int, months: int = 0):
        db = self.db
        now = datetime.datetime.utcnow().isoformat()

        has_sub = db.exists("subscriptions", server_id=server_id)

        if not has_sub:
            # brand-new subscription
            end_date = None
            if sub_type == "monthly":
                end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=30 * months)).isoformat()
            elif sub_type == "trial":
                end_date = (datetime.datetime.utcnow() + datetime.timedelta(value)).isoformat() # value used as days
                trials_data = db.get_as_dict("trials", server_id=server_id)
                if trials_data:
                    if trials_data["trial"]:
                        return [False, "this server has/had trial before"]
                else:
                    db.insert(
                        "trials",
                        server_id=server_id,
                        trial=1
                        )

            db.insert(
                "subscriptions",
                server_id=server_id,
                sub_type=sub_type,
                value=value,
                end_date=end_date,
                created_at=now,
                months=months
            )
            
            self.check_subscriptions()
            return [True, "Subscription added.", db.get_as_dict("subscriptions", server_id=server_id)[0]]

        # if subscription already exists
        existing = db.get_as_dict("subscriptions", server_id=server_id)[0]

        old_type = existing["sub_type"]
        old_value = existing["value"]
        old_end = existing["end_date"]
        old_month = existing["months"] 

        # type mismatch → user must manually cancel
        if old_type != sub_type and old_value != value:
            return [False, "A different subscription type or tier already exists. Use `.cancel_sub` first or let it expire"]

        # -- monthly extension --
        if sub_type == "monthly":
            old_end_dt = datetime.datetime.fromisoformat(old_end)
            new_end = old_end_dt + datetime.timedelta(days=30 * months)

            db.update(
                "subscriptions",
                "server_id", server_id,
                value=value,
                end_date=new_end.isoformat(),
                months=old_month+months
            )
            self.check_subscriptions()
            return [True, "Monthly subscription extended.", db.get_as_dict("subscriptions", server_id=server_id)[0]]

        # -- revshare update --
        if sub_type == "revshare":
            db.update(
                "subscriptions",
                "server_id", server_id,
                value=value
            )
            self.check_subscriptions()
            return [True, "Revshare subscription updated.", db.get_as_dict("subscriptions", server_id=server_id)[0]]

    # Cancel subscription + send to webhook
    def cancel_sub(self, server_id: int):
        db = self.db
        if not db.exists("subscriptions", server_id=server_id):
            return [False, "No subscription exists."]

        sub = db.get_as_dict("subscriptions", server_id=server_id)[0]

        # Send webhook log
        requests.post(sub_WEBHOOK, json={
            "content": f"Subscription cancelled for server {server_id}\n```{sub}```"
        })

        # Delete subscription
        db.delete("subscriptions", "server_id", server_id)

        # Turn off subscription flag in servers table
        db.update("servers", "server_id", server_id, sub=0)

        self.check_subscriptions()
        return [True, "Subscription cancelled."]

    # Monthly reset check (call daily or every restart)
    def check_subscriptions(self):
        db = self.db

        # Fetch all subs and servers
        subs = {s["server_id"]: s for s in db.get_as_dict("subscriptions")}
        servers = db.get_server_ids()

        now = datetime.datetime.utcnow()

        for server_id in servers:
            if server_id not in subs:
                # no subscription → disable sub
                db.update("servers", "server_id", server_id, sub=0)
                continue

            sub = subs[server_id]
            sub_type = sub["sub_type"]
            end_date = sub["end_date"]

            active = True

            if sub_type == "monthly" or sub_type == "trial":
                if end_date is None:
                    active = False
                else:
                    end_dt = datetime.datetime.fromisoformat(end_date)
                    if now > end_dt:
                        active = False

            # Apply subscription status
            db.update("servers", "server_id", server_id, sub=1 if active else 0)




