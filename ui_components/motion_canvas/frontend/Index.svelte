<script lang="ts">
	import type { Gradio } from "@gradio/utils";

	type FileData = { path: string; url?: string | null } | null;
	type Arrow = [number, number, number, number];
	type CanvasValue = {
		background?: FileData;
		arrows: Arrow[];
		camera?: string;
		camera_amount?: number;
		enabled?: boolean;
		reason?: string;
	};

	export let gradio: Gradio<{ change: never; input: never }>;
	export let elem_id = "";
	export let elem_classes: string[] = [];
	export let visible = true;
	export let value: CanvasValue | null = null;
	export let label = "";
	export let show_label = true;
	export let interactive = true;
	export let loading_status: any = undefined;
	export let scale: number | null = null;
	export let min_width: number | undefined = undefined;
	export let root = "";
	export let container = true;

	const MAX_H = 360;
	const MIN_LEN = 0.02;

	let w = 0;
	let h = 0;
	let stage: HTMLDivElement;
	let natural: { w: number; h: number } | null = null;
	let draft: Arrow | null = null;
	let selected: number | null = null;

	$: arrows = value?.arrows ?? [];
	$: enabled = value?.enabled !== false;
	$: editable = interactive !== false && enabled;
	$: bg = value?.background ?? null;
	$: src = bg ? bg.url || `${root}/gradio_api/file=${bg.path}` : null;
	$: if (!src) natural = null;
	$: ar = natural ? natural.w / natural.h : 16 / 9;
	$: camera = value?.camera ?? "None";
	$: amount = Math.max(0, Math.min(1, value?.camera_amount ?? 0));
	$: show_camera = camera && camera !== "None" && amount > 0;
	$: cam_vectors = show_camera ? camera_grid(camera, amount, w, h) : [];
	$: if (selected !== null && selected >= arrows.length) selected = null;

	function camera_grid(name: string, amt: number, cw: number, ch: number) {
		if (!cw || !ch) return [];
		const n = name.toLowerCase();
		const cols = 7;
		const rows = Math.max(3, Math.round((cols * ch) / cw));
		const cell = Math.min(cw / cols, ch / rows);
		const len = cell * (0.25 + 0.55 * amt);
		const out: number[][] = [];
		for (let r = 0; r < rows; r++) {
			for (let c = 0; c < cols; c++) {
				const x = ((c + 0.5) / cols) * cw;
				const y = ((r + 0.5) / rows) * ch;
				let dx = 0;
				let dy = 0;
				if (n.includes("zoom")) {
					const vx = x - cw / 2;
					const vy = y - ch / 2;
					const d = Math.hypot(vx, vy);
					if (d < cell * 0.6) continue;
					const k = (len * (0.4 + (0.6 * d) / Math.hypot(cw / 2, ch / 2))) / d;
					const sign = n.includes("out") ? -1 : 1;
					dx = sign * vx * k;
					dy = sign * vy * k;
				} else if (n.includes("left")) dx = -len;
				else if (n.includes("right")) dx = len;
				else if (n.includes("up")) dy = -len;
				else if (n.includes("down")) dy = len;
				else continue;
				out.push([x - dx / 2, y - dy / 2, x + dx / 2, y + dy / 2]);
			}
		}
		return out;
	}

	function head(x0: number, y0: number, x1: number, y1: number, size: number) {
		const a = Math.atan2(y1 - y0, x1 - x0);
		const p = (da: number) =>
			`${x1 - size * Math.cos(a + da)},${y1 - size * Math.sin(a + da)}`;
		return `${x1},${y1} ${p(0.45)} ${p(-0.45)}`;
	}

	function shaft_end(x0: number, y0: number, x1: number, y1: number, back: number) {
		const d = Math.hypot(x1 - x0, y1 - y0) || 1;
		const k = Math.max(0, d - back) / d;
		return [x0 + (x1 - x0) * k, y0 + (y1 - y0) * k];
	}

	function pos(e: PointerEvent): [number, number] {
		const r = stage.getBoundingClientRect();
		const clamp = (v: number) => Math.min(1, Math.max(0, v));
		return [clamp((e.clientX - r.left) / r.width), clamp((e.clientY - r.top) / r.height)];
	}

	function set_arrows(next: Arrow[]) {
		const base: CanvasValue = value ?? { background: null, arrows: [] };
		value = { ...base, arrows: next };
		gradio.dispatch("change");
		gradio.dispatch("input");
	}

	function on_down(e: PointerEvent) {
		if (!editable || e.button !== 0) return;
		stage.focus();
		stage.setPointerCapture(e.pointerId);
		const [x, y] = pos(e);
		draft = [x, y, x, y];
		e.preventDefault();
	}

	function on_move(e: PointerEvent) {
		if (!draft) return;
		const [x, y] = pos(e);
		draft = [draft[0], draft[1], x, y];
	}

	function on_up() {
		if (!draft) return;
		const d = draft;
		draft = null;
		if (Math.hypot(d[2] - d[0], d[3] - d[1]) < MIN_LEN) {
			selected = null;
			return;
		}
		const r = (v: number) => Math.round(v * 1000) / 1000;
		set_arrows([...arrows, d.map(r) as Arrow]);
		selected = null;
	}

	function pick(e: PointerEvent, i: number) {
		if (!editable) return;
		e.stopPropagation();
		e.preventDefault();
		stage.focus();
		selected = selected === i ? null : i;
	}

	function on_key(e: KeyboardEvent) {
		if (!editable) return;
		if ((e.key === "Delete" || e.key === "Backspace") && selected !== null) {
			e.preventDefault();
			const i = selected;
			selected = null;
			set_arrows(arrows.filter((_, j) => j !== i));
		} else if (e.key === "Escape") {
			selected = null;
		}
	}

	function undo() {
		selected = null;
		set_arrows(arrows.slice(0, -1));
	}

	function clear() {
		selected = null;
		set_arrows([]);
	}

	function on_img_load(e: Event) {
		const img = e.currentTarget as HTMLImageElement;
		if (img.naturalWidth && img.naturalHeight)
			natural = { w: img.naturalWidth, h: img.naturalHeight };
	}
