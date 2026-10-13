// Per-row queue actions (cancel / remove).
// Gradio inserts gr.HTML content as innerHTML, so scripts inside the queue
// template never run. This file is loaded once through gr.Blocks(head=...)
// and listens on the document, so re-rendered rows need no rebinding.
(function () {
  function sendQueueAction(action, jobId) {
    const input = document.querySelector("#queue-action-input textarea");
    const trigger = document.querySelector("#queue-action-trigger");
    const button = trigger && (trigger.tagName === "BUTTON" ? trigger : trigger.querySelector("button"));
    if (!input || !button) {
      console.warn("Queue action bridge components not found.");
      return;
    }
    input.value = JSON.stringify({ action: action, job_id: jobId });
    input.dispatchEvent(new Event("input", { bubbles: true }));
    button.click();
  }

  document.addEventListener("click", function (event) {
    const btn = event.target.closest(".queue-row-action-btn[data-action][data-job-id]");
    if (!btn || btn.disabled) return;
    event.preventDefault();
    btn.disabled = true; // avoid double clicks until the queue re-renders
    sendQueueAction(btn.dataset.action, btn.dataset.jobId);
  });
})();
