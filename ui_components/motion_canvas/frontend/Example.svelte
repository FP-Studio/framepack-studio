<script lang="ts">
	export let value: { arrows?: number[][] } | null;
	export let type: "gallery" | "table";
	export let selected = false;
	$: n = value?.arrows?.length ?? 0;
</script>

<div class:table={type === "table"} class:gallery={type === "gallery"} class:selected>
	{n ? `${n} ${n === 1 ? "arrow" : "arrows"}` : ""}
</div>

<style>
	.gallery {
		padding: var(--size-1) var(--size-2);
	}
	div {
		overflow: hidden;
		white-space: nowrap;
	}
</style>
