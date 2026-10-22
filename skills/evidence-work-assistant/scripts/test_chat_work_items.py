"""Synthetic regression checks; never touch live chats or real credentials."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import chat_work_items as app


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.override = patch.object(app, 'ROOT', self.root)
        self.override.start()

    def tearDown(self):
        self.override.stop()
        self.temp.cleanup()

    def msg(self, native='m1', at='2026-10-16T09:00:00+08:00', text='明天交稿'):
        return dict(platform='feishu', account='test-tenant', chat='test', sender='A', native_id=native,
                    at=at, text=text, source_ref='synthetic-fixture.json')

    def test_repeated_collection_updates_same_message(self):
        app.store([self.msg()])
        app.store([self.msg(text='已取消')])
        c = app.db()
        rows = c.execute('SELECT payload FROM messages').fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0][0])['text'], '已取消')
        c.close()

    def test_identical_ui_text_at_distinct_times_remains_distinct(self):
        app.store([self.msg(None), self.msg(None, at='2026-10-16T09:01:00+08:00')])
        c = app.db()
        self.assertEqual(c.execute('SELECT COUNT(*) FROM messages').fetchone()[0], 2)
        c.close()

    def test_unknown_schema_and_missing_cursor_fail_closed(self):
        for j in [{'data':{}}, {'data':{'messages':[],'has_more':True}}, {'data':{'messages':[]}}]:
            with self.assertRaises(ValueError):
                app.page(j, 'feishu')

    def test_all_pages_are_saved_and_failed_later_page_is_partial(self):
        page1 = {'ok':True,'identity':'user','data':{'messages':[
            {'message_id':'m1','chat_id':'c1','sender':{'name':'A'},'create_time':'1792112400000','content':'{"text":"todo"}'}],
            'has_more':True,'page_token':'cursor-2'}}
        args = argparse.Namespace(days=7, start=None, end=None, cursor=None, max_pages=10, account='test')
        with patch.object(app,'run_json',side_effect=[page1,RuntimeError('expired_login')]), contextlib.redirect_stdout(io.StringIO()):
            code = app.collect_feishu(args)
        cov = json.loads(next((self.root/'data').glob('*/coverage.json')).read_text())
        self.assertEqual(code,2)
        self.assertEqual(cov['status'],'partial')
        self.assertEqual(cov['next_cursor'],'cursor-2')
        self.assertEqual(cov['messages'],1)

    def test_bot_identity_does_not_pass_as_personal_history(self):
        j = {'ok':True,'identity':'bot','data':{'messages':[],'has_more':False}}
        args = argparse.Namespace(days=7,start=None,end=None,cursor=None,max_pages=1,account='test')
        with patch.object(app,'run_json',return_value=j), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.collect_feishu(args),2)

    def test_full_pagination_finishes(self):
        args = argparse.Namespace(days=7,start=None,end=None,cursor=None,max_pages=2,account='test')
        pages = [{'ok':True,'identity':'user','data':{'messages':[],'has_more':True,'page_token':'next'}},
                 {'ok':True,'identity':'user','data':{'messages':[],'has_more':False}}]
        with patch.object(app,'run_json',side_effect=pages) as call, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.collect_feishu(args),0)
        self.assertIn('next',call.call_args_list[1].args[0])

    def test_greenbubbles_real_struct_timestamp_and_pagination(self):
        m = app.gb_message({'id':'opaque','createdAtUnix':1792112400,'content':{'text':'hello'},'senderDisplayName':'A'},'test','chat','fixture')
        self.assertEqual(app.timestamp(m['at']), '2026-10-16T09:00:00+08:00')
        self.assertEqual(m['text'],'hello')
        self.assertEqual(app.page({'ok':True,'items':[],'page':{'hasMore':False}},'wechat'),([],False,None))

    def test_lark_cli_local_rendered_time_uses_controlled_process_timezone(self):
        m = app.lark_message({'create_time':'2026-10-16 11:32','sender':{},'content':'hello'}, 'test', 'fixture')
        self.assertEqual(app.timestamp(m['at']), '2026-10-16T11:32:00+08:00')
        self.assertEqual(m['time_precision'], 'minute')

    def test_tagged_wechat_text_and_opaque_attachment_handling(self):
        m = app.gb_message({'id':'a','content':{'Text':'今天交稿'}}, 'test','chat','fixture')
        self.assertEqual(m['text'], '今天交稿')
        m = app.gb_message({'id':'b','content':{'Emoji':'<xml aeskey="synthetic-private" />'}}, 'test','chat','fixture')
        self.assertNotIn('synthetic-private', m['text'])
        self.assertIn('未读取', m['text'])

    def test_unknown_or_recalled_evidence_cannot_be_rendered(self):
        m = self.msg(); m['deleted']=True; app.store([m])
        for eid in [m['id'],'does-not-exist']:
            f = self.root/'tasks.json'
            f.write_text(json.dumps([{'title':'unsafe','status':'pending','evidence_ids':[eid]}]))
            with self.assertRaises(ValueError):
                app.render_tasks(argparse.Namespace(file=str(f),output=str(self.root/'report.md')))
        self.assertFalse((self.root/'report.md').exists())

    def test_naive_timestamp_does_not_get_invented_timezone(self):
        with self.assertRaises(ValueError):
            app.timestamp('2026-10-16T09:00:00')


if __name__ == '__main__':
    unittest.main()
