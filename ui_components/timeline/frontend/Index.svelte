<script lang="ts">
	import type { Gradio, SelectData } from "@gradio/utils";

	type Section = { start: number; end: number; order?: number; state?: string };
	type Prompt = { start: number; end: number; text: string };
	type Frame = {
		kind: "start" | "key" | "end";
		t: number;
		snapped?: number | null;
		label?: string;
		index?: number;
		set?: boolean;
	};
	type Lane = {
		id?: string;
		label: string;
		text?: string;
		start: number;
		end: number;
		enabled?: boolean;
		reason?: string;
	};
	type TimelineValue = {
		duration: number;
		direction?: "forward" | "backward" | null;
		sections?: Section[];
		prompts?: Prompt[];
		blend?: number;
		frames?: Frame[];
		lanes?: Lane[];
		keyframes_enabled?: boolean;
		keyframes_reason?: string;
		selected_section?: number | null;
		selectable?: boolean;
	};

	export let gradio: Gradio<{ change: never; input: never; select: SelectData }>;
	export let elem_id = "";
	export let elem_classes: string[] = [];
	export let visible = true;
	export let value: TimelineValue | null = null;
	export let label = "";
	export let show_label = true;
	export let interactive = true;
	export let loading_status: any = undefined;
	export let scale: number | null = null;
	export let min_width: number | undefined = undefined;
	export let root = "";
	export let container = true;

	let track_width = 600;
	let frames_track: HTMLDivElement;
	let drag: { i: number; t: number; moved: boolean } | null = null;

	$: duration = value && value.duration > 0 ? value.duration : 0;
	$: sections = value?.sections ?? [];
	$: prompts = value?.prompts ?? [];
	$: frames = value?.frames ?? [];
	$: lanes = value?.lanes ?? [];
	$: blend = Math.max(0, value?.blend ?? 0);
	$: keys_enabled = value?.keyframes_enabled !== false;
	$: editable = interactive !== false && keys_enabled;
	$: caption =
		value?.direction === "backward"
			? "generated end → start"
			: value?.direction === "forward"
				? "generated start → end"
				: "";
	$: ticks = make_ticks(sections, duration, track_width);

	const pct = (t: number) => `${(Math.min(Math.max(t, 0), duration) / duration) * 100}%`;
	const span = (a: number, b: number) =>
		`left:${pct(a)};width:${((Math.min(b, duration) - Math.max(a, 0)) / duration) * 100}%`;
	const fmt = (t: number) => `${(Math.round(t * 10) / 10).toFixed(1)}`;
	const round1 = (t: number) => Math.round(t * 10) / 10;

	function make_ticks(secs: Section[], dur: number, width: number) {
		if (!dur) return [];
		const raw = new Set<number>([0, dur]);
		for (const s of secs) {
			raw.add(round1(s.start));
			raw.add(round1(s.end));
		}
		const all = [...raw].filter((t) => t >= 0 && t <= dur).sort((a, b) => a - b);
		const min_px = 34;
		const out: { t: number; anchor: string }[] = [];
		let last = -Infinity;
		for (const t of all) {
			const px = (t / dur) * width;
			const is_end = t === dur;
			if (is_end) {
				while (out.length > 1 && px - (out[out.length - 1].t / dur) * width < min_px) out.pop();
			} else if (px - last < min_px) continue;
			out.push({ t, anchor: t === 0 ? "left" : is_end ? "right" : "mid" });
			last = px;
		}
		return out;
	}

	function anchor(t: number) {
		const f = t / duration;
		return f < 0.03 ? "left" : f > 0.97 ? "right" : "mid";
	}

	function cell_state(s: Section, i: number) {
		if (value?.selected_section === i) return "selected";
		return s.state ?? "normal";
	}

	function commit_frame(i: number, t: number) {
		if (!value) return;
		const next = frames.map((f, j) => (j === i ? { ...f, t: round1(t) } : f));
		value = { ...value, frames: next };
		gradio.dispatch("change");
		gradio.dispatch("input");
	}

	function time_at(clientX: number) {
		const r = frames_track.getBoundingClientRect();
		const t = ((clientX - r.left) / r.width) * duration;
		return Math.min(Math.max(t, 0.1), duration - 0.1);
	}

	function on_down(e: PointerEvent, i: number) {
		if (!editable || frames[i].kind !== "key") return;
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
		drag = { i, t: frames[i].t, moved: false };
		e.preventDefault();
	}

	function on_move(e: PointerEvent) {
		if (!drag) return;
		drag = { ...drag, t: time_at(e.clientX), moved: true };
	}

	function on_up() {
		if (!drag) return;
		const { i, t, moved } = drag;
		drag = null;
		if (moved && round1(t) !== frames[i].t) commit_frame(i, t);
	}

	function on_key(e: KeyboardEvent, i: number) {
		if (!editable || frames[i].kind !== "key") return;
		const step = e.key === "ArrowRight" ? 0.1 : e.key === "ArrowLeft" ? -0.1 : 0;
		if (!step) return;
		e.preventDefault();
		const t = Math.min(Math.max(frames[i].t + step, 0.1), duration - 0.1);
		commit_frame(i, t);
	}

	function select_section(i: number) {
		if (!value?.selectable) return;
		const s = sections[i];
		value = { ...value, selected_section: i };
		gradio.dispatch("select", {
			index: i,
			value: { start: s.start, end: s.end, order: s.order }
		});
	}

	function frame_label(f: Frame) {
		const name = f.label ?? f.kind;
		return `${name} keyframe at ${fmt(f.t)} seconds${f.set === false ? ", not set" : ""}`;
	}
