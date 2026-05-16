(function () {
  const script = document.currentScript;
  if (!script || !script.dataset.eventUrl || !window.EventSource) {
    return;
  }

  const currentPhase = script.dataset.currentPhase || null;
  const currentItem = script.dataset.currentItem || null;
  const liveRole = script.dataset.liveRole || null;
  const source = new EventSource(script.dataset.eventUrl);

  source.onmessage = function (message) {
    let event;
    try {
      event = JSON.parse(message.data);
    } catch (_error) {
      return;
    }

    const phase = event.phase == null ? null : String(event.phase);
    const item = event.item == null ? null : String(event.item);
    if (
      (liveRole === "teacher" && event.progress === true) ||
      phase !== currentPhase ||
      item !== currentItem
    ) {
      window.location.reload();
    }
  };
})();
