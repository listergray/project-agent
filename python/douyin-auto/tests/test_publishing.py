"""Offline regressions: a fresh browser, synthetic forms, no account or uploads."""
from __future__ import annotations

import asyncio
import base64
import json
import struct
import tempfile
import unittest
import zlib
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from playwright.async_api import async_playwright

from app import jobs, publisher
from app.browser_gate import BrowserGate
from app.cover_check import collect_cover_state


def image_data() -> str:
    def chunk(name, data):
        return struct.pack('!I', len(data)) + name + data + struct.pack('!I', zlib.crc32(name + data))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 48, 48, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress((b'\x00' + b'\x20\x90\xa0' * 48) * 48)) + chunk(b'IEND', b'')
    return 'data:image/png;base64,' + base64.b64encode(png).decode()


PNG = image_data()


def form(*, vertical=True, horizontal=True, background=False, tip='') -> str:
    h = f'<img src="{PNG}">' if horizontal else '<span>选择封面</span>'
    v = (f'<div class="preview" style="background-image:url({PNG})"></div>' if background
         else f'<img src="{PNG}">') if vertical else '<span>选择封面</span>'
    return f'''<style>
      .covers {{display:flex; gap:10px}} .card {{width:160px}}
      .h img {{width:160px;height:120px}} .v {{width:90px}}
      .v img,.preview {{width:90px;height:120px}} .preview {{background-size:cover}}
    </style>
    <div style="display:none">竖封面3:4</div>
    <input placeholder="填写作品标题" value="测试标题">
    <div contenteditable="true" data-placeholder="添加作品简介">#ai编程 #干货</div>
    <section class="covers"><div class="card h" id="h">{h}<div>横封面4:3</div></div>
    <div class="card v" id="v">{v}<div>竖封面3:4</div></div>
    <div>AI智能推荐封面生成中<img src="{PNG}" width="120" height="120"></div></section>
    <aside><img src="{PNG}" width="160" height="160">账号头像</aside><p>{tip}</p>'''


class CoverTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_data = publisher.settings.data_dir
        self.old_timeout = publisher.settings.cover_verify_timeout_ms
        publisher.settings.data_dir = self.temp.name
        publisher.settings.cover_verify_timeout_ms = 3000
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        # Tests must remain offline even if an image/selector is accidentally changed.
        await self.page.route('http**/*', lambda route: route.abort())

    async def asyncTearDown(self):
        await self.browser.close()
        await self.pw.stop()
        publisher.settings.data_dir = self.old_data
        publisher.settings.cover_verify_timeout_ms = self.old_timeout
        self.temp.cleanup()

    async def load(self, html):
        await self.page.set_content(html)
        await self.page.wait_for_function('Array.from(document.images).every(i => i.complete)')

    async def test_loaded_images_and_hidden_duplicate_labels(self):
        await self.load(form())
        state = await collect_cover_state(self.page)
        self.assertTrue(state['v']['ok'])
        self.assertTrue(state['h']['ok'])

    async def test_css_background_on_preview_and_card_itself(self):
        await self.load(form(background=True))
        # CSS images have their own load event, independent of document.images.
        await collect_cover_state(self.page)
        await self.page.wait_for_timeout(50)
        self.assertTrue((await collect_cover_state(self.page))['v']['ok'])
        await self.page.locator('#v').evaluate(
            '(el, png) => {el.innerHTML="竖封面3:4";el.style.cssText=`height:120px;background-image:url(${png})`}', PNG)
        self.assertTrue((await collect_cover_state(self.page))['v']['ok'])

    async def test_broken_css_image_is_not_a_cover(self):
        await self.load(form(vertical=False))
        await self.page.locator('#v').evaluate('''el => {
            el.insertAdjacentHTML('afterbegin', '<div class="preview" style="background-image:url(data:image/png;base64,broken)"></div>');
        }''')
        self.assertFalse((await collect_cover_state(self.page))['v']['ok'])
        await self.page.wait_for_timeout(50)
        self.assertFalse((await collect_cover_state(self.page))['v']['ok'])

    async def test_separate_caption_row_matches_each_cover_by_geometry(self):
        await self.load(f'''<section style="width:600px">
          <div style="display:flex;gap:10px"><img src="{PNG}" style="width:160px;height:120px">
          <img src="{PNG}" style="width:90px;height:120px"></div>
          <div style="display:flex;gap:10px"><span style="width:160px">横封面4:3</span>
          <span style="width:90px">竖封面3:4</span></div></section>''')
        state = await collect_cover_state(self.page)
        self.assertTrue(state['v']['ok'])
        self.assertTrue(state['h']['ok'])

    async def test_missing_vertical_cannot_borrow_horizontal_or_avatar(self):
        await self.load(form(vertical=False))
        state = await collect_cover_state(self.page)
        self.assertFalse(state['v']['ok'])
        self.assertTrue(state['h']['ok'])

    async def test_background_color_blank_canvas_and_broken_images_are_not_covers(self):
        await self.load(form(vertical=False, horizontal=False))
        await self.page.locator('#v').evaluate('''el => {
            el.style.backgroundColor = 'red';
            el.insertAdjacentHTML('afterbegin','<canvas width="90" height="120"></canvas>');
        }''')
        await self.page.locator('#v').evaluate('''(el,png) => {
            el.insertAdjacentHTML('afterbegin', `<img src="${png}" style="width:48px;height:48px">`);
        }''', PNG)
        await self.page.locator('#h').evaluate('''el => {
            el.insertAdjacentHTML('afterbegin','<img src="data:image/png;base64,broken">');
        }''')
        state = await collect_cover_state(self.page)
        self.assertFalse(state['v']['ok'])
        self.assertFalse(state['h']['ok'])
        await self.page.locator('canvas').evaluate("el => {let c=el.getContext('2d'); c.fillStyle='blue'; c.fillRect(0,0,90,120)}")
        self.assertTrue((await collect_cover_state(self.page))['v']['ok'])

    async def test_explicit_missing_warning_blocks_even_with_preview(self):
        await self.load(form(tip='横/竖双封面缺失'))
        state = await collect_cover_state(self.page)
        self.assertFalse(state['v']['ok'])
        self.assertFalse(state['h']['ok'])

    async def test_delayed_preview_is_retried_without_llm(self):
        await self.load(form(vertical=False))
        collect = publisher._collect_form_facts
        scheduled = False

        async def collect_then_schedule(*args, **kwargs):
            nonlocal scheduled
            facts = await collect(*args, **kwargs)
            if not scheduled:
                scheduled = True
                await self.page.evaluate('''png => setTimeout(() => {
                    document.querySelector('#v').insertAdjacentHTML('afterbegin',`<img src="${png}">`);
                }, 250)''', PNG)
            return facts

        with patch('app.llm_judge.judge_publish_form', side_effect=AssertionError('must not call LLM')) as judge, \
                patch.object(publisher, '_collect_form_facts', side_effect=collect_then_schedule):
            result = await publisher._verify_covers(self.page, expect_v=True, expect_h=True, timeout_ms=6000, poll_ms=100)
            judge.assert_not_called()
        self.assertTrue(result['ok'], result)
        self.assertGreaterEqual(result['attemptCount'], 3)
        diagnostic = json.loads(Path(result['diagnosticPath']).read_text(encoding='utf-8'))
        self.assertFalse(diagnostic['attempts'][0]['facts']['cover_v_ok'])
        self.assertNotIn('data:image', json.dumps(diagnostic))

    async def test_transient_preview_is_not_stable(self):
        await self.load(form())
        await self.page.evaluate("setTimeout(() => document.querySelector('#v img').remove(), 50)")
        result = await publisher._verify_covers(self.page, expect_v=True, expect_h=True, timeout_ms=400, poll_ms=150)
        self.assertFalse(result['ok'])
        self.assertIn('竖封面', result['reason'])

    async def test_visible_editor_after_hidden_duplicate_blocks(self):
        await self.load(form() + '<div style="display:none">设置竖封面</div><div>设置竖封面</div>')
        result = await publisher._verify_covers(self.page, expect_v=True, expect_h=True, timeout_ms=100, poll_ms=50)
        self.assertFalse(result['ok'])
        self.assertTrue(result['facts']['cover_modal_open'])

    async def run_pipeline(self, *, upload_ok=True):
        video = Path(self.temp.name) / 'test.mp4'
        cover = Path(self.temp.name) / 'cover.png'
        video.write_bytes(b'offline fixture')
        cover.write_bytes(b'offline fixture')
        context = SimpleNamespace(pages=[self.page], close=AsyncMock())
        manager = AsyncMock()
        manager.__aenter__.return_value = SimpleNamespace(
            chromium=SimpleNamespace(launch_persistent_context=AsyncMock(return_value=context)))
        with ExitStack() as stack:
            stack.enter_context(patch.object(publisher, 'async_playwright', return_value=manager))
            stack.enter_context(patch.object(self.page, 'goto', new=AsyncMock()))
            for name, value in {
                '_is_logged_in': True, '_upload_file': None, '_wait_upload_ready': None,
                '_dismiss_guides': None, '_save_debug_shot': 'offline-shot.png',
                '_fill_title': {'title': True, 'topics': True}, '_set_covers': upload_ok,
                '_close_cover_modal_if_open': None, '_prepare_before_publish': None,
            }.items():
                stack.enter_context(patch.object(publisher, name, new=AsyncMock(return_value=value)))
            click = stack.enter_context(patch.object(publisher, '_click_publish_and_confirm', new=AsyncMock(
                return_value={'ok': True, 'message': 'offline confirmation'})))
            stack.enter_context(patch.object(publisher, '_remember_login'))
            result = await publisher.publish_video(str(video), cover_path_v=str(cover), cover_path_h=str(cover), location='')
            return result, click.await_count

    async def test_pipeline_never_clicks_publish_for_missing_cover(self):
        await self.load(form(vertical=False))
        result, clicks = await self.run_pipeline()
        self.assertFalse(result['ok'])
        self.assertEqual(clicks, 0)
        self.assertEqual(result['stage'], 'prepublish_check')
        self.assertTrue(Path(result['coverCheck']['diagnosticPath']).is_file())

    async def test_pipeline_requires_upload_confirmation_even_if_previews_exist(self):
        await self.load(form())
        result, clicks = await self.run_pipeline(upload_ok=False)
        self.assertFalse(result['ok'])
        self.assertEqual(clicks, 0)
        self.assertIn('选图或保存未完成', result['message'])

    async def test_pipeline_allows_confirmed_stable_covers(self):
        await self.load(form())
        result, clicks = await self.run_pipeline()
        self.assertTrue(result['ok'])
        self.assertEqual(clicks, 1)


class BrowserQueueTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.gate = BrowserGate()
        self.patcher = patch.object(publisher, '_browser_gate', self.gate)
        self.patcher.start()

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_fifo_publish_has_priority_over_keepalive(self):
        self.assertTrue(self.gate.acquire('keepalive'))
        first = self.gate.enqueue_publish()
        second = self.gate.enqueue_publish()
        self.assertFalse(self.gate.acquire_publish(first))
        self.gate.release()
        self.assertFalse(self.gate.acquire('keepalive'))
        self.assertFalse(self.gate.acquire_publish(second))
        self.assertTrue(self.gate.acquire_publish(first))
        self.gate.release()
        self.assertFalse(self.gate.acquire('keepalive'))
        self.assertTrue(self.gate.acquire_publish(second))
        self.gate.release()
        self.assertTrue(self.gate.acquire('keepalive'))

    async def test_keepalive_over_five_seconds_does_not_fail_publishing(self):
        self.gate.acquire('keepalive')
        messages = []
        task = asyncio.create_task(publisher._wait_for_publish_browser(messages.append, timeout_sec=8))
        await asyncio.sleep(5.2)
        self.assertFalse(task.done())
        self.gate.release()
        self.assertTrue(await task)
        self.assertEqual(self.gate.status()['holder'], 'publish')
        self.assertTrue(any('已排队' in message for message in messages))
        self.gate.release()

    async def test_cancelled_and_timed_out_waiters_do_not_leak_queue_or_lock(self):
        self.gate.acquire('keepalive')
        task = asyncio.create_task(publisher._wait_for_publish_browser(lambda _: None, timeout_sec=10))
        await asyncio.sleep(0.02)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(self.gate.status()['waitingPublish'], 0)
        self.assertFalse(await publisher._wait_for_publish_browser(lambda _: None, timeout_sec=0.02))
        self.assertEqual(self.gate.status()['waitingPublish'], 0)
        self.gate.release()
        self.assertTrue(self.gate.acquire('keepalive'))
        self.gate.release()


class JobDeduplicationTests(unittest.TestCase):
    def test_duplicate_episode_clicks_share_only_the_active_job(self):
        old_data = jobs.settings.data_dir
        with tempfile.TemporaryDirectory() as temp:
            jobs.settings.data_dir = temp
            try:
                first, created = jobs.get_or_create_publish_job({'ep': 36, 'status': 'RUNNING'})
                self.assertTrue(created)
                same, created = jobs.get_or_create_publish_job({'ep': 36, 'status': 'RUNNING'})
                self.assertFalse(created)
                self.assertEqual(first['id'], same['id'])
                other, created = jobs.get_or_create_publish_job({'ep': 37, 'status': 'RUNNING'})
                self.assertTrue(created)
                self.assertNotEqual(first['id'], other['id'])
                jobs.update_job(first['id'], status='FAILED')
                retried, created = jobs.get_or_create_publish_job({'ep': 36, 'status': 'RUNNING'})
                self.assertTrue(created)
                self.assertNotEqual(first['id'], retried['id'])
            finally:
                jobs.settings.data_dir = old_data


if __name__ == '__main__':
    unittest.main()