</script>

<div
	id={elem_id || null}
	class="fps-timeline {elem_classes.join(' ')}"
	class:hidden={!visible}
	class:boxed={container}
	style:flex-grow={scale}
	style:min-width={min_width ? `${min_width}px` : null}
>
	{#if (show_label && label) || (duration && caption)}
		<div class="head">
			{#if show_label && label}<span class="block-label">{label}</span>{/if}
			{#if duration && caption}<span class="caption">{caption}</span>{/if}
		</div>
	{/if}

	{#if !duration}
		<div class="placeholder">Timeline appears once a length is set</div>
	{:else}
		<div class="grid">
			<!-- ruler -->
			<div class="lane-label"></div>
			<div class="track ruler" bind:clientWidth={track_width}>
				{#each ticks as tk}
					<span class="tick {tk.anchor}" style:left={pct(tk.t)}>{fmt(tk.t)}s</span>
				{/each}
			</div>

			<!-- sections -->
			<div class="lane-label">Sections</div>
			<div class="track sections">
				{#each sections as s, i}
					{@const st = cell_state(s, i)}
					{@const w = ((s.end - s.start) / duration) * track_width}
					<button
						type="button"
						class="cell {st}"
						class:alt={i % 2 === 1}
						class:clickable={value.selectable}
						style={span(s.start, s.end)}
						tabindex={value.selectable ? 0 : -1}
						aria-disabled={!value.selectable}
						title={`${fmt(s.start)}–${fmt(s.end)} s${s.order != null ? `, generated #${s.order}` : ""}${st !== "normal" ? ` (${st})` : ""}`}
						aria-label={`Section ${i + 1}, ${fmt(s.start)} to ${fmt(s.end)} seconds`}
						on:click={() => select_section(i)}
					>
						{#if s.order != null && w >= 16}<span class="order">{s.order}</span>{/if}
					</button>
				{/each}
			</div>

			<!-- prompts -->
			<div class="lane-label">Prompt</div>
			<div class="track prompts">
				{#if prompts.length === 0}
					<span class="empty-note">No prompt</span>
				{/if}
				{#each prompts as p, i}
					<div
						class="bar prompt"
						class:alt={i % 2 === 1}
						style={span(p.start, p.end)}
						title={p.text}
					>
						<span class="txt">{p.text}</span>
					</div>
				{/each}
				{#if blend > 0}
					{#each prompts.slice(1) as p, i}
						<div
							class="blend"
							class:rev={i % 2 === 1}
							style={span(p.start - blend / 2, p.start + blend / 2)}
							title={`Blend ${fmt(blend)} s`}
						></div>
					{/each}
				{/if}
			</div>

			<!-- frames -->
			<div class="lane-label top">Frames</div>
			<div
				class="track frames"
				class:disabled={!keys_enabled}
				bind:this={frames_track}
			>
				<div class="axis"></div>
				{#each frames as f, i}
					{@const t = drag && drag.i === i ? drag.t : f.t}
					{@const draggable = editable && f.kind === "key"}
					{#if f.kind === "key" && f.snapped != null && Math.abs(f.snapped - f.t) > 0.05 && !(drag && drag.i === i)}
						<div class="snap-line" style={span(Math.min(f.t, f.snapped), Math.max(f.t, f.snapped))}></div>
						<div
							class="marker ghost"
							style:left={pct(f.snapped)}
							title={`snaps to ${fmt(f.snapped)} s`}
						>
							<span class="diamond"></span>
						</div>
					{/if}
					<button
						type="button"
						class="marker {f.kind}"
						class:unset={f.set === false}
						class:draggable
						class:dragging={drag && drag.i === i}
						style:left={pct(t)}
						aria-label={frame_label(f)}
						title={f.kind === "key" && f.snapped != null && Math.abs(f.snapped - f.t) > 0.05
							? `${f.label ?? "Key"} at ${fmt(f.t)} s, snaps to ${fmt(f.snapped)} s`
							: `${f.label ?? f.kind} at ${fmt(f.t)} s`}
						tabindex={draggable || f.kind !== "key" ? 0 : -1}
						on:pointerdown={(e) => on_down(e, i)}
						on:pointermove={on_move}
						on:pointerup={on_up}
						on:pointercancel={on_up}
						on:keydown={(e) => on_key(e, i)}
					>
						<span class="diamond"></span>
						<span class="mlabel {anchor(t)}">
							{#if drag && drag.i === i}{t.toFixed(2)} s{:else}{f.label ?? ""}{/if}
						</span>
					</button>
				{/each}
			</div>
			{#if !keys_enabled && value.keyframes_reason}
				<div class="lane-label"></div>
				<div class="note">{value.keyframes_reason}</div>
			{/if}

			<!-- extra lanes -->
			{#each lanes as ln}
				<div class="lane-label" title={ln.label}>{ln.label}</div>
				<div class="track lane">
					<div
						class="bar extra"
						class:off={ln.enabled === false}
						style={span(ln.start, ln.end)}
						title={ln.enabled === false ? `${ln.text ?? ""} (${ln.reason ?? "disabled"})` : ln.text}
					>
						<span class="txt">
							{#if ln.enabled === false}{ln.reason || "Disabled"}{:else}{ln.text ?? ""}{/if}
						</span>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.fps-timeline {
		position: relative;
		font-family: inherit;
		color: var(--body-text-color);
		min-width: 0;
		width: 100%;
	}
	.fps-timeline.boxed {
		padding: var(--block-padding);
		border: 1px solid var(--border-color-primary);
		border-radius: var(--block-radius);
		background: var(--background-fill-primary);
	}
	.hidden {
		display: none;
	}
	.head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 8px;
		margin-bottom: 6px;
		min-height: 18px;
	}
	.block-label {
		font-size: var(--block-label-text-size);
		font-weight: var(--block-label-text-weight, 400);
		color: var(--block-label-text-color, var(--body-text-color-subdued));
	}
	.caption {
		margin-left: auto;
		font-size: var(--text-xs);
		color: var(--body-text-color-subdued);
		white-space: nowrap;
	}
	.placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 72px;
		border: 1px dashed var(--border-color-primary);
		border-radius: var(--radius-sm, 4px);
		color: var(--body-text-color-subdued);
		font-size: var(--text-sm);
	}

	.grid {
		display: grid;
		grid-template-columns: 72px minmax(0, 1fr);
		column-gap: 10px;
		row-gap: 5px;
		align-items: center;
		padding-right: 6px;
	}
	.lane-label {
		font-size: var(--text-xs);
		color: var(--body-text-color-subdued);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.lane-label.top {
		align-self: start;
		line-height: 18px;
	}
	.track {
		position: relative;
		height: 20px;
		min-width: 0;
	}

	/* ruler */
	.ruler {
		height: 14px;
	}
	.tick {
		position: absolute;
		top: 0;
		font-size: 10px;
		line-height: 14px;
		color: var(--body-text-color-subdued);
		font-variant-numeric: tabular-nums;
		transform: translateX(-50%);
		white-space: nowrap;
	}
	.tick.left {
		transform: none;
	}
	.tick.right {
		transform: translateX(-100%);
	}

	/* sections */
	.sections {
		height: 24px;
		border-radius: 4px;
		overflow: hidden;
		background: var(--background-fill-secondary);
		box-shadow: inset 0 0 0 1px var(--border-color-primary);
	}
	.cell {
		position: absolute;
		top: 0;
		bottom: 0;
		margin: 0;
		padding: 0;
		border: none;
		border-right: 1px solid var(--border-color-primary);
		background: transparent;
		color: var(--body-text-color-subdued);
		font: inherit;
		cursor: default;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.cell:last-child {
		border-right: none;
	}
	.cell.alt {
		background: color-mix(in srgb, var(--body-text-color) 5%, transparent);
	}
	.cell.clickable {
		cursor: pointer;
	}
	.cell.clickable:hover {
		background: color-mix(in srgb, var(--color-accent) 12%, transparent);
	}
	.cell.kept {
		background: color-mix(in srgb, var(--body-text-color) 12%, transparent);
		color: color-mix(in srgb, var(--body-text-color-subdued) 70%, transparent);
	}
	.cell.regen {
		background: repeating-linear-gradient(
				-45deg,
				color-mix(in srgb, var(--color-accent) 30%, transparent) 0 3px,
				transparent 3px 7px
			),
			color-mix(in srgb, var(--color-accent) 12%, transparent);
		color: var(--color-accent);
	}
	.cell.selected {
		background: color-mix(in srgb, var(--color-accent) 18%, transparent);
		box-shadow: inset 0 0 0 2px var(--color-accent);
		color: var(--color-accent);
	}
	.cell:focus-visible {
		outline: 2px solid var(--color-accent);
		outline-offset: -2px;
	}
	.order {
		font-size: 10px;
		font-weight: 600;
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}

	/* bars (prompts and lanes) */
	.bar {
		position: absolute;
		top: 0;
		bottom: 0;
		display: flex;
		align-items: center;
		padding: 0 6px;
		border-radius: 4px;
		overflow: hidden;
		box-sizing: border-box;
		font-size: var(--text-xs);
	}
	.txt {
		overflow: hidden;
		white-space: nowrap;
		text-overflow: ellipsis;
		min-width: 0;
		position: relative;
		z-index: 3;
	}
	.prompt {
		background: color-mix(in srgb, var(--color-accent) 14%, var(--background-fill-primary));
		border: 1px solid color-mix(in srgb, var(--color-accent) 35%, transparent);
	}
	.prompt.alt {
		background: color-mix(in srgb, var(--color-accent) 26%, var(--background-fill-primary));
	}
	.prompt + .prompt {
		border-left: none;
	}
	.blend {
		position: absolute;
		top: 0;
		bottom: 0;
		z-index: 2;
		pointer-events: auto;
		background: linear-gradient(
			to right,
			transparent,
			color-mix(in srgb, var(--color-accent) 30%, transparent) 50%,
			transparent
		);
	}
	.empty-note {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		padding-left: 6px;
		font-size: var(--text-xs);
		font-style: italic;
		color: var(--body-text-color-subdued);
		border: 1px dashed var(--border-color-primary);
		border-radius: 4px;
	}
	.extra {
		background: var(--background-fill-secondary);
		border: 1px solid var(--border-color-primary);
	}
	.extra.off {
		color: var(--body-text-color-subdued);
		font-style: italic;
		background: repeating-linear-gradient(
				-45deg,
				color-mix(in srgb, var(--body-text-color) 7%, transparent) 0 4px,
				transparent 4px 9px
			),
			var(--background-fill-secondary);
		border-style: dashed;
	}

	/* frames */
	.frames {
		height: 34px;
		touch-action: none;
		user-select: none;
	}
	.axis {
		position: absolute;
		left: 0;
		right: 0;
		top: 9px;
		height: 1px;
		background: var(--border-color-primary);
	}
	.marker {
		position: absolute;
		top: 0;
		width: 18px;
		height: 34px;
		margin: 0;
		padding: 0;
		border: none;
		background: none;
		transform: translateX(-50%);
		cursor: default;
		color: var(--body-text-color);
		font: inherit;
		z-index: 3;
		touch-action: none;
	}
	.marker .diamond {
		position: absolute;
		left: 4px;
		top: 4px;
		width: 10px;
		height: 10px;
		box-sizing: border-box;
		transform: rotate(45deg);
		border-radius: 2px;
		background: var(--body-text-color);
		border: 1.5px solid var(--body-text-color);
	}
	.marker.key .diamond {
		background: var(--color-accent);
		border-color: var(--color-accent);
	}
	.marker.unset .diamond {
		background: var(--background-fill-primary);
		border-style: dashed;
		border-color: var(--body-text-color-subdued);
	}
	.marker.key.unset .diamond {
		border-color: var(--color-accent);
	}
	.marker.draggable {
		cursor: ew-resize;
	}
	.marker.draggable:hover .diamond,
	.marker.dragging .diamond {
		transform: rotate(45deg) scale(1.25);
		box-shadow: 0 0 0 3px var(--color-accent-soft);
	}
	.marker:focus-visible {
		outline: none;
	}
	.marker:focus-visible .diamond {
		box-shadow: 0 0 0 2px var(--background-fill-primary), 0 0 0 4px var(--color-accent);
	}
	.marker.dragging {
		z-index: 5;
	}
	.mlabel {
		position: absolute;
		top: 18px;
		left: 50%;
		transform: translateX(-50%);
		font-size: 10px;
		line-height: 14px;
		white-space: nowrap;
		color: var(--body-text-color-subdued);
		font-variant-numeric: tabular-nums;
		pointer-events: none;
	}
	.mlabel.left {
		left: 4px;
		transform: none;
	}
	.mlabel.right {
		left: auto;
		right: 4px;
		transform: none;
	}
	.marker.key .mlabel {
		color: var(--color-accent);
		font-weight: 600;
	}
	.marker.dragging .mlabel {
		color: var(--body-text-color);
		background: var(--background-fill-primary);
		border: 1px solid var(--color-accent);
		border-radius: 3px;
		padding: 0 4px;
	}
	.marker.ghost {
		pointer-events: auto;
		z-index: 2;
		opacity: 0.6;
	}
	.marker.ghost .diamond {
		background: transparent;
		border: 1.5px dashed var(--color-accent);
	}
	.snap-line {
		position: absolute;
		top: 8px;
		height: 0;
		border-top: 1.5px dashed var(--color-accent);
		opacity: 0.7;
		z-index: 1;
	}
	.frames.disabled .marker.key .diamond {
		background: var(--body-text-color-subdued);
		border-color: var(--body-text-color-subdued);
		opacity: 0.45;
	}
	.frames.disabled .marker.key .mlabel {
		color: var(--body-text-color-subdued);
		font-weight: 400;
	}
	.frames.disabled .snap-line,
	.frames.disabled .ghost {
		display: none;
	}
	.note {
		font-size: var(--text-xs);
		color: var(--body-text-color-subdued);
		font-style: italic;
		margin-top: -2px;
	}
</style>
