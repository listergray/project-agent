"""Offline submission regressions, including uploader resets and lost browsers."""
from __future__ import annotations

import tempfile
import unittest
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from playwright.async_api import async_playwright

from app import jobs, main, publisher, scanner
from app.publish_confirmation import find_work, is_publish_request, submission_evidence

logging.getLogger().setLevel(logging.WARNING)


class EvidenceTests(unittest.TestCase):
    def test_only_a_publish_post_and_business_work_id_confirm_submission(self):
        self.assertTrue(is_publish_request('https://creator.douyin.com/web/api/media/aweme/create/', 'POST'))
        self.assertFalse(is_publish_request('https://creator.douyin.com/web/api/media/upload/', 'POST'))
        self.assertFalse(is_publish_request('https://creator.douyin.com/web/api/media/aweme/create/', 'GET'))
        self.assertFalse(is_publish_request('https://other.example/aweme/create/', 'POST'))
        self.assertIsNone(submission_evidence({'status_code': 0}))
        self.assertIsNone(submission_evidence({'status_code': 0, 'data': {'video_id': '123456789'}}))
        self.assertTrue(submission_evidence({'status_code': 0, 'aweme': {'aweme_id': '123456789'}})['ok'])
        self.assertFalse(submission_evidence({'status_code': 1, 'status_msg': '拒绝'})['ok'])

    def test_uncertain_submission_is_needs_review_not_failure_or_success(self):
        self.assertEqual(main.publish_result_status({'ok': True}), 'SUCCESS')
        self.assertEqual(main.publish_result_status({'ok': False, 'unconfirmed': True}), 'NEEDS_REVIEW')
        self.assertEqual(main.publish_result_status({'ok': False}), 'FAILED')

    def test_needs_review_is_deduplicated_and_excluded_from_scan_without_db(self):
        old_data = jobs.settings.data_dir
        with tempfile.TemporaryDirectory() as temp:
            jobs.settings.data_dir = temp
            try:
                first, _ = jobs.get_or_create_publish_job({'ep': 36, 'status': 'NEEDS_REVIEW'})
                same, created = jobs.get_or_create_publish_job({'ep': 36, 'status': 'RUNNING'})
                self.assertFalse(created)
                self.assertEqual(first['id'], same['id'])
                (Path(temp) / '技术栈EP.36教程.mp4').write_bytes(b'offline fixture')
                with patch('app.db.published_eps', side_effect=RuntimeError('offline')):
                    self.assertEqual(scanner.scan_videos(temp, min_ep=36), [])
            finally:
                jobs.settings.data_dir = old_data


class ConfirmationBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.pw = await async_playwright().start()
        self.addAsyncCleanup(self.pw.stop)
        self.browser = await self.pw.chromium.launch(headless=True)
        self.addAsyncCleanup(self.browser.close)
        self.page = await self.browser.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(error))

    async def editor(self, action):
        body = '''<input placeholder="填写作品标题" value="目标视频">
          <button id="publish">发布</button><script>window.clicks=0;
          document.querySelector('#publish').onclick=async()=>{window.clicks++;ACTION};</script>'''.replace('ACTION', action)

        async def route(request):
            if is_publish_request(request.request.url, request.request.method):
                await request.fulfill(json={'status_code': 0, 'aweme': {'aweme_id': '1234567890123'}})
            else:
                await request.fulfill(content_type='text/html; charset=utf-8', body=body)
        await self.page.route('**/*', route)
        await self.page.goto('https://creator.douyin.com/creator-micro/content/post/video')

    async def test_success_notice_on_upload_page_finishes_without_reclick(self):
        await self.editor('history.pushState({},"","/creator-micro/content/upload");document.body.innerHTML="<p>发布成功</p><button>上传视频</button>";')
        submitted = []
        result = await publisher._click_publish_and_confirm(self.page, wait_sec=1, expected_title='目标视频', on_submit=lambda: submitted.append(True))
        self.assertTrue(result['ok'], result)
        self.assertEqual(await self.page.evaluate('window.clicks'), 1)
        self.assertEqual(len(submitted), 1)

    async def test_reset_upload_checks_the_matching_work(self):
        await self.editor('history.pushState({},"","/creator-micro/content/upload");document.body.innerHTML="<button>上传视频</button>";')
        with patch.object(publisher, 'check_management', new=AsyncMock(return_value={'source': 'content_manage', 'title': '目标视频', 'status': '审核中'})) as check:
            result = await publisher._click_publish_and_confirm(self.page, wait_sec=1, expected_title='目标视频')
        self.assertTrue(result['ok'], result)
        check.assert_awaited_once()
        self.assertEqual(await self.page.evaluate('window.clicks'), 1)

    async def test_empty_upload_alone_never_counts_as_success(self):
        await self.editor('history.pushState({},"","/creator-micro/content/upload");document.body.innerHTML="<button>上传视频</button>";')
        with patch.object(publisher, 'check_management', new=AsyncMock(return_value=None)):
            result = await publisher._click_publish_and_confirm(self.page, wait_sec=1, expected_title='目标视频')
        self.assertFalse(result['ok'])
        self.assertTrue(result['unconfirmed'])
        self.assertEqual(await self.page.evaluate('window.clicks'), 1)

    async def test_editor_timeout_does_not_click_publish_again(self):
        await self.editor('')
        with patch.object(publisher, '_save_debug_shot', new=AsyncMock()):
            result = await publisher._click_publish_and_confirm(self.page, wait_sec=0.2, expected_title='目标视频')
        self.assertTrue(result['unconfirmed'])
        self.assertEqual(await self.page.evaluate('window.clicks'), 1)

    async def test_business_response_finishes_without_management_redirect(self):
        await self.editor('await fetch("/web/api/media/aweme/create/",{method:"POST"});')
        result = await publisher._click_publish_and_confirm(self.page, wait_sec=3, expected_title='目标视频')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['evidence']['workId'], '1234567890123')

    async def test_management_requires_this_title_and_a_non_draft_status(self):
        await self.editor('')
        await self.page.evaluate('history.pushState({},"","/creator-micro/content/manage")')
        await self.page.set_content('<article><span>目标视频</span><p>审核中</p></article>')
        self.assertIsNotNone(await find_work(self.page, '目标视频', timeout_sec=0))
        self.assertIsNone(await find_work(self.page, '另一条视频', timeout_sec=0))
        await self.page.set_content('<article><span>目标视频</span><p>草稿</p></article><article>另一条 已发布</article>')
        self.assertIsNone(await find_work(self.page, '目标视频', timeout_sec=0))
        await self.page.set_content('<div role="list"><article><span>目标视频</span></article><article>另一条 已发布</article></div>')
        self.assertIsNone(await find_work(self.page, '目标视频', timeout_sec=0))

    async def test_browser_cleanup_does_not_override_result(self):
        context = SimpleNamespace(close=AsyncMock(side_effect=RuntimeError('already closed')))
        await publisher._close_publish_context(context)
        context.close.assert_awaited_once()

    async def test_review_episode_is_rejected_before_starting_another_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            video = Path(temp) / '技术栈EP.36教程.mp4'
            video.write_bytes(b'offline')
            with patch.object(jobs, 'episodes_needing_review', return_value={36}):
                with self.assertRaises(HTTPException) as raised:
                    await main.publish(main.PublishRequest(videoPath=str(video)))
            self.assertEqual(raised.exception.status_code, 409)

    async def test_frontend_continues_polling_and_stops_on_needs_review(self):
        html = (Path(__file__).resolve().parents[1] / 'web/index.html').read_text(encoding='utf-8')
        async def route(request):
            if request.request.resource_type == 'document':
                await request.fulfill(content_type='text/html; charset=utf-8', body=html)
            else:
                await request.fulfill(json={'videoDir': '', 'list': []})
        await self.page.route('**/*', route)
        await self.page.goto('http://offline.test/')
        await self.page.evaluate('''() => {
            window.pollCalls=0; window.messages=[];
            sleep=async()=>{}; loadJobs=async()=>{}; toast=msg=>messages.push(msg);
            api=async()=>({status:++pollCalls<122?'RUNNING':'NEEDS_REVIEW',message:'待核对'});
        }''')
        await self.page.evaluate("pollJob('offline')")
        self.assertEqual(await self.page.evaluate('window.pollCalls'), 122)
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
