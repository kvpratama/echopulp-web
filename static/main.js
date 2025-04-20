// AJAX subscribe/unsubscribe for search page

console.log("main JS loaded");

function attachSearchSubFormListeners() {
    document.querySelectorAll(".search-sub-form").forEach(function(form) {
        if (form.dataset.ajaxified) return; // Prevent double-binding
        form.dataset.ajaxified = 'true';
        form.addEventListener("submit", async function(e) {
            e.preventDefault();
            const btn = form.querySelector("button");
            btn.disabled = true;
            // Save podcast id and scroll position
            const card = form.closest('.card');
            const podcastId = form.querySelector('[name="podcast_id"], [name="podcast_id"]')?.value;
            const cardTop = card ? card.offsetTop : null;
            const formData = new FormData(form);
            const action = form.getAttribute("action");
            const method = form.getAttribute("method") || "post";
            try {
                const resp = await fetch(action, {
                    method: method.toUpperCase(),
                    body: formData
                });
                if (resp.redirected) {
                    const newDoc = await fetch(resp.url);
                    const html = await newDoc.text();
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, "text/html");
                    // Find the updated card by podcast_id using a data attribute
                    let newCard = null;
                    if (podcastId) {
                        const newCards = Array.from(doc.querySelectorAll('.card'));
                        for (const c of newCards) {
                            // Use data-podcast-id for reliability
                            if (c.dataset.podcastId === podcastId) {
                                newCard = c;
                                break;
                            }
                        }
                        // Fallback to old way if data attribute isn't set
                        if (!newCard) {
                            for (const c of newCards) {
                                if (c.innerHTML.includes(`value=\"${podcastId}\"`)) {
                                    newCard = c;
                                    break;
                                }
                            }
                        }
                    }
                    if (newCard && card) {
                        // Replace the card with the new version
                        card.replaceWith(newCard);
                        // Re-attach listeners to new forms
                        attachSearchSubFormListeners();
                        window.requestAnimationFrame(() => {
                            // Scroll to the new card (by podcast id)
                            const targetCard = document.querySelector('.card[data-podcast-id="' + podcastId + '"]') || newCard;
                            if (targetCard) {
                                window.scrollTo({top: targetCard.offsetTop, behavior: 'auto'});
                            } else if (cardTop !== null) {
                                window.scrollTo({top: cardTop, behavior: 'auto'});
                            }
                        });
                    } else {
                        // Fallback: replace the full row and restore scroll
                        const newRow = doc.querySelector(".row");
                        if (newRow) {
                            document.querySelector(".row").replaceWith(newRow);
                        }
                        // Re-attach listeners to new forms
                        attachSearchSubFormListeners();
                        window.requestAnimationFrame(() => {
                            if (podcastId) {
                                const targetCard = document.querySelector('.card[data-podcast-id="' + podcastId + '"]');
                                if (targetCard) {
                                    window.scrollTo({top: targetCard.offsetTop, behavior: 'auto'});
                                    return;
                                }
                            }
                            if (cardTop !== null) {
                                window.scrollTo({top: cardTop, behavior: 'auto'});
                            }
                        });
                    }
                    // Update feedback message
                    const newMsg = doc.querySelector(".alert.alert-info");
                    const oldMsg = document.querySelector(".alert.alert-info");
                    if (oldMsg) oldMsg.remove();
                    if (newMsg) document.querySelector("h2").after(newMsg);
                } else {
                    // Try to update button state in-place
                    const data = await resp.json();
                    // Not implemented: fallback
                }
            } catch (err) {
                alert("Error: " + err);
            } finally {
                btn.disabled = false;
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", function () {
    attachSearchSubFormListeners();
    
    document.querySelectorAll('.summarize-btn').forEach(function(btn) {
        btn.addEventListener('click', async function() {
            const episodeId = btn.getAttribute('data-episode-id');
            const audioUrl = btn.getAttribute('data-audio-url');
            const modal = new bootstrap.Modal(document.getElementById('summaryModal'));
            const modalBody = document.getElementById('summaryModalBody');
            modalBody.innerHTML = 'Loading summary...';
            modal.show();
            try {
                const resp = await fetch('/summarize_podcast', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        episode_id: episodeId,
                        audio_url: audioUrl
                    })
                });
                const data = await resp.json();
                if (data.summary) {
                    modalBody.innerHTML = data.summary;
                } else if (data.status === 'success') {
                    modalBody.innerHTML = 'Summary is being generated and will be available soon.';
                } else {
                    modalBody.innerHTML = 'Failed to generate summary.';
                }
            } catch (e) {
                modalBody.innerHTML = 'Error: ' + e;
            }
        });
    });
});
