const statusOutput = document.getElementById("statusOutput");
const documentList = document.getElementById("documentList");
const draftOutput = document.getElementById("draftOutput");
const insightsOutput = document.getElementById("insightsOutput");
const feedbackOutput = document.getElementById("feedbackOutput");
const queryInput = document.getElementById("queryInput");
const editedDraftInput = document.getElementById("editedDraftInput");

async function requestJson(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Request failed: ${response.status} ${errorText}`);
  }
  return response.json();
}

async function refreshStatus() {
  try {
    const payload = await requestJson("/api/status");
    statusOutput.textContent = `Status: ${payload.status}\nDocuments: ${payload.documents.length}\nVector store ready: ${payload.vector_store_ready}\nInsights count: ${payload.insights_count}`;
    documentList.textContent = payload.documents.length > 0 ? payload.documents.join("\n") : "No sample documents found.";
    await refreshInsights();
  } catch (error) {
    statusOutput.textContent = `Unable to load status. ${error.message}`;
  }
}

async function refreshInsights() {
  try {
    const payload = await requestJson("/api/insights");
    insightsOutput.textContent = payload.insights.length > 0 ? payload.insights.map((item, index) => `${index + 1}. [${item.type}] ${item.insight}`).join("\n") : "No learned insights yet.";
  } catch (error) {
    insightsOutput.textContent = `Unable to load insights. ${error.message}`;
  }
}

async function processDocuments() {
  try {
    const payload = await requestJson("/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rebuild: true }),
    });
    statusOutput.textContent = `Documents processed: ${payload.processed_documents}`;
    documentList.textContent = payload.documents.join("\n");
    await refreshStatus();
  } catch (error) {
    statusOutput.textContent = `Document processing failed. ${error.message}`;
  }
}

async function generateDraft() {
  try {
    const payload = await requestJson("/api/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryInput.value.trim(), draft_type: "summary" }),
    });
    draftOutput.textContent = payload.draft;
    editedDraftInput.value = payload.draft;
  } catch (error) {
    draftOutput.textContent = `Draft generation failed. ${error.message}`;
  }
}

async function submitFeedback() {
  try {
    const payload = await requestJson("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        original: draftOutput.textContent,
        edited: editedDraftInput.value.trim(),
        query: queryInput.value.trim(),
      }),
    });
    feedbackOutput.textContent = `Feedback applied. Insights count: ${payload.insights_count}`;
    await refreshInsights();
  } catch (error) {
    feedbackOutput.textContent = `Feedback submission failed. ${error.message}`;
  }
}

window.addEventListener("load", async () => {
  document.getElementById("processBtn").addEventListener("click", processDocuments);
  document.getElementById("draftBtn").addEventListener("click", generateDraft);
  document.getElementById("feedbackBtn").addEventListener("click", submitFeedback);
  await refreshStatus();
});
