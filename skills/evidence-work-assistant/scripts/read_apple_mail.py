#!/usr/bin/env python3
"""Read recent Apple Mail metadata and selected bodies, without changing mail state."""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time

OSASCRIPT = "/usr/bin/osascript"


def refresh_mail():
    """Launch Mail and request fresh mail for all accounts before listing."""
    subprocess.run(["/usr/bin/open", "-a", "Mail"], check=True, capture_output=True, timeout=15)
    p = subprocess.run([OSASCRIPT, "-e", 'tell application "Mail" to check for new mail'],
                       capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError((p.stderr or "Mail refresh failed").strip()[:500])
    time.sleep(20)
    return {"requested": True, "wait_seconds": 20,
            "limitation": "Mail refresh is asynchronous; delivery/synchronization completion is not guaranteed"}


def run_js(source, timeout=15):
    p = subprocess.run([OSASCRIPT, "-l", "JavaScript", "-e", source], capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout or "Apple Mail script failed").strip()[:500])
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError("Apple Mail returned invalid JSON") from e


def list_messages(days, limit):
    refresh = refresh_mail()
    source = f'''const Mail=Application("Mail");
const cutoff=new Date(Date.now()-{days}*86400000);
const accounts=Mail.accounts();
const rows=[];
const excluded=["trash","deleted messages","deleted items","junk","spam","drafts","outbox","垃圾邮件","垃圾箱","废纸篓","已删除邮件","草稿","发件箱"];
for(let ai=0;ai<accounts.length;ai++) {{
  const boxes=accounts[ai].mailboxes();
  for(let bi=0;bi<boxes.length;bi++) {{
    let boxName="";
    try {{ boxName=String(boxes[bi].name()||""); }} catch(e) {{ continue; }}
    const folded=boxName.trim().toLowerCase();
    if(excluded.some(x=>folded===x || folded.endsWith("/"+x))) continue;
    try {{
      const messages=boxes[bi].messages.whose({{dateReceived:{{_greaterThan:cutoff}}}})();
      for(const m of messages) {{
        try {{
          const id=Number(m.id());
          const rawDate=String(m.dateReceived());
          const date=new Date(rawDate);
          if(!Number.isFinite(date.getTime())) continue;
          rows.push({{account_index:ai,account_label:"账户"+(ai+1),mailbox_index:bi,mailbox:boxName,
                     message_id:id,date_received:date.toISOString(),sender:String(m.sender()||""),
                     subject:String(m.subject()||"")}});
        }} catch(e) {{}}
      }}
    }} catch(e) {{}}
  }}
}}
const seen=new Set();
const unique=rows.filter(x=>{{const k=x.account_index+":"+x.message_id;if(seen.has(k))return false;seen.add(k);return true;}});
unique.sort((a,b)=>b.date_received.localeCompare(a.date_received));
const capped=unique.slice(0,{limit});
JSON.stringify({{account_count:accounts.length,days:{days},count:capped.length,total_found:unique.length,truncated:unique.length>capped.length,
  attachments:"metadata only; attachment bodies not fetched",items:capped}});'''
    data = run_js(source, timeout=90)
    data["refresh"] = refresh
    for item in data.get("items", []):
        digest = hashlib.sha256(f"{item['account_index']}:{item['message_id']}:{item['date_received']}".encode()).hexdigest()[:24]
        item["evidence_id"] = "mail:" + digest
        item["selector"] = f"{item['account_index']}:{item['mailbox_index']}:{item['message_id']}"
    return data


def read_message(selector, max_chars):
    try:
        ai, bi, mid = (int(x) for x in selector.split(":"))
    except Exception as e:
        raise ValueError("Selector must be account_index:mailbox_index:message_id") from e
    source = f'''const Mail=Application("Mail");
const matches=Mail.accounts()[{ai}].mailboxes()[{bi}].messages.whose({{id:{mid}}})();
if(matches.length!==1)throw Error("Message selector is absent or ambiguous; refresh the mail index");
const m=matches[0];
const body=String(m.content()||"");
const rawDate=String(m.dateReceived());
const date=new Date(rawDate);
JSON.stringify({{message_id:Number(m.id()),date_received:date.toISOString(),sender:String(m.sender()||""),
  subject:String(m.subject()||""),content:body.slice(0,{max_chars}),truncated:body.length>{max_chars}}});'''
    return run_js(source, timeout=12)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("list", help="List recent message headers across configured accounts")
    q.add_argument("--days", type=int, required=True)
    q.add_argument("--limit", type=int, default=2000)
    r = sub.add_parser("read", help="Read selected message bodies by selectors from list output")
    r.add_argument("--selector", action="append", required=True)
    r.add_argument("--max-chars", type=int, default=20000)
    a = p.parse_args()
    if a.command == "list":
        if not 1 <= a.days <= 365 or not 1 <= a.limit <= 10000:
            p.error("days must be 1-365 and limit 1-10000")
        print(json.dumps(list_messages(a.days, a.limit), ensure_ascii=False))
        return
    if not 1 <= a.max_chars <= 100000:
        p.error("max-chars must be 1-100000")
    results = []
    for selector in a.selector:
        try:
            item = read_message(selector, a.max_chars)
            item["selector"] = selector
            item["ok"] = True
        except (RuntimeError, subprocess.TimeoutExpired, ValueError) as e:
            item = {"selector": selector, "ok": False, "error": "timeout" if isinstance(e, subprocess.TimeoutExpired) else str(e)}
        results.append(item)
    print(json.dumps({"messages": results}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        print(json.dumps({"ok": False, "error": "timeout" if isinstance(e, subprocess.TimeoutExpired) else str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