</script>

<div
	id={elem_id || null}
	class="fps-motion {elem_classes.join(' ')}"
	class:hidden={!visible}
	class:boxed={container}
	style:flex-grow={scale}
	style:min-width={min_width ? `${min_width}px` : null}
>
	{#if show_label && label}<span class="block-label">{label}</span>{/if}

	<div
		class="stage"
		class:editable
		class:disabled={!enabled}
		class:empty={!src}
		style="aspect-ratio: {ar}; width: min(100%, {MAX_H * ar}px);"
		bind:this={stage}
		bind:clientWidth={w}
		bind:clientHeight={h}
		tabindex={editable ? 0 : -1}
		role="application"
		aria-label="Motion canvas. Drag to draw an arrow; select an arrow and press Delete to remove it."
		on:pointerdown={on_down}
		on:pointermove={on_move}
		on:pointerup={on_up}
		on:pointercancel={on_up}
		on:keydown={on_key}
	>
		{#if src}
			<img {src} alt="Start frame" draggable="false" on:load={on_img_load} />
		{:else}
			<div class="hint-empty"><span>Add a start frame to draw on it</span></div>
		{/if}

		<svg width={w} height={h} viewBox="0 0 {w || 1} {h || 1}">
			{#each cam_vectors as [x0, y0, x1, y1]}
				{@const [sx, sy] = shaft_end(x0, y0, x1, y1, 4)}
				<g class="cam">
					<line x1={x0} y1={y0} x2={sx} y2={sy} />
					<polygon points={head(x0, y0, x1, y1, 8)} />
				</g>
			{/each}

			{#each arrows as a, i}
				{@const x0 = a[0] * w}
				{@const y0 = a[1] * h}
				{@const x1 = a[2] * w}
				{@const y1 = a[3] * h}
				{@const sel = selected === i}
				{@const hs = sel ? 18 : 14}
				{@const [sx, sy] = shaft_end(x0, y0, x1, y1, hs * 0.7)}
				<g class="arrow" class:sel>
					<line class="outline" x1={x0} y1={y0} x2={sx} y2={sy} />
					<line class="fill" x1={x0} y1={y0} x2={sx} y2={sy} />
					<polygon points={head(x0, y0, x1, y1, hs)} />
					<circle cx={x0} cy={y0} r={sel ? 5.5 : 4.5} />
					<line
						class="hit"
						x1={x0}
						y1={y0}
						x2={x1}
						y2={y1}
						role="button"
						tabindex="-1"
						aria-label="Arrow {i + 1}"
						on:pointerdown={(e) => pick(e, i)}
					/>
				</g>
			{/each}

			{#if draft}
				{@const x0 = draft[0] * w}
				{@const y0 = draft[1] * h}
				{@const x1 = draft[2] * w}
				{@const y1 = draft[3] * h}
				{@const [sx, sy] = shaft_end(x0, y0, x1, y1, 10)}
				<g class="arrow draft">
					<line class="outline" x1={x0} y1={y0} x2={sx} y2={sy} />
					<line class="fill" x1={x0} y1={y0} x2={sx} y2={sy} />
					{#if Math.hypot(x1 - x0, y1 - y0) > 6}
						<polygon points={head(x0, y0, x1, y1, 14)} />
					{/if}
					<circle cx={x0} cy={y0} r="4.5" />
				</g>
			{/if}
		</svg>

		{#if show_camera}
			<span class="chip">Camera: {camera} &middot; {Math.round(amount * 100)}%</span>
		{/if}

		{#if !enabled}
			<div class="veil">
				{#if value?.reason}<span class="reason">{value.reason}</span>{/if}
			</div>
		{/if}
	</div>

	<div class="toolbar">
		<button type="button" disabled={!editable || arrows.length === 0} on:click={undo}>Undo</button>
		<button type="button" disabled={!editable || arrows.length === 0} on:click={clear}>Clear</button>
		<span class="hint">
			{#if selected !== null}
				Arrow selected: press Delete to remove it
			{:else}
				Drag on the frame to draw where things should move
			{/if}
		</span>
		{#if arrows.length}
			<span class="count">{arrows.length} {arrows.length === 1 ? "arrow" : "arrows"}</span>
		{/if}
	</div>
</div>

<style>
	.fps-motion {
		position: relative;
		font-family: inherit;
		color: var(--body-text-color);
		width: 100%;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.fps-motion.boxed {
		padding: var(--block-padding);
		border: 1px solid var(--border-color-primary);
		border-radius: var(--block-radius);
		background: var(--background-fill-primary);
	}
	.hidden {
		display: none;
	}
	.block-label {
		font-size: var(--block-label-text-size);
		font-weight: var(--block-label-text-weight, 400);
		color: var(--block-label-text-color, var(--body-text-color-subdued));
	}

	.stage {
		position: relative;
		margin: 0 auto;
		max-width: 100%;
		border-radius: var(--radius-md, 6px);
		overflow: hidden;
		background: #3a3d42;
		touch-action: none;
		user-select: none;
		-webkit-user-select: none;
		outline: none;
	}
	.stage.editable {
		cursor: crosshair;
	}
	.stage:focus-visible {
		box-shadow: 0 0 0 2px var(--color-accent);
	}
	.stage.empty {
		background: repeating-linear-gradient(
				45deg,
				rgba(255, 255, 255, 0.03) 0 10px,
				transparent 10px 20px
			),
			#55595f;
	}
	img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: contain;
		pointer-events: none;
	}
	.hint-empty {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		color: rgba(255, 255, 255, 0.75);
		font-size: var(--text-sm);
		pointer-events: none;
		text-align: center;
		padding: 0 16px;
	}
	.hint-empty span {
		padding: 4px 12px;
		border-radius: 999px;
		background: rgba(0, 0, 0, 0.45);
		color: #fff;
	}
	svg {
		position: absolute;
		inset: 0;
		overflow: visible;
	}

	.cam line {
		stroke: rgba(255, 255, 255, 0.42);
		stroke-width: 1.5;
		stroke-linecap: round;
	}
	.cam polygon {
		fill: rgba(255, 255, 255, 0.42);
	}
	.cam {
		filter: drop-shadow(0 0 1px rgba(0, 0, 0, 0.5));
		pointer-events: none;
	}

	.arrow line.outline {
		stroke: #1a1a1a;
		stroke-width: 5.5;
		stroke-linecap: round;
	}
	.arrow line.fill {
		stroke: #ffd400;
		stroke-width: 3.5;
		stroke-linecap: round;
	}
	.arrow polygon,
	.arrow circle {
		fill: #ffd400;
		stroke: #1a1a1a;
		stroke-width: 1.2;
		stroke-linejoin: round;
	}
	.arrow.sel line.outline {
		stroke-width: 8.5;
	}
	.arrow.sel line.fill {
		stroke-width: 6;
	}
	.arrow.sel {
		filter: drop-shadow(0 0 4px rgba(255, 212, 0, 0.75));
	}
	.arrow.draft {
		opacity: 0.85;
		pointer-events: none;
	}
	.arrow line.hit {
		stroke: transparent;
		stroke-width: 16;
		stroke-linecap: round;
		cursor: pointer;
		pointer-events: stroke;
		outline: none;
	}
	.stage:not(.editable) .arrow line.hit {
		pointer-events: none;
	}

	.chip {
		position: absolute;
		top: 8px;
		left: 8px;
		padding: 2px 8px;
		border-radius: 999px;
		background: rgba(0, 0, 0, 0.6);
		color: #fff;
		font-size: var(--text-xs);
		line-height: 18px;
		pointer-events: none;
		white-space: nowrap;
	}

	.stage.disabled > img,
	.stage.disabled > svg,
	.stage.disabled > .hint-empty {
		opacity: 0.6;
		filter: grayscale(0.7);
	}
	.veil {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.25);
		cursor: not-allowed;
	}
	.reason {
		max-width: 80%;
		padding: 6px 12px;
		border-radius: var(--radius-md, 6px);
		background: rgba(0, 0, 0, 0.7);
		color: #fff;
		font-size: var(--text-sm);
		text-align: center;
	}

	.toolbar {
		display: flex;
		align-items: center;
		gap: 6px;
		flex-wrap: wrap;
		min-height: 28px;
	}
	.toolbar button {
		font: inherit;
		font-size: var(--text-sm);
		padding: 3px 12px;
		border-radius: var(--button-small-radius, var(--radius-sm, 4px));
		border: 1px solid var(--button-secondary-border-color, var(--border-color-primary));
		background: var(--button-secondary-background-fill, var(--background-fill-secondary));
		color: var(--button-secondary-text-color, var(--body-text-color));
		cursor: pointer;
	}
	.toolbar button:hover:not(:disabled) {
		background: var(
			--button-secondary-background-fill-hover,
			var(--background-fill-secondary)
		);
		border-color: var(--color-accent);
	}
	.toolbar button:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.hint {
		margin-left: 6px;
		font-size: var(--text-xs);
		color: var(--body-text-color-subdued);
		flex: 1 1 auto;
		min-width: 0;
	}
	.count {
		font-size: var(--text-xs);
		color: var(--body-text-color-subdued);
		font-variant-numeric: tabular-nums;
	}
</style>
