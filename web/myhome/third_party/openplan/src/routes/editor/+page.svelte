<script lang="ts">
  import { onMount } from 'svelte';
  import { currentProject, viewMode, selectedElementId, selectedRoomId, createDefaultProject, loadProject, selectedTool, placingFurnitureId, elevationWallId, elevationPickMode } from '$lib/stores/project';
  import { localStore } from '$lib/services/datastore';
  import { createProjectFromRoomPlan, isRoomPlanJson } from '$lib/utils/roomplanImport';
  import TopBar from '$lib/components/toolbar/TopBar.svelte';
  import BuildPanel from '$lib/components/sidebar/BuildPanel.svelte';
  import PropertiesPanel from '$lib/components/sidebar/PropertiesPanel.svelte';
  import LayersPanel from '$lib/components/sidebar/LayersPanel.svelte';

  let showLayers = $state(false);
  import FloorPlanCanvas from '$lib/components/editor/FloorPlanCanvas.svelte';
  import AlignmentToolbar from '$lib/components/editor/AlignmentToolbar.svelte';
  import UndoHistoryPanel from '$lib/components/editor/UndoHistoryPanel.svelte';
  import CommandPalette from '$lib/components/editor/CommandPalette.svelte';
  import ElevationView from '$lib/components/editor/ElevationView.svelte';
  import PrintLayout from '$lib/components/editor/PrintLayout.svelte';
  import OnboardingTooltip from '$lib/components/OnboardingTooltip.svelte';
  import { triggerTip } from '$lib/stores/onboarding.svelte';

  let commandPaletteOpen = $state(false);
  let printOpen = $state(false);

  // Lazy-load ThreeViewer to avoid loading Three.js (~1.4MB) until 3D mode is activated
  let ThreeViewer: any = $state(null);
  $effect(() => {
    if (mode === '3d' && !ThreeViewer) {
      import('$lib/components/viewer3d/ThreeViewer.svelte').then(m => { ThreeViewer = m.default; });
    }
  });

  let mode = $state<'2d' | '3d'>('2d');
  let ready = $state(false);
  let showHelp = $state(false);
  let showUndoHistory = $state(false);

  // Mobile (< md): BuildPanel becomes an off-canvas drawer toggled by the Tools FAB.
  let buildPanelOpen = $state(false);
  // Close the drawer once the user has picked a tool / item so the canvas is usable
  selectedTool.subscribe(() => { if (buildPanelOpen) buildPanelOpen = false; });
  placingFurnitureId.subscribe((id) => { if (id && buildPanelOpen) buildPanelOpen = false; });

  // iOS capture handoff (?import=CODE → fetch RoomPlan JSON from Firebase Storage inbox)
  let importingCapture = $state(false);
  let importError = $state<string | null>(null);

  /** Fetch a RoomPlan capture uploaded by the iOS app and open it as a new project. Returns true on success. */
  async function importCaptureFromCode(code: string): Promise<boolean> {
    importingCapture = true;
    try {
      const url = `https://firebasestorage.googleapis.com/v0/b/openplan3d.firebasestorage.app/o/inbox%2F${code}.json?alt=media`;
      let res: Response;
      try {
        res = await fetch(url);
      } catch {
        throw new Error('Network error while downloading the capture. Check your connection and try again.');
      }
      if (res.status === 404) {
        throw new Error(`Capture code ${code} was not found. It may have expired — share it again from the iOS app.`);
      }
      if (!res.ok) {
        throw new Error(`Failed to download the capture (HTTP ${res.status}).`);
      }
      let data: any;
      try {
        data = await res.json();
      } catch {
        throw new Error('The downloaded capture is not valid JSON.');
      }
      if (!isRoomPlanJson(data)) {
        throw new Error('The downloaded file is not a valid RoomPlan export.');
      }
      // The iOS app can send explicit import choices (user-facing toggles);
      // openplanPrepared is the older marker for exact hand-drawn/edited
      // geometry. Raw scans without either keep the dialog defaults.
      const sent = data?.openplanImportOptions;
      const options = sent
        ? {
            straighten: !!sent.straighten,
            orthogonal: !!sent.orthogonal,
            mergeDistance: sent.straighten || sent.orthogonal ? 15 : 0,
          }
        : data?.openplanPrepared
          ? { straighten: false, orthogonal: false, mergeDistance: 0 }
          : undefined;
      const project = createProjectFromRoomPlan(data, `Room Capture ${code}`, options);
      loadProject(project);
      await localStore.save(project);
      // Remove ?import=CODE so a refresh doesn't re-import
      history.replaceState(null, '', `/editor?id=${project.id}`);
      return true;
    } catch (e: any) {
      importError = e?.message ?? 'Failed to import capture.';
      return false;
    } finally {
      importingCapture = false;
    }
  }

  viewMode.subscribe((m) => {
    mode = m;
    if (m === '3d') {
      // Clear selection when entering 3D — start in view-only mode
      selectedElementId.set(null);
      selectedRoomId.set(null);
      elevationPickMode.set(false);
      // Onboarding tip for first 3D view
      triggerTip('first-3d', 200, 80);
    }
  });

  onMount(() => {
    let saveTimeout: ReturnType<typeof setTimeout> | undefined
    let unsubProject: (() => void) | undefined
    let onMessage: ((event: MessageEvent) => void) | undefined
    let fallbackTimer: ReturnType<typeof setTimeout> | undefined
    let cancelled = false

    void (async () => {
      const url = new URL(window.location.href)
      const embed = url.searchParams.get('embed') === '1'

      if (embed) {
        const { OPENPLAN_MSG, normalizeProject, postToParent, serializeProject } = await import(
          '$lib/services/embedBridge'
        )
        if (cancelled) return
        let loaded = false
        unsubProject = currentProject.subscribe((p) => {
          if (!p) return
          clearTimeout(saveTimeout)
          saveTimeout = setTimeout(() => {
            postToParent(OPENPLAN_MSG.save, { project: serializeProject(p) })
            void localStore.save(p)
          }, 600)
        })

        onMessage = (event: MessageEvent) => {
          if (event.data?.type !== OPENPLAN_MSG.load) return
          loaded = true
          const project = normalizeProject(event.data.project)
          if (project) {
            currentProject.set(project)
            void localStore.save(project)
          } else {
            const p = createDefaultProject('我的小屋')
            currentProject.set(p)
            void localStore.save(p)
          }
          ready = true
        }
        window.addEventListener('message', onMessage)
        postToParent(OPENPLAN_MSG.ready)
        const readyPing = setInterval(() => {
          if (cancelled || loaded) {
            clearInterval(readyPing)
            return
          }
          postToParent(OPENPLAN_MSG.ready)
        }, 400)
        fallbackTimer = setTimeout(() => {
          if (!ready) {
            const p = createDefaultProject('我的小屋')
            currentProject.set(p)
            ready = true
          }
        }, 1200)
        return
      }

      unsubProject = currentProject.subscribe((p) => {
        if (!p) return
        clearTimeout(saveTimeout)
        saveTimeout = setTimeout(() => localStore.save(p), 500)
      })

      const rawCode = url.searchParams.get('import')
      if (rawCode) {
        const code = rawCode.toUpperCase()
        if (/^[A-Z2-9]{4,32}$/.test(code)) {
          if (await importCaptureFromCode(code)) {
            ready = true
            return
          }
        } else {
          importError = 'Invalid import code in URL.'
        }
      }

      const id = url.searchParams.get('id')
      if (id) {
        const project = await localStore.load(id)
        if (project) {
          currentProject.set(project)
        } else {
          const p = createDefaultProject()
          currentProject.set(p)
          await localStore.save(p)
          history.replaceState(null, '', `/openplan/editor?id=${p.id}`)
        }
      } else {
        const p = createDefaultProject()
        currentProject.set(p)
        await localStore.save(p)
        history.replaceState(null, '', `/openplan/editor?id=${p.id}`)
      }
      ready = true
    })()

    return () => {
      cancelled = true
      unsubProject?.()
      clearTimeout(saveTimeout)
      clearTimeout(fallbackTimer)
      if (onMessage) window.removeEventListener('message', onMessage)
    }
  });
