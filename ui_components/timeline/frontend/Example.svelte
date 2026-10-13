<script lang="ts">
	export let value: { duration?: number } | null;
	export let type: "gallery" | "table";
	export let selected = false;
</script>

<div class:table={type === "table"} class:gallery={type === "gallery"} class:selected>
	{value?.duration ? `${value.duration.toFixed(1)} s timeline` : ""}
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
