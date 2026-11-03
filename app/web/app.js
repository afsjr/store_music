const STORAGE_KEY = "emporio_session_id";
const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const newConversationButton = document.getElementById("new-conversation");
const configBanner = document.getElementById("config-banner");

let sessionId = localStorage.getItem(STORAGE_KEY);
let isSending = false;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function clearWelcome() {
  const welcome = messagesEl.querySelector(".welcome");
  if (welcome) welcome.remove();
}

function addMessage(role, content, citations = [], handoff = false) {
  clearWelcome();
  const article = document.createElement("article");
  article.className = `message ${role}`;
  article.innerHTML = escapeHtml(content);

  if (citations.length) {
    const citationsEl = document.createElement("div");
    citationsEl.className = "citations";
    for (const citation of citations) {
      const chip = document.createElement("span");
      chip.className = "citation";
      chip.textContent = `Manual, seção ${citation.section}, p. ${citation.page}`;
      citationsEl.appendChild(chip);
    }
    article.appendChild(citationsEl);
  }

  if (handoff) {
    const handoffEl = document.createElement("div");
    handoffEl.className = "handoff";
    handoffEl.textContent = "Atendimento encaminhado para a equipe.";
    article.appendChild(handoffEl);
  }

  messagesEl.appendChild(article);
  scrollToBottom();
  return article;
}

function addTyping() {
  clearWelcome();
  const wrapper = document.createElement("article");
  wrapper.className = "message assistant";
  wrapper.id = "typing-indicator";
  wrapper.innerHTML = '<span class="typing"><span></span><span></span><span></span></span>';
  messagesEl.appendChild(wrapper);
  scrollToBottom();
}

function removeTyping() {
  const typing = document.getElementById("typing-indicator");
  if (typing) typing.remove();
}

async function createSession() {
  const response = await fetch("/api/sessions", { method: "POST" });
  if (!response.ok) throw new Error("Não foi possível criar a sessão.");
  const data = await response.json();
  sessionId = data.session_id;
  localStorage.setItem(STORAGE_KEY, sessionId);
  return sessionId;
}

async function ensureSession() {
  if (!sessionId) {
    await createSession();
  }
  return sessionId;
}

async function loadHistory() {
  if (!sessionId) return;
  const response = await fetch(`/api/sessions/${sessionId}/messages?limit=50`);
  if (response.status === 404) {
    sessionId = null;
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  if (!response.ok) return;
  const data = await response.json();
  for (const message of data.messages) {
    addMessage(message.role, message.content, message.citations || []);
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    if (response.ok) return;
    const data = await response.json().catch(() => ({}));
    const detail = data.detail || {};
    if (detail.llm === "unavailable") {
      configBanner.textContent =
        "O provedor de LLM ainda não está configurado. Preencha DEEPSEEK_API_KEY no .env para conversar.";
      configBanner.classList.remove("hidden");
    }
  } catch {
    configBanner.textContent = "Não foi possível verificar a saúde da aplicação.";
    configBanner.classList.remove("hidden");
  }
}

async function sendMessage(text) {
  if (isSending || !text.trim()) return;
  isSending = true;
  sendButton.disabled = true;
  inputEl.value = "";
  inputEl.style.height = "auto";
  addMessage("user", text.trim());
  addTyping();

  try {
    await ensureSession();
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message: text.trim() }),
    });
    const data = await response.json().catch(() => ({}));
    removeTyping();

    if (!response.ok) {
      const detail =
        typeof data.detail === "string"
          ? data.detail
          : "Não foi possível responder agora. Tente novamente.";
      addMessage("error", detail);
      return;
    }

    if (data.session_id) {
      sessionId = data.session_id;
      localStorage.setItem(STORAGE_KEY, sessionId);
    }
    addMessage("assistant", data.reply, data.citations || [], data.handoff);
  } catch (error) {
    removeTyping();
    addMessage("error", "Falha de conexão com o atendimento. Tente novamente.");
  } finally {
    isSending = false;
    sendButton.disabled = false;
    inputEl.focus();
  }
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(inputEl.value);
});

inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage(inputEl.value);
  }
});

inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = `${Math.min(inputEl.scrollHeight, 160)}px`;
});

messagesEl.addEventListener("click", (event) => {
  const button = event.target.closest(".suggestion");
  if (button) {
    sendMessage(button.dataset.message || button.textContent);
  }
});

newConversationButton.addEventListener("click", async () => {
  sessionId = null;
  localStorage.removeItem(STORAGE_KEY);
  messagesEl.innerHTML = "";
  configBanner.classList.add("hidden");
  await createSession();
  window.location.reload();
});

(async function init() {
  await checkHealth();
  try {
    await ensureSession();
    await loadHistory();
    if (!messagesEl.querySelector(".message") && !messagesEl.querySelector(".welcome")) {
      const welcome = document.createElement("div");
      welcome.className = "welcome";
      welcome.innerHTML = `
        <h2>Olá! Como posso ajudar?</h2>
        <p>Posso consultar instrumentos, preços, estoque, promoções, pedidos e as políticas da loja.</p>
        <div class="suggestions">
          <button class="suggestion" type="button" data-message="Quais violões custam até R$ 1000?">Violões até R$ 1000</button>
          <button class="suggestion" type="button" data-message="Quanto custa o Takamine GD20?">Preço do Takamine GD20</button>
          <button class="suggestion" type="button" data-message="Qual o horário e o endereço da loja?">Horário e endereço</button>
          <button class="suggestion" type="button" data-message="Me arrependi da minha compra, posso devolver?">Política de devolução</button>
        </div>`;
      messagesEl.appendChild(welcome);
    }
  } catch {
    addMessage("error", "Não foi possível iniciar o atendimento.");
  }
})();
