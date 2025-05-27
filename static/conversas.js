const historicoMensagens = {
    cliente1: [],
    cliente2: [],
    cliente3: []
};

let clienteAtivo = 'cliente1';

// 🔄 Seleciona o cliente na sidebar
function selecionarCliente(clienteId) {
    clienteAtivo = clienteId;

    // Remove 'active' de todos os itens
    document.querySelectorAll('#lista-clientes li').forEach(li => li.classList.remove('active'));

    // Adiciona 'active' ao cliente selecionado
    const seletor = `#lista-clientes li[onclick="selecionarCliente('${clienteId}')"]`;
    const elementoSelecionado = document.querySelector(seletor);
    if (elementoSelecionado) {
        elementoSelecionado.classList.add('active');
    }

    renderizarMensagens();
}

// 📤 Envia uma mensagem
function enviarMensagem() {
    const input = document.getElementById('mensagem');
    const mensagem = input.value.trim();

    if (mensagem === '') return;

    // Adiciona mensagem enviada
    historicoMensagens[clienteAtivo].push({ tipo: 'sent', texto: mensagem });

    // Simula resposta automática
    setTimeout(() => {
        historicoMensagens[clienteAtivo].push({
            tipo: 'received',
            texto: 'Resposta automática: ' + mensagem
        });
        renderizarMensagens();
    }, 1000);

    input.value = '';
    renderizarMensagens();
}

// 🖥️ Renderiza o chat do cliente selecionado
function renderizarMensagens() {
    const chatBox = document.getElementById('chat-messages');
    chatBox.innerHTML = '';

    const mensagens = historicoMensagens[clienteAtivo] || [];

    mensagens.forEach(msg => {
        const div = document.createElement('div');
        div.className = `message ${msg.tipo}`;
        div.innerText = msg.texto;
        chatBox.appendChild(div);
    });

    chatBox.scrollTop = chatBox.scrollHeight;
}