</script>

<svelte:window on:keydown={(e) => { if (e.key === 'p' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); printOpen = true; } if ((e.key === 'k' && (e.ctrlKey || e.metaKey)) || (e.key === '/' && !e.ctrlKey && !e.metaKey && (e.target as HTMLElement)?.tagName !== 'INPUT' && (e.target as HTMLElement)?.tagName !== 'TEXTAREA')) { e.preventDefault(); commandPaletteOpen = !commandPaletteOpen; } if (e.key === '?' && !e.ctrlKey && !e.metaKey) { showHelp = !showHelp; e.preventDefault(); } if (e.key === 'Escape' && showHelp) { showHelp = false; } if (e.key === 'l' && !e.ctrlKey && !e.metaKey && !e.altKey && (e.target as HTMLElement)?.tagName !== 'INPUT') { showLayers = !showLayers; } }} />

{#if ready}
  <div class="h-screen flex flex-col overflow-hidden">
    <TopBar />
    <div class="flex flex-1 overflow-hidden">
      {#if mode === '2d'}
        <!-- Build panel: inline sidebar on md+, off-canvas drawer on phones -->
        {#if buildPanelOpen}
          <div
            class="md:hidden fixed inset-x-0 top-12 bottom-0 bg-black/40 z-40"
            onclick={() => buildPanelOpen = false}
            aria-hidden="true"
          ></div>
        {/if}
        <div class="h-full max-md:fixed max-md:left-0 max-md:top-12 max-md:bottom-0 max-md:h-auto max-md:z-50 max-md:shadow-2xl max-md:transition-transform max-md:duration-200 {buildPanelOpen ? '' : 'max-md:-translate-x-full'}">
          <BuildPanel />
        </div>
      {/if}
      <div class="flex-1 min-w-0 relative">
        {#if mode === '2d'}
          <FloorPlanCanvas />
          <AlignmentToolbar />
          {#if $elevationWallId}
            <!-- Integrated elevation view replaces the plan canvas area (sidebars stay) -->
            <ElevationView />
          {/if}
        {:else}
          {#if ThreeViewer}
            <ThreeViewer />
          {:else}
            <div class="flex items-center justify-center h-full text-slate-400">加载 3D 视图…</div>
          {/if}
        {/if}
      </div>
      {#if showLayers && mode === '2d'}
        <LayersPanel />
      {/if}
      <PropertiesPanel is3D={mode === '3d'} />
    </div>
  </div>

  <!-- Tools drawer FAB (mobile only) -->
  {#if mode === '2d'}
    <button
      class="md:hidden fixed bottom-4 left-4 w-12 h-12 rounded-full bg-blue-600 text-white shadow-lg active:bg-blue-700 transition-colors z-40 flex items-center justify-center"
      onclick={() => buildPanelOpen = !buildPanelOpen}
      title="工具"
      aria-label="切换工具面板"
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
    </button>
  {/if}

  <!-- Layers toggle button -->
  {#if mode === '2d'}
    <button
      class="max-md:hidden fixed bottom-4 left-14 w-8 h-8 rounded-full shadow-lg hover:bg-slate-600 transition-colors z-50 text-sm"
      class:bg-blue-600={showLayers}
      class:text-white={showLayers}
      class:bg-slate-700={!showLayers}
      class:text-gray-300={!showLayers}
      onclick={() => showLayers = !showLayers}
      title="图层面板 (L)"
      aria-label="切换图层面板"
    >🗂</button>
  {/if}

  <!-- Undo History toggle button -->
  <button
    class="max-md:hidden fixed bottom-4 left-24 w-8 h-8 rounded-full shadow-lg hover:bg-slate-600 transition-colors z-50 text-sm"
    class:bg-blue-600={showUndoHistory}
    class:text-white={showUndoHistory}
    class:bg-slate-700={!showUndoHistory}
    class:text-gray-300={!showUndoHistory}
    onclick={() => showUndoHistory = !showUndoHistory}
    title="撤销历史"
    aria-label="切换撤销历史"
  >⟲</button>

  <UndoHistoryPanel bind:visible={showUndoHistory} />

  <!-- Help button (desktop only — keyboard shortcuts are meaningless on touch) -->
  <button
    class="max-md:hidden fixed bottom-4 left-4 w-8 h-8 rounded-full bg-slate-700 text-white text-sm font-bold shadow-lg hover:bg-slate-600 transition-colors z-50"
    onclick={() => showHelp = !showHelp}
    title="快捷键 (?)"
    aria-label="快捷键"
  >?</button>

  <!-- Shortcuts overlay -->
  {#if showHelp}
    {@const shortcutsCopied = { value: false }}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onclick={() => showHelp = false} onkeydown={(e) => { if (e.key === 'Escape') showHelp = false; }} role="dialog" tabindex="-1" aria-label="快捷键">
      <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
      <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[85vh] flex flex-col" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} role="document">
        <div class="flex items-center justify-between px-6 pt-5 pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707"/></svg>
            <h2 class="text-lg font-bold text-slate-800">快捷键</h2>
          </div>
          <div class="flex items-center gap-2">
            <button
              class="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-800 transition-colors flex items-center gap-1.5"
              onclick={() => {
                const text = [
                  '快捷键 — OpenPlan3D',
                  '',
                  '── 工具 ──',
                  'V          选择',
                  'W          画墙',
                  'D          门',
                  'H          平移',
                  'M          测量',
                  'N          标注',
                  'T          文字',
                  'S          对齐开关',
                  '',
                  '── 编辑 ──',
                  'Ctrl+Z     撤销',
                  'Ctrl+Y     重做',
                  'Ctrl+C     复制',
                  'Ctrl+V     粘贴',
                  'Ctrl+A     全选',
                  'Ctrl+D     取消选择',
                  'Ctrl+S     保存',
                  'Esc        取消 / 取消选择',
                  '',
                  '── 元素 ──',
                  'R          旋转',
                  'Del/Back   删除所选',
                  'Ctrl+L     锁定/解锁',
                  'Ctrl+G     编组',
                  'Ctrl+⇧+G   取消编组',
                  '',
                  '── 视图 ──',
                  'Tab        切换 2D/3D',
                  'F          适应画布',
                  'G          网格开关',
                  'L          图层开关',
                  '?          显示快捷键',
                  '',
                  '── 画布 ──',
                  '滚轮       缩放',
                  '+/-        缩放',
                  '空格+拖拽  平移',
                  '',
                  '── 墙体 ──',
                  '双击       结束连续画墙',
                  'C          闭合墙环',
                ].join('\n');
                navigator.clipboard.writeText(text);
              }}
              aria-label="复制全部快捷键"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
              全部复制
            </button>
            <button class="text-gray-400 hover:text-gray-600 text-xl leading-none" onclick={() => showHelp = false} aria-label="关闭">✕</button>
          </div>
        </div>

        <div class="overflow-y-auto px-6 py-4">
          <div class="grid grid-cols-2 gap-x-8 gap-y-0 text-sm">
            <div>
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-bold uppercase tracking-wider text-indigo-500">工具</span>
                <div class="flex-1 h-px bg-indigo-100"></div>
              </div>
              <div class="space-y-1.5 mb-5">
                <div class="flex justify-between"><span class="text-gray-600">选择</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">V</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">画墙</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">W</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">门</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">D</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">平移</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">H</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">测量</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">M</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">标注</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">N</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">文字</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">T</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">对齐开关</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">S</kbd></div>
              </div>

              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-bold uppercase tracking-wider text-amber-500">编辑</span>
                <div class="flex-1 h-px bg-amber-100"></div>
              </div>
              <div class="space-y-1.5 mb-5">
                <div class="flex justify-between"><span class="text-gray-600">撤销</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+Z</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">重做</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+Y</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">复制</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+C</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">粘贴</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+V</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">全选</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+A</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">取消选择</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+D</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">保存</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+S</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">取消 / 取消选择</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Esc</kbd></div>
              </div>
            </div>

            <div>
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-bold uppercase tracking-wider text-emerald-500">元素</span>
                <div class="flex-1 h-px bg-emerald-100"></div>
              </div>
              <div class="space-y-1.5 mb-5">
                <div class="flex justify-between"><span class="text-gray-600">旋转</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">R</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">删除所选</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Del</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">锁定 / 解锁</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+L</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">编组</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+G</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">取消编组</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Ctrl+⇧+G</kbd></div>
              </div>

              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-bold uppercase tracking-wider text-blue-500">视图</span>
                <div class="flex-1 h-px bg-blue-100"></div>
              </div>
              <div class="space-y-1.5 mb-5">
                <div class="flex justify-between"><span class="text-gray-600">切换 2D / 3D</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">Tab</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">适应画布</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">F</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">网格开关</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">G</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">图层开关</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">L</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">显示快捷键</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">?</kbd></div>
              </div>

              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-bold uppercase tracking-wider text-purple-500">画布</span>
                <div class="flex-1 h-px bg-purple-100"></div>
              </div>
              <div class="space-y-1.5 mb-5">
                <div class="flex justify-between"><span class="text-gray-600">缩放</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">滚轮</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">缩放</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">+ / −</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">平移</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">空格+拖</kbd></div>
              </div>

              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-bold uppercase tracking-wider text-rose-500">墙体</span>
                <div class="flex-1 h-px bg-rose-100"></div>
              </div>
              <div class="space-y-1.5">
                <div class="flex justify-between"><span class="text-gray-600">结束连续画墙</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">双击</kbd></div>
                <div class="flex justify-between"><span class="text-gray-600">闭合墙环</span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono text-slate-700 border border-gray-200">C</kbd></div>
              </div>
            </div>
          </div>
        </div>

        <div class="px-6 py-3 border-t border-gray-100 text-center">
          <p class="text-xs text-gray-400">按 <kbd class="px-1 py-0.5 bg-gray-100 rounded text-xs font-mono border border-gray-200">?</kbd> 或 <kbd class="px-1 py-0.5 bg-gray-100 rounded text-xs font-mono border border-gray-200">Esc</kbd> 关闭</p>
        </div>
      </div>
    </div>
  {/if}

  <CommandPalette bind:open={commandPaletteOpen} />
  <PrintLayout bind:open={printOpen} />
  <OnboardingTooltip />
{:else}
  <div class="h-screen flex flex-col items-center justify-center gap-3">
    {#if importingCapture}
      <div class="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" aria-hidden="true"></div>
      <p class="text-gray-400">正在从 iOS 导入扫描…</p>
    {:else}
      <p class="text-gray-400">加载中…</p>
    {/if}
  </div>
{/if}

<!-- iOS capture import error toast -->
{#if importError}
  <div class="fixed top-16 left-1/2 -translate-x-1/2 z-[100] w-[calc(100vw-2rem)] max-w-md bg-red-50 border border-red-200 text-red-700 rounded-lg shadow-lg px-4 py-3 flex items-start gap-3" role="alert">
    <svg class="w-5 h-5 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
    <div class="flex-1 text-sm">
      <p class="font-semibold">Capture import failed</p>
      <p>{importError}</p>
    </div>
    <button class="text-red-400 hover:text-red-600 text-lg leading-none" onclick={() => importError = null} aria-label="Dismiss error">✕</button>
  </div>
{/if}
