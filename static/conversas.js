// static/conversas.js

// Dados simulados para chats e contatos (em um sistema real, viriam do backend)
const whatsappChatData = {
    'cliente1': {
        name: 'Empresa Alfa Ltda.',
        avatar: 'https://placehold.co/40x40/075e54/ffffff?text=AL',
        lastMessageSnippet: 'Contrato de serviços assinado e enviado.',
        lastMessageTime: '14:30',
        status: 'online',
        messages: [
            { sender: 'received', text: 'Olá Bloco 244! Recebemos a proposta de serviços de contabilidade. Parece ótimo!', timestamp: '14:20' },
            { sender: 'sent', text: 'Excelente! Estamos muito felizes em ter a Empresa Alfa a bordo. O contrato foi assinado e enviado por e-mail, certo?', timestamp: '14:22' },
            { sender: 'received', text: 'Sim, o contrato já foi assinado digitalmente e reenviado. Precisam de mais algum documento?', timestamp: '14:30' },
            { sender: 'sent', text: 'Perfeito! Por enquanto, está tudo certo. Nossa equipe fiscal entrará em contato para o onboarding e coleta de dados iniciais.', timestamp: '14:32' },
            { sender: 'received', text: 'Aguardamos o contato! Obrigado pela agilidade.', timestamp: '14:35' }
        ]
    },
    'cliente2': {
        name: 'Startup Inovação Tech',
        avatar: 'https://placehold.co/40x40/128c7e/ffffff?text=IT',
        lastMessageSnippet: 'Detalhes da folha de pagamento para startup.',
        lastMessageTime: 'Hoje, 09:45',
        status: 'online',
        messages: [
            { sender: 'received', text: 'Bom dia, Bloco 244! Queríamos discutir os detalhes da folha de pagamento para nossa nova contratação.', timestamp: '09:40' },
            { sender: 'sent', text: 'Bom dia! Podemos agendar uma call para amanhã às 10h para alinhar todos os pontos e as obrigações fiscais.', timestamp: '09:45' },
            { sender: 'received', text: 'Combinado! Me envie o convite. E sobre a consultoria para o plano de incentivo, já podemos avançar?', timestamp: '09:48' },
            { sender: 'sent', text: 'Sim, a proposta já está pronta. Enviarei junto com o convite da call. Será um prazer ajudá-los nesse projeto!', timestamp: '09:50' }
        ]
    },
    'cliente3': {
        name: 'Consultório Dr. Roberto',
        avatar: 'https://placehold.co/40x40/075e54/ffffff?text=DR',
        lastMessageSnippet: 'Dúvida sobre alíquota de ISS para serviço médico.',
        lastMessageTime: 'Há 1 hora',
        status: 'online',
        messages: [
            { sender: 'received', text: 'Olá, Bloco 244. Tenho uma dúvida sobre a alíquota de ISS para um novo serviço que vou oferecer. Poderiam me ajudar?', timestamp: '10:00' },
            { sender: 'sent', text: 'Olá Dr. Roberto! Com certeza. Qual seria o novo serviço? Precisamos verificar a classificação fiscal correta.', timestamp: '10:05' },
            { sender: 'received', text: 'É um procedimento estético avançado. Acredito que se enquadre em um código diferente.', timestamp: '10:10' },
            { sender: 'sent', text: 'Ok, estou consultando a legislação municipal. Retorno em breve com a informação precisa para você. Não se preocupe!', timestamp: '10:15' }
        ]
    },
    'contato1': {
        name: 'Parceiro Jurídico',
        avatar: 'https://placehold.co/40x40/128c7e/ffffff?text=PJ',
        status: 'Documentação para abertura de empresa'
    },
    'contato2': {
        name: 'Fornecedor de Software X',
        avatar: 'https://placehold.co/40x40/075e54/ffffff?text=FX',
        status: 'Fatura de licença de dezembro'
    },
    'contato3': {
        name: 'Maria (Estagiária)',
        avatar: 'https://placehold.co/40x40/128c7e/ffffff?text=MA',
        status: 'Precisando de orientação sobre o lançamento de notas.'
    },
    'contato4': {
        name: 'Banco Investimentos',
        avatar: 'https://placehold.co/40x40/075e54/ffffff?text=BI',
        status: 'Proposta de linha de crédito PJ'
    },
    'contato5': {
        name: 'Prefeitura Municipal',
        avatar: 'https://placehold.co/40x40/128c7e/ffffff?text=PM',
        status: 'Aguardando parecer sobre alvará'
    }
};

let currentWhatsappClient = null; // Cliente selecionado atualmente para a aba de conversas

/**
 * Renderiza a lista de chats e contatos na barra lateral do WhatsApp.
 */
