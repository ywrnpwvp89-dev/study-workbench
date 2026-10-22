#!/usr/bin/env python3
"""Local evidence store and read-only chat collectors. Language reasoning is done by Codex."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid
import unicodedata

TZ = dt.timezone(dt.timedelta(hours=8))
ROOT = Path(os.environ.get('CHAT_WORK_ITEMS_HOME', str(Path.home()/'.local/share/chat-work-items')))
LARK = Path.home()/'.local/bin/lark-cli'
GB = Path.home()/'.local/bin/greenbubbles'
os.umask(0o077)


def dump(path, obj):
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')
    tmp.replace(path)


def db():
    (ROOT/'data').mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(ROOT/'data/messages.sqlite3')
    c.execute('CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, platform TEXT, account TEXT, chat TEXT, at TEXT, payload TEXT)')
    return c


def timestamp(value):
    if value is None or value == '':
        return None
    if isinstance(value, (int, float)) or str(value).replace('.', '', 1).isdigit():
        n = float(value)
        if n > 100000000000:
            n /= 1000
        return dt.datetime.fromtimestamp(n, TZ).isoformat(timespec='seconds')
    v = dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if not v.tzinfo:
        raise ValueError('Timestamp must include a timezone; preserve unverified UI dates as null')
    return v.astimezone(TZ).isoformat(timespec='seconds')


def window(days):
    end = dt.datetime.now(TZ).replace(microsecond=0)
    return (end-dt.timedelta(days=days)).isoformat(), end.isoformat()


def selected_window(a):
    if bool(a.start) != bool(a.end):
        raise ValueError('Provide both --start and --end when resuming')
    start, end = (timestamp(a.start), timestamp(a.end)) if a.start else window(a.days)
    if start > end:
        raise ValueError('Start must not follow end')
    return start, end


def run_json(argv, timeout=120):
    env = dict(os.environ, TZ='Asia/Shanghai', LARKSUITE_CLI_NO_UPDATE_NOTIFIER='1', LARKSUITE_CLI_NO_SKILLS_NOTIFIER='1')
    p = subprocess.run([str(x) for x in argv], capture_output=True, text=True, timeout=timeout, env=env)
    j = None
    # GreenBubbles writes machine errors to stdout, Lark to stderr.
    for raw in (p.stdout, p.stderr):
        try:
            candidate = json.loads(raw)
            if isinstance(candidate, dict):
                j = candidate
                break
        except ValueError:
            continue
    if j is None:
        raise RuntimeError('CLI failed or returned non-JSON (exit %s); inspect backend status locally' % p.returncode)
    if p.returncode or j.get('ok') is False:
        e = j.get('error', {})
        raise RuntimeError('CLI error: '+str(e.get('subtype') or e.get('code') or e.get('message') or 'unknown'))
    return j


def page(j, backend):
    d = j.get('data', j)
    if not isinstance(d, dict):
        raise ValueError('Unknown result envelope')
    # Official Lark shortcut and GreenBubbles query envelopes.
    rows = d.get('messages', d.get('items'))
    if not isinstance(rows, list):
        raise ValueError('Unknown message/list schema; refuse to report an empty success')
    pg = j.get('page', d.get('page', d)) if backend == 'wechat' else d
    field = 'hasMore' if backend == 'wechat' else 'has_more'
    if field not in pg:
        raise ValueError('Missing pagination metadata; coverage cannot be established')
    more = pg[field]
    if not isinstance(more, bool):
        raise ValueError('Invalid pagination flag')
    cursor = pg.get('nextCursor') if backend == 'wechat' else pg.get('page_token')
    if more and not cursor:
        raise ValueError('More pages exist but no continuation cursor was returned')
    return rows, more, cursor


def store(messages):
    c = db()
    with c:
        for m in messages:
            if m['platform'] not in ('wechat', 'feishu') or not m.get('chat') or not m.get('source_ref'):
                raise ValueError('platform, chat and observed source_ref are required')
            m['at'] = timestamp(m.get('at'))
            identity = [m['platform'], m.get('account', ''), m.get('native_id')]
            if not m.get('native_id'):
                identity += [m['chat'], m.get('at'), m.get('time_label'), m.get('sender'), m['text']]
                if not m.get('at'):
                    # Do not collapse repeated identical UI messages with unverified dates.
                    identity.append(m['source_ref'])
            m['id'] = m['platform']+':'+hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()[:24]
            m['synthetic_id'] = not bool(m.get('native_id'))
            c.execute('INSERT OR REPLACE INTO messages VALUES (?,?,?,?,?,?)',
                      (m['id'], m['platform'], m.get('account', ''), m['chat'], m.get('at'), json.dumps(m, ensure_ascii=False)))
    c.close()


def load_wechat_exclusions():
    """Load user-selected WeChat chats to omit from collection and summaries."""
    path = ROOT/'wechat-summary-exclusions.json'
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    entries = data.get('excluded_chats', []) if isinstance(data, dict) else []
    if not isinstance(entries, list):
        raise ValueError('Invalid WeChat exclusion list')
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('name'), str) or entry.get('match', 'exact') not in ('exact', 'prefix'):
            raise ValueError('Invalid WeChat exclusion entry')
    return entries


def normalized_chat_name(name):
    return ''.join(unicodedata.normalize('NFKC', str(name or '')).split()).casefold()


def is_excluded_wechat_chat(name, entries=None):
    entries = load_wechat_exclusions() if entries is None else entries
    actual = normalized_chat_name(name)
    if not actual:
        return False
    for entry in entries:
        target = normalized_chat_name(entry['name'])
        if entry.get('match', 'exact') == 'prefix':
            if actual.startswith(target):
                return True
        elif actual == target:
            return True
    return False


def text_content(x):
    if isinstance(x, str):
        try:
            v = json.loads(x)
            if isinstance(v, (dict, list)):
                return text_content(v)
        except ValueError:
            pass
        return x
    if isinstance(x, dict):
        if isinstance(x.get('text'), str):
            return x['text']
        # Keep structure when no plain text is available (cards/attachments).
        return json.dumps(x, ensure_ascii=False)
    return json.dumps(x, ensure_ascii=False)


def lark_message(m, account, source):
    sender = m.get('sender') or {}
    created = m.get('create_time')
    precision = 'native'
    if isinstance(created, str):
        try:
            # lark-cli 1.0.98 renders create_time in its process's local timezone.
            # run_json explicitly fixes TZ, rather than guessing UI timestamps.
            created = dt.datetime.strptime(created, '%Y-%m-%d %H:%M').replace(tzinfo=TZ).isoformat()
            precision = 'minute'
        except ValueError:
            pass
    return dict(platform='feishu', account=account,
                chat=m.get('chat_name') or m.get('chat_id') or 'unresolved chat',
                chat_id=m.get('chat_id'), native_id=m.get('message_id'),
                sender=sender.get('name') or sender.get('id') or 'unknown',
                at=created, time_precision=precision, raw_time_label=m.get('create_time'),
                message_url=m.get('message_app_link'), text=text_content(m.get('content', (m.get('body') or {}).get('content', ''))),
                deleted=m.get('deleted', False), msg_type=m.get('msg_type', m.get('message_type')),
                thread_id=m.get('thread_id'), mentions=m.get('mentions', []), source_ref=source)


def gb_message(m, account, chat, source):
    content = m.get('text', m.get('content', ''))
    if isinstance(content, dict):
        if isinstance(content.get('text'), str):
            content = content['text']
        elif isinstance(content.get('Text'), str):
            content = content['Text']
        elif isinstance(content.get('Quote'), dict):
            content = content['Quote'].get('reply_text') or '[引用回复正文未解码]'
        elif isinstance(content.get('System'), str):
            system = content['System']
            content = system if not system.lstrip().startswith('<') else '[系统事件]'
        else:
            # Do not export opaque attachment XML or embedded media credentials
            # into model context. Raw CLI pages retain the original locally.
            kind = next(iter(content), 'unknown')
            value = content.get(kind)
            title = value.get('title') if isinstance(value, dict) else None
            content = '['+kind+' 内容未读取'+(': '+title if isinstance(title, str) else '')+']'
    return dict(platform='wechat', account=account, chat=chat,
                native_id=m.get('id'), sender=m.get('senderDisplayName') or m.get('sender') or m.get('from') or 'unknown',
                at=m.get('createdAtUnix', m.get('timestamp', m.get('createTime', m.get('createdAt')))),
                text=text_content(content),
                deleted=m.get('deleted', False), msg_type=m.get('messageTypeLabel'),
                content_truncated=m.get('contentTruncated'), decode_state=m.get('contentDecodeState'), source_ref=source)


def collect_feishu(a):
    start, end = selected_window(a)
    if a.cursor and not a.start:
        raise ValueError('Resume cursor requires original --start and --end from coverage.json')
    run = ROOT/'data'/('feishu-'+uuid.uuid4().hex[:12])
    run.mkdir(parents=True)
    cov = dict(platform='feishu', account=a.account, start=start, end=end, status='partial',
               pages=0, messages=0, next_cursor=a.cursor, notices=[], limitations=['Current authorized tenant only; search API visibility; attachment bodies not fetched'])
    cursor, seen = a.cursor, set()
    try:
        for n in range(a.max_pages):
            args = [LARK, 'im', '+messages-search', '--as', 'user', '--query', '', '--start', start, '--end', end,
                    '--page-size', '50', '--format', 'json', '--no-reactions']
            if cursor:
                args += ['--page-token', cursor]
            j = run_json(args)
            raw = run/('%05d.json' % n)
            dump(raw, j)
            if j.get('identity') != 'user':
                raise ValueError('Refusing non-user identity')
            rows, more, next_cursor = page(j, 'feishu')
            if j.get('data', {}).get('notice'):
                cov['notices'].append(j['data']['notice'])
            store([lark_message(m, a.account, str(raw)) for m in rows])
            cov.update(pages=n+1, messages=cov['messages']+len(rows), next_cursor=next_cursor)
            if not more:
                cov['status'] = 'complete_search_results' if not cov['notices'] else 'partial'
                if cov['notices']:
                    cov['reason'] = 'Server returned notices; review before claiming coverage'
                break
            if next_cursor in seen:
                raise ValueError('Repeated pagination cursor')
            seen.add(next_cursor)
            cursor = next_cursor
        else:
            cov['reason'] = 'Page cap reached; resume using next_cursor and the SAME start/end bounds'
    except Exception as e:
        cov.update(status='error' if not cov['pages'] else 'partial', reason=str(e))
    dump(run/'coverage.json', cov)
    print(json.dumps(dict(coverage=str(run/'coverage.json'), **cov), ensure_ascii=False))
    return 0 if cov['status'] == 'complete_search_results' else 2


def collect_wechat(a):
    start, end = selected_window(a)
    run = ROOT/'data'/('wechat-'+uuid.uuid4().hex[:12])
    run.mkdir(parents=True)
    profile_args = ['--profile', a.profile] if getattr(a, 'profile', None) else []
    cov = dict(platform='wechat', account=a.account, profile=getattr(a, 'profile', None), start=start, end=end, status='partial',
               chats=[], warnings=[], limitations=['Local stored history only; attachments not transcribed'])
    if getattr(a, 'profile', None) == 'chatwork-clone-free':
        cov['limitations'].append('Independent clone source; daily-app history and full seven-day coverage require separate migration verification')
    try:
        run_json([GB, 'source', 'status'] + profile_args)
        cursor, seen, chats, enumeration_done = None, set(), [], False
        for n in range(a.max_pages):
            args = [GB, 'chats', '--limit', '500'] + profile_args
            if cursor:
                args += ['--cursor', cursor]
            j = run_json(args)
            dump(run/('chats-%05d.json' % n), j)
            rows, more, cursor = page(j, 'wechat')
            chats.extend(rows)
            cov['warnings'].extend(j.get('warnings', []))
            if j.get('consistency', {}).get('coverageComplete') is False:
                cov['warnings'].append('Incomplete conversation coverage')
            if not more:
                enumeration_done = True
                break
            if cursor in seen:
                raise ValueError('Repeated conversation cursor')
            seen.add(cursor)
        if not enumeration_done:
            raise ValueError('Conversation enumeration hit page cap')
        exclusions = load_wechat_exclusions()
        cov['excluded_chat_names'] = [entry['name'] for entry in exclusions]
        for chat in chats:
            cid = chat.get('id')
            if not cid:
                raise ValueError('Conversation has no ID')
            rec = dict(chat=chat.get('displayName') or cid, id=cid, status='partial', messages=0, next_cursor=None)
            cov['chats'].append(rec)
            if is_excluded_wechat_chat(rec['chat'], exclusions):
                rec.update(status='excluded_by_user', next_cursor=None)
                continue
            cursor, seen = None, set()
            for n in range(a.max_pages):
                args = [GB, 'messages', 'list', '--json', '--conversation', cid, '--limit', '500',
                        '--since', str(int(dt.datetime.fromisoformat(start).timestamp())),
                        '--until', str(int(dt.datetime.fromisoformat(end).timestamp()))] + profile_args
                if cursor:
                    args += ['--cursor', cursor]
                j = run_json(args)
                raw = run/(hashlib.sha256(cid.encode()).hexdigest()[:16]+'-%05d.json' % n)
                dump(raw, j)
                rows, more, cursor = page(j, 'wechat')
                store([gb_message(m, a.account, rec['chat'], str(raw)) for m in rows])
                rec.update(messages=rec['messages']+len(rows), next_cursor=cursor)
                cov['warnings'].extend(j.get('warnings', []))
                if j.get('consistency', {}).get('coverageComplete') is False:
                    cov['warnings'].append('Backend reports incomplete shard coverage')
                if not more:
                    rec['status'] = 'complete_local_results'
                    break
                if cursor in seen:
                    raise ValueError('Repeated message cursor')
                seen.add(cursor)
        if all(x['status'] in ('complete_local_results', 'excluded_by_user') for x in cov['chats']) and not cov['warnings']:
            cov['status'] = 'complete_local_results'
    except Exception as e:
        cov['reason'] = str(e)
    dump(run/'coverage.json', cov)
    print(json.dumps(dict(coverage=str(run/'coverage.json'), **cov), ensure_ascii=False))
    return 0 if cov['status'] == 'complete_local_results' else 2


def import_ui(a):
    j = json.loads(Path(a.file).expanduser().read_text())
    if not j.get('account'):
        raise ValueError('Record the observed account/tenant')
    messages = []
    for m in j['messages']:
        m.update(platform=j['platform'], account=j['account'], chat=j['chat'])
        if m.get('native_id'):
            raise ValueError('UI import must not invent native IDs')
        messages.append(m)
    store(messages)
    run = ROOT/'data'/('ui-'+uuid.uuid4().hex[:12])
    dump(run/'observations.json', j)
    coverage = dict(j.get('coverage', {}), platform=j['platform'], account=j['account'], chat=j['chat'],
                    messages=len(messages), observation=str(run/'observations.json'))
    # A UI import can establish one chat's interval, never whole-platform coverage.
    coverage['scope'] = 'observed_chat_only'
    dump(run/'coverage.json', coverage)
    print(json.dumps(dict(imported=len(messages), coverage=str(run/'coverage.json'))))


def context(a):
    start, end = window(a.days)
    c = db()
    all_rows = [json.loads(x[0]) for x in c.execute('SELECT payload FROM messages WHERE at>=? AND at<=? ORDER BY at,id', (start, end))]
    all_unknown = [json.loads(x[0]) for x in c.execute('SELECT payload FROM messages WHERE at IS NULL ORDER BY id')]
    exclusions = load_wechat_exclusions()
    excluded = lambda m: m.get('platform') == 'wechat' and is_excluded_wechat_chat(m.get('chat'), exclusions)
    excluded_rows = [m for m in all_rows if excluded(m)]
    excluded_unknown = [m for m in all_unknown if excluded(m)]
    rows = [m for m in all_rows if not excluded(m)]
    unknown = [m for m in all_unknown if not excluded(m)]
    c.close()
    out = Path(a.output).expanduser()
    chunks = []
    for i in range(0, len(rows), 500):
        p = out.with_name(out.stem+'-part-%03d.json' % (i//500)+out.suffix)
        dump(p, {'messages':rows[i:i+500]})
        chunks.append(str(p))
    coverages = [dict(path=str(p), **json.loads(p.read_text())) for p in sorted((ROOT/'data').glob('*/coverage.json'))]
    excluded_chats = sorted({m.get('chat') for m in excluded_rows + excluded_unknown if m.get('chat')})
    dump(out, dict(start=start, end=end, count=len(rows), chunks=chunks, unknown_date_messages=unknown, coverage=coverages,
                   excluded_wechat_messages=len(excluded_rows)+len(excluded_unknown), excluded_wechat_chats=excluded_chats))
    print(json.dumps(dict(context=str(out), messages=len(rows), chunks=chunks, unknown_dates=len(unknown),
                          excluded_wechat_messages=len(excluded_rows)+len(excluded_unknown), excluded_wechat_chats=excluded_chats)))


def render_tasks(a):
    items = json.loads(Path(a.file).expanduser().read_text())
    if not isinstance(items, list):
        raise ValueError('Tasks must be a JSON array')
    c = db()
    lines = ['# 聊天工作事项', '', '生成时间：'+dt.datetime.now(TZ).isoformat(timespec='minutes'), '',
             '本报告仅覆盖本地已读取的消息。读取范围与缺失见文末清单；任务由 Codex 根据上下文判断。', '']
    for i, t in enumerate(items, 1):
        if not t.get('title') or not t.get('evidence_ids'):
            raise ValueError('Every item needs a title and observed evidence')
        if t.get('status') not in ['pending','in_progress','done','cancelled','needs_confirmation']:
            raise ValueError('Unknown task status')
        evidence = []
        for eid in t['evidence_ids']:
            r = c.execute('SELECT payload FROM messages WHERE id=?', (eid,)).fetchone()
            if not r:
                raise ValueError('Unknown evidence ID: '+eid)
            m = json.loads(r[0])
            if m.get('deleted'):
                raise ValueError('Recalled/deleted messages cannot be task evidence')
            evidence.append(m)
        lines += ['## %d. %s' % (i, t['title']), '',
                  '- 负责人：'+str(t.get('owner') or '待确认'), '- 截止：'+str(t.get('due') or '未明确'),
                  '- 状态：'+t['status'], '- 判断：'+str(t.get('rationale') or ''), '']
        for m in evidence:
            lines += ['来源：%s / %s / %s / %s；证据 `%s`' % (m['platform'], m['chat'], m['sender'], m.get('at') or m.get('time_label') or '日期待核', m['id']), '',
                      '> '+m['text'].replace('\n','\n> '), '', '读取凭据：'+m['source_ref'], '']
            if m.get('message_url'):
                lines += ['[在飞书查看原消息]('+m['message_url']+')', '']
    lines += ['## 读取覆盖与限制', '']
    coverage_paths = [Path(a.coverage).expanduser()] if getattr(a, 'coverage', None) else sorted((ROOT/'data').glob('*/coverage.json'))
    for p in coverage_paths:
        j = json.loads(p.read_text())
        lines += ['- %s：%s；%s；[读取清单](%s)' % (j.get('platform'), j.get('status','partial'), j.get('reason') or '; '.join(j.get('limitations',[])), p)]
    out = Path(a.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines)+'\n')
    dump(out.with_suffix('.json'), items)
    c.close()
    print(json.dumps(dict(report=str(out), items=len(items))))


def doctor(a):
    result = {'default_days':7, 'timezone':'Asia/Shanghai', 'background_service':False}
    for name, binary, args in [('feishu', LARK, ['auth','status']), ('wechat', GB, ['source','status'])]:
        if not binary.exists():
            result[name] = {'installed':False, 'read_ready':False}
            continue
        try:
            j = run_json([binary]+args, timeout=20)
            if name == 'feishu':
                user = j.get('identities', j.get('data',{}).get('identities',{})).get('user',{})
                ready = user.get('status') in ('authenticated','logged_in','active','valid') or user.get('tokenStatus') == 'valid'
                result[name] = {'installed':True, 'read_ready':ready, 'identity':j.get('identity'), 'requires_live_read_verification':True}
            else:
                result[name] = {'installed':True, 'read_ready':True, 'requires_live_read_verification':True}
        except Exception as e:
            result[name] = {'installed':True, 'read_ready':False, 'reason':str(e)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('doctor').set_defaults(func=doctor)
    for cmd, func in [('collect-feishu',collect_feishu),('collect-wechat',collect_wechat)]:
        q = s.add_parser(cmd)
        q.add_argument('--days', type=int, default=7)
        q.add_argument('--start', help='ISO8601 with timezone; use original bounds for continuation')
        q.add_argument('--end', help='ISO8601 with timezone')
        q.add_argument('--account', default='current-authorized-profile' if cmd=='collect-feishu' else 'current-local-account')
        q.add_argument('--max-pages', type=int, default=200)
        if cmd == 'collect-feishu':
            q.add_argument('--cursor')
        else:
            q.add_argument('--profile', help='Explicit verified GreenBubbles source profile')
        q.set_defaults(func=func)
    q = s.add_parser('import-ui'); q.add_argument('file'); q.set_defaults(func=import_ui)
    q = s.add_parser('context'); q.add_argument('--days',type=int,default=7); q.add_argument('--output',required=True); q.set_defaults(func=context)
    q = s.add_parser('render-tasks'); q.add_argument('file'); q.add_argument('--output',required=True); q.add_argument('--coverage',help='Use this collection manifest rather than historical setup attempts'); q.set_defaults(func=render_tasks)
    a = p.parse_args()
    if hasattr(a,'days') and a.days <= 0 or hasattr(a,'max_pages') and a.max_pages <= 0:
        p.error('days/max-pages must be positive')
    try:
        return a.func(a) or 0
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
