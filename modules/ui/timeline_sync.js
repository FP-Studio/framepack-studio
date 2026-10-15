// Create timeline <-> Latest result video: the timeline's playhead follows the
// video, and clicking a section jumps the video there. Loaded once through
// gr.Blocks(head=...); elements are looked up lazily because Gradio renders
// (and re-renders) the components after this runs.
(function () {
  const TIMELINE = "create-timeline";

  function sendPlayhead(t) {
    window.dispatchEvent(
      new CustomEvent("fps-timeline-playhead", { detail: { elem_id: TIMELINE, t: t } })
    );
  }

  // Media events don't bubble, so listen in the capture phase.
  ["timeupdate", "seeked", "loadedmetadata"].forEach(function (name) {
    document.addEventListener(
      name,
      function (event) {
        const video = event.target;
        if (video && video.closest && video.closest("#create-result")) {
          sendPlayhead(video.currentTime);
        }
      },
      true
    );
  });
  document.addEventListener(
    "emptied",
    function (event) {
      if (event.target.closest && event.target.closest("#create-result")) sendPlayhead(null);
    },
    true
  );

  // Clicking a section jumps the result video to it
  window.addEventListener("fps-timeline-seek", function (event) {
    const detail = event.detail || {};
    const video = document.querySelector("#create-result video");
    if (detail.elem_id !== TIMELINE || !video || !isFinite(video.duration)) return;
    video.currentTime = Math.min(Math.max(detail.t, 0), Math.max(video.duration - 0.05, 0));
  });
})();