function renderWhatsappSidebar() {
    const chatListEl = document.getElementById('chat-list-whatsapp');
    const contactListEl = document.getElementById('contact-list-whatsapp');

    chatListEl.innerHTML = '';
    contactListEl.innerHTML = '';

    // Renderiza CHATS
    for (const id in whatsappChatData) {
        if (whatsappChatData[id].messages) { // Se tiver mensagens, é um chat
            const chat = whatsappChatData[id];
            const li = document.createElement('li');
            li.dataset.clientId = id;
            if (id === currentWhatsappClient) {
                li.classList.add('active-chat');
            }
            li.onclick = () => selecionarWhatsappCliente(id);
            li.innerHTML = `
                <div class="client-avatar-chat">
                    <img src="${chat.avatar}" alt="Avatar ${chat.name}">
                </div>
                <div class="chat-info">
                    <h4 class="chat-name">${chat.name}</h4>
                    <p class="last-message-snippet">${chat.lastMessageSnippet || ''}</p>
                </div>
                <span class="message-time">${chat.lastMessageTime || ''}</span>
            `;
            chatListEl.appendChild(li);
        }
    }

    // Renderiza CONTATOS (apenas os que não são chats ativos na simulação)
    for (const id in whatsappChatData) {
        if (!whatsappChatData[id].messages) { // Se não tiver mensagens, é um contato simples
            const contact = whatsappChatData[id];
            const li = document.createElement('li');
            li.dataset.clientId = id; // Pode ser útil para futura funcionalidade de iniciar conversa
            li.onclick = () => alert(`Clicou no contato: ${contact.name}. Implementar início de conversa.`); // Apenas um alert por enquanto
            li.innerHTML = `
                <div class="client-avatar-chat">
                    <img src="${contact.avatar}" alt="Avatar ${contact.name}">
                </div>
                <div class="chat-info">
                    <h4 class="chat-name">${contact.name}</h4>
                    <p class="last-message-snippet">${contact.status || ''}</p>
                </div>
            `;
            contactListEl.appendChild(li);
        }
    }
}

/**
 * Seleciona um cliente na barra lateral e exibe suas mensagens.
 * @param {string} clientId
 */
function selecionarWhatsappCliente(clientId) {
    currentWhatsappClient = clientId;

    // Remove 'active-chat' de todos e adiciona ao selecionado
    document.querySelectorAll('#chat-list-whatsapp li').forEach(li => li.classList.remove('active-chat'));
    const selectedLi = document.querySelector(`#chat-list-whatsapp li[data-client-id="${clientId}"]`);
    if (selectedLi) {
        selectedLi.classList.add('active-chat');
    }

    const client = whatsappChatData[clientId];
    const chatHeader = document.getElementById('chat-main-header');
    chatHeader.innerHTML = `
        <div class="chat-partner-info">
            <div class="client-avatar-chat">
                <img src="${client.avatar}" alt="Avatar ${client.name}">
            </div>
            <div class="partner-details">
                <h3 id="chat-partner-name">${client.name}</h3>
                <p id="chat-partner-status" class="status-text">${client.status || 'online'}</p>
            </div>
        </div>
        <div class="header-action-icons">
            <i class="fas fa-search"></i>
            <i class="fas fa-ellipsis-v"></i>
        </div>
    `;

    renderWhatsappMessages(clientId);
}

/**
 * Renderiza as mensagens do cliente selecionado.
 * @param {string} clientId
 */
function renderWhatsappMessages(clientId) {
    const chatMessagesDisplay = document.getElementById('chat-messages-display');
    chatMessagesDisplay.innerHTML = '';

    const messages = whatsappChatData[clientId]?.messages || [];
    messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message-bubble', msg.sender);
        messageDiv.innerHTML = `
            <p>${msg.text}</p>
            <span class="timestamp">${msg.timestamp}</span>
        `;
        chatMessagesDisplay.appendChild(messageDiv);
    });

    chatMessagesDisplay.scrollTop = chatMessagesDisplay.scrollHeight; // Rola para o final
}

/**
 * Envia uma nova mensagem.
 */
function enviarWhatsappMensagem() {
    if (!currentWhatsappClient) {
        alert('Selecione uma conversa para enviar a mensagem.');
        return;
    }

    const messageInput = document.getElementById('message-input');
    const messageText = messageInput.value.trim();

    if (messageText) {
        const newMessage = {
            sender: 'sent',
            text: messageText,
            timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
        };
        whatsappChatData[currentWhatsappClient].messages.push(newMessage);
        whatsappChatData[currentWhatsappClient].lastMessageSnippet = messageText; // Atualiza snippet
        whatsappChatData[currentWhatsappClient].lastMessageTime = newMessage.timestamp; // Atualiza hora

        renderWhatsappMessages(currentWhatsappClient);
        renderWhatsappSidebar(); // Re-renderiza a sidebar para atualizar o snippet e a hora

        messageInput.value = '';

        // Simulação de resposta do outro lado
        setTimeout(() => {
            if (currentWhatsappClient) {
                const autoReply = {
                    sender: 'received',
                    text: 'Ok, obrigado! Recebi sua mensagem.',
                    timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
                };
                whatsappChatData[currentWhatsappClient].messages.push(autoReply);
                whatsappChatData[currentWhatsappClient].lastMessageSnippet = autoReply.text;
                whatsappChatData[currentWhatsappClient].lastMessageTime = autoReply.timestamp;
                renderWhatsappMessages(currentWhatsappClient);
                renderWhatsappSidebar();
            }
        }, 1000 + Math.random() * 1500);
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Inicializa a sidebar
    renderWhatsappSidebar();
    // Seleciona o primeiro cliente de chat por padrão, se houver
    const firstChatId = Object.keys(whatsappChatData).find(id => whatsappChatData[id].messages);
    if (firstChatId) {
        selecionarWhatsappCliente(firstChatId);
    }

    // Adiciona evento de clique ao botão de enviar mensagem
    const sendButton = document.getElementById('send-message-button');
    if (sendButton) {
        sendButton.addEventListener('click', enviarWhatsappMensagem);
    }

    // Adiciona evento de keypress para enviar mensagem com Enter
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                enviarWhatsappMensagem();
            }
        });
    }

    // Adiciona evento de clique para o banner de notificação (apenas para fechar)
    const notificationCloseBtn = document.querySelector('.notification-close');
    if (notificationCloseBtn) {
        notificationCloseBtn.addEventListener('click', () => {
            document.querySelector('.notification-banner').style.display = 'none';
        });
    }
});
