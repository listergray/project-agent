"""Inspect actual cover previews; never count an unrelated image as a cover."""
from __future__ import annotations

from playwright.async_api import Page


# Run once per poll so horizontal/vertical evidence comes from the same DOM state.
# No image URLs or page HTML are returned: diagnostics contain only geometry,
# element classes and a source fingerprint.
_COVER_STATE_JS = r"""() => {
    const visible = el => {
        if (!el || !el.isConnected) return false;
        if (el.checkVisibility && !el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true})) return false;
        const s = getComputedStyle(el), r = el.getBoundingClientRect();
        return s.visibility !== 'hidden' && s.display !== 'none' &&
            Number(s.opacity) !== 0 && r.width > 0 && r.height > 0;
    };
    const text = el => (el.innerText || '').replace(/\s+/g, '');
    const patterns = {v: /^竖封面(?:[（(]?3[:：/]4[）)]?)?$/,
                      h: /^横封面(?:[（(]?4[:：/]3[）)]?)?$/};
    const all = Array.from(document.querySelectorAll('body *'));
    const imageCache = window[Symbol.for('douyin-auto.cover-images')] ||= new Map();
    const labels = kind => all.filter(el => visible(el) && patterns[kind].test(text(el)) &&
        !Array.from(el.children).some(c => visible(c) && patterns[kind].test(text(c))));
    const slots = {v: labels('v'), h: labels('h')};
    const fingerprint = value => {
        let h = 2166136261;
        for (let i = 0; i < value.length; i++) h = Math.imul(h ^ value.charCodeAt(i), 16777619);
        return (h >>> 0).toString(16);
    };
    const inspect = el => {
        if (!visible(el)) return null;
        const r = el.getBoundingClientRect();
        if (r.width < 40 || r.height < 40) return null;
        let type = '', source = '';
        if (el.tagName === 'IMG') {
            source = el.currentSrc || el.src || '';
            if (!el.complete || el.naturalWidth < 40 || el.naturalHeight < 40) return null;
            type = 'img';
        } else if (el.tagName === 'CANVAS') {
            // A blank crop/placeholder canvas does not prove an image was set.
            try {
                const ctx = el.getContext('2d');
                if (!ctx || !el.width || !el.height) return null;
                const pixels = ctx.getImageData(0, 0, el.width, el.height).data;
                if (!pixels.some((v, i) => i % 4 === 3 && v > 0)) return null;
                const step = Math.max(4, Math.floor(pixels.length / 128 / 4) * 4);
                const sample = [];
                for (let i = 0; i < pixels.length; i += step) sample.push(...pixels.slice(i, i + 4));
                source = `${el.width}x${el.height}:${sample.join(',')}`;
            } catch (_) { return null; }
            type = 'canvas';
        } else {
            source = getComputedStyle(el).backgroundImage || '';
            if (!/url\(/i.test(source)) return null;
            type = 'background';
        }
        if (!source || /data:image\/svg|\.svg(?:[?#"')]|$)/i.test(source)) return null;
        if (type === 'background') {
            const match = /url\(["']?(.*?)["']?\)/i.exec(source);
            if (!match) return null;
            const url = match[1];
            if (!imageCache.has(url)) {
                const image = new Image(); image.src = url; imageCache.set(url, image);
            }
            const image = imageCache.get(url);
            if (!image.complete || image.naturalWidth < 40 || image.naturalHeight < 40) return null;
        }
        return {type, tag: el.tagName, class: String(el.className || '').slice(0, 120),
                width: Math.round(r.width), height: Math.round(r.height),
                fingerprint: fingerprint(source)};
    };
    const media = root => [root, ...root.querySelectorAll('*')]
        .map(el => ({el, info: inspect(el)})).filter(row => row.info);
    const find = kind => {
        const other = kind === 'v' ? 'h' : 'v';
        const ratioMatches = info => kind === 'v'
            ? info.width / info.height < 0.95 : info.width / info.height > 1.05;
        for (const label of slots[kind]) {
            let root = label;
            for (let level = 0; root && root !== document.body && level < 7; level++, root = root.parentElement) {
                if (slots[other].some(el => root.contains(el))) {
                    // Some layouts put both captions in one row. Only accept a
                    // preview directly above this caption, with the right ratio.
                    const lr = label.getBoundingClientRect(), rr = root.getBoundingClientRect();
                    if (rr.width > 1000 || rr.height > 650) break;
                    const rows = media(root).filter(({el}) => {
                        const mr = el.getBoundingClientRect(), ratio = mr.width / mr.height;
                        return Boolean(el.compareDocumentPosition(label) & Node.DOCUMENT_POSITION_FOLLOWING) &&
                            mr.bottom <= lr.top + 10 && lr.top - mr.bottom <= 80 &&
                            lr.left >= mr.left - 10 && lr.left < mr.right &&
                            (kind === 'v' ? ratio < 0.95 : ratio > 1.05);
                    });
                    if (rows.length === 1) return {ok: true, preview: rows[0].info};
                    if (rows.length > 1) break;
                    continue;
                }
                const rows = media(root).filter(row => ratioMatches(row.info));
                if (rows.length) return {ok: true, preview: rows[0].info};
            }
        }
        return {ok: false, reason: slots[kind].length ? '预览图片尚未就绪' : '未找到可见封面区域'};
    };
    const state = {v: find('v'), h: find('h'), missing: []};
    const leafText = all.filter(el => visible(el) && !Array.from(el.children).some(visible))
        .map(text).join('\n');
    if (/横封面(?:缺失|未设置)|缺少横封面|横[\/／]竖双封面缺失/.test(leafText)) state.missing.push('横');
    if (/竖封面(?:缺失|未设置)|缺少竖封面|横[\/／]竖双封面缺失/.test(leafText)) state.missing.push('竖');
    if (state.missing.includes('横')) state.h = {...state.h, ok: false, reason: '页面提示横封面缺失'};
    if (state.missing.includes('竖')) state.v = {...state.v, ok: false, reason: '页面提示竖封面缺失'};
    return state;
}"""


async def collect_cover_state(page: Page) -> dict:
    return await page.evaluate(_COVER_STATE_JS)
