// ========== ESTADO DO JOGO ==========
const API = 'http://127.0.0.1:8000';
const container = document.getElementById('grafo-jogo');
let nodes = new vis.DataSet([]);
let edges = new vis.DataSet([]);
let network = null;
let proximoId = 3; // 1 = origem, 2 = destino
let totalJogadas = 0;
let jogoFinalizado = false;
let modoAtual = 'diario'; // 'diario' ou 'pratica'
let palavraInicial = '';
let palavraFinal = '';
let THRESHOLD = 50.0;
let mostrarPorcentagem = true;
let sessionId = null;

// ========== CONFIGURAÇÃO VIS.JS ==========
const configuracaoVis = {
    nodes: {
        shape: 'box',
        margin: { top: 8, bottom: 8, left: 14, right: 14 },
        font: { size: 16, face: 'DM Sans, system-ui, sans-serif', color: '#333' },
        borderWidth: 2,
        borderWidthSelected: 3,
        shadow: { enabled: true, size: 6, x: 0, y: 2, color: 'rgba(0,0,0,0.1)' },
        chosen: false
    },
    edges: {
        color: { color: '#999', highlight: '#666' },
        width: 2,
        font: { size: 11, face: 'DM Sans, system-ui, sans-serif', color: '#888', align: 'top' },
        smooth: { type: 'continuous', roundness: 0.3 }
    },
    physics: {
        barnesHut: {
            springLength: 160,
            springConstant: 0.04,
            damping: 0.12,
            avoidOverlap: 0.3
        },
        stabilization: { iterations: 80 }
    },
    interaction: { hover: true, tooltipDelay: 200 }
};

// ========== TEMA (DARK MODE) ==========
function aplicarTema(tema) {
    document.documentElement.setAttribute('data-theme', tema);
    localStorage.setItem('linxicon-tema', tema);
    document.getElementById('btn-tema').textContent = tema === 'dark' ? '☀️' : '🌙';

    // Atualizar cores do Vis.js
    if (network) {
        const fontColor = tema === 'dark' ? '#e0e0e0' : '#333';
        network.setOptions({
            nodes: { font: { color: fontColor } },
            edges: { font: { color: tema === 'dark' ? '#aaa' : '#888' } }
        });
    }
}

function alternarTema() {
    const atual = document.documentElement.getAttribute('data-theme');
    aplicarTema(atual === 'dark' ? 'light' : 'dark');
}

// Inicializar tema
(function() {
    const salvo = localStorage.getItem('linxicon-tema');
    if (salvo) {
        aplicarTema(salvo);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        aplicarTema('dark');
    }
})();

// ========== TOAST NOTIFICATIONS ==========
function mostrarToast(mensagem, tipo = 'frio') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;
    toast.textContent = mensagem;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ========== LOADING STATE ==========
function setLoading(ativo) {
    const btn = document.getElementById('btn-conectar');
    const spinner = document.getElementById('spinner');
    const input = document.getElementById('input-palavra');

    btn.disabled = ativo;
    input.disabled = ativo;
    spinner.style.display = ativo ? 'inline-block' : 'none';
}

// ========== BUSCAR CONFIG ==========
async function buscarConfig() {
    try {
        const resp = await fetch(`${API}/config`);
        const dados = await resp.json();
        THRESHOLD = dados.threshold;
    } catch (e) {
        console.warn('Config não disponível, usando padrão:', THRESHOLD);
    }
}

// ========== INICIAR JOGO ==========
async function iniciarJogo(modo) {
    modoAtual = modo || 'diario';
    jogoFinalizado = false;
    totalJogadas = 0;
    proximoId = 3;
    document.getElementById('contador-jogadas').textContent = '0';

    // Atualizar tabs visuais
    document.getElementById('tab-diario').classList.toggle('ativo', modoAtual === 'diario');
    document.getElementById('tab-pratica').classList.toggle('ativo', modoAtual === 'pratica');

    const endpoint = modoAtual === 'diario' ? '/desafio-diario' : '/pratica';

    try {
        const resposta = await fetch(`${API}${endpoint}`);
        const dados = await resposta.json();

        palavraInicial = dados.palavra_inicial;
        palavraFinal = dados.palavra_final;
        sessionId = dados.session_id || null;

        // Atualizar tags visuais
        document.getElementById('tag-origem').textContent = palavraInicial;
        document.getElementById('tag-destino').textContent = palavraFinal;

        // Limpar e recriar grafo
        nodes.clear();
        edges.clear();

        nodes.add({
            id: 1,
            label: palavraInicial,
            color: { background: '#dbe7ff', border: '#0044CC' },
            font: { color: '#0044CC', bold: true }
        });
        nodes.add({
            id: 2,
            label: palavraFinal,
            color: { background: '#ffd6e2', border: '#B2003C' },
            font: { color: '#B2003C', bold: true }
        });

        const dadosGrafo = { nodes, edges };
        network = new vis.Network(container, dadosGrafo, configuracaoVis);

        // Reaplicar tema ao Vis.js
        const tema = document.documentElement.getAttribute('data-theme');
        if (tema === 'dark') {
            aplicarTema('dark');
        }

        console.log(`Jogo iniciado (${modoAtual}): ${palavraInicial} → ${palavraFinal}`);
    } catch (erro) {
        mostrarToast('Erro ao conectar com a API. O servidor está rodando?', 'erro');
        console.error(erro);
    }
}

function trocarModo(modo) {
    iniciarJogo(modo);
}

// ========== BFS: DETECÇÃO DE VITÓRIA ==========
function verificarVitoria() {
    const todasArestas = edges.get();
    const todosNos = nodes.get();

    // Construir grafo de adjacência
    const adj = {};
    todosNos.forEach(n => adj[n.id] = []);
    todasArestas.forEach(e => {
        adj[e.from].push(e.to);
        adj[e.to].push(e.from);
    });

    // BFS do nó 1 ao nó 2
    const visitados = new Set();
    const fila = [[1, [1]]]; // [nóAtual, caminhoAteAqui]
    visitados.add(1);

    while (fila.length > 0) {
        const [atual, caminho] = fila.shift();

        if (atual === 2) {
            return caminho.map(id => {
                const no = nodes.get(id);
                return no ? no.label : '?';
            });
        }

        for (const vizinho of (adj[atual] || [])) {
            if (!visitados.has(vizinho)) {
                visitados.add(vizinho);
                fila.push([vizinho, [...caminho, vizinho]]);
            }
        }
    }

    return null; // sem caminho
}

// ========== MODAL DE VITÓRIA ==========
function mostrarVitoria(caminho) {
    jogoFinalizado = true;

    // Preencher caminho visual
    const containerCaminho = document.getElementById('caminho-vitoria');
    containerCaminho.innerHTML = '';
    caminho.forEach((palavra, i) => {
        const span = document.createElement('span');
        span.className = 'caminho-palavra';
        span.textContent = palavra;
        containerCaminho.appendChild(span);

        if (i < caminho.length - 1) {
            const seta = document.createElement('span');
            seta.className = 'caminho-seta';
            seta.textContent = '→';
            containerCaminho.appendChild(seta);
        }
    });

    // Stats
    document.getElementById('stat-jogadas').textContent = totalJogadas;
    document.getElementById('stat-ponte').textContent = caminho.length;

    // Salvar histórico
    salvarHistorico(caminho);

    // Mostrar modal
    document.getElementById('modal-vitoria').classList.add('visivel');
}

function fecharModal() {
    document.getElementById('modal-vitoria').classList.remove('visivel');
}

function jogarNovamente() {
    fecharModal();
    iniciarJogo('pratica');
}

// ========== COMPARTILHAR ==========
function compartilhar() {
    const caminho = document.getElementById('caminho-vitoria').textContent;
    const texto = `🔗 Linxicon PT-BR\n${palavraInicial} → ${palavraFinal}\n\n${caminho}\n\n✅ ${totalJogadas} jogadas`;

    navigator.clipboard.writeText(texto).then(() => {
        mostrarToast('Resultado copiado para a área de transferência!', 'sucesso');
    }).catch(() => {
        mostrarToast('Erro ao copiar. Tente manualmente.', 'erro');
    });
}

// ========== HISTÓRICO (LOCALSTORAGE) ==========
function salvarHistorico(caminho) {
    const historico = JSON.parse(localStorage.getItem('linxicon-historico') || '[]');
    historico.push({
        data: new Date().toISOString().slice(0, 10),
        modo: modoAtual,
        palavraInicial,
        palavraFinal,
        jogadas: totalJogadas,
        ponte: caminho.length,
        caminho: caminho
    });
    localStorage.setItem('linxicon-historico', JSON.stringify(historico));
}

// ========== TENTAR PALAVRA ==========
async function tentarPalavra() {
    if (jogoFinalizado) {
        mostrarToast('Jogo finalizado! Inicie um novo jogo.', 'frio');
        return;
    }

    const inputEl = document.getElementById('input-palavra');
    const palavraJogada = inputEl.value.trim().toLowerCase();

    if (!palavraJogada) return;

    // Verificar duplicata
    const nosExistentes = nodes.get();
    if (nosExistentes.some(n => n.label === palavraJogada)) {
        mostrarToast('Você já jogou essa palavra!', 'morno');
        inputEl.value = '';
        return;
    }

    setLoading(true);

    let conectouComAlgo = false;
    let novoNodeId = proximoId;
    let novasArestas = [];
    let maiorSimilaridade = 0;
    let feedbackFinal = 'frio';

    for (let node of nosExistentes) {
        try {
            const resposta = await fetch(`${API}/validar-conexao`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    palavra_alvo: node.label,
                    palavra_jogada: palavraJogada,
                    session_id: sessionId,
                    palavras_existentes: nosExistentes.map(n => n.label)
                })
            });

            if (!resposta.ok) {
                if (resposta.status === 400) {
                    const erroJson = await resposta.json().catch(() => ({}));
                    const detalhe = erroJson.detail || `"${palavraJogada}" é inválida.`;
                    mostrarToast(detalhe, 'erro');
                    inputEl.value = '';
                    setLoading(false);
                    return;
                }
                continue;
            }

            const dados = await resposta.json();

            // Rastrear maior similaridade para feedback
            if (dados.similaridade > maiorSimilaridade) {
                maiorSimilaridade = dados.similaridade;
                feedbackFinal = dados.feedback;
            }

            if (dados.conectou) {
                conectouComAlgo = true;
                const arestaConfig = {
                    from: novoNodeId,
                    to: node.id,
                    font: { align: 'top', size: 11 }
                };
                if (mostrarPorcentagem) {
                    arestaConfig.label = dados.similaridade + '%';
                }
                novasArestas.push(arestaConfig);
            }
        } catch (erro) {
            console.error('Erro na comunicação com a API:', erro);
        }
    }

    setLoading(false);

    if (conectouComAlgo) {
        // Adicionar nó intermediário
        nodes.add({
            id: novoNodeId,
            label: palavraJogada,
            color: { background: '#E8E8E8', border: '#999' },
            font: { color: '#333' }
        });
        edges.add(novasArestas);
        proximoId++;
        totalJogadas++;
        document.getElementById('contador-jogadas').textContent = totalJogadas;

        // Registrar palavra na sessão do backend (#16)
        if (sessionId) {
            fetch(`${API}/confirmar-palavra`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    palavra: palavraJogada
                })
            }).catch(e => console.warn('Erro ao confirmar palavra na sessão:', e));
        }

        // Efeito visual: flash no novo nó
        setTimeout(() => {
            nodes.update({
                id: novoNodeId,
                color: { background: '#d4edda', border: '#28a745' }
            });
            setTimeout(() => {
                nodes.update({
                    id: novoNodeId,
                    color: { background: '#E8E8E8', border: '#999' }
                });
            }, 600);
        }, 100);

        mostrarToast(`"${palavraJogada}" conectou! (${maiorSimilaridade}%)`, 'sucesso');

        // Verificar vitória
        const caminhoVitoria = verificarVitoria();
        if (caminhoVitoria) {
            setTimeout(() => mostrarVitoria(caminhoVitoria), 800);
        }
    } else {
        totalJogadas++;
        document.getElementById('contador-jogadas').textContent = totalJogadas;

        // Feedback quente/morno/frio
        const msgs = {
            quente: `🔥 Quase! "${palavraJogada}" chegou a ${maiorSimilaridade}% — só faltou um pouco!`,
            morno:  `🌡️ Morno. "${palavraJogada}" atingiu ${maiorSimilaridade}% — tente algo mais próximo.`,
            frio:   `❄️ "${palavraJogada}" está longe (${maiorSimilaridade}%). Pense em outra direção.`
        };
        mostrarToast(msgs[feedbackFinal] || msgs.frio, feedbackFinal);
    }

    inputEl.value = '';
    inputEl.focus();
}

// ========== EVENT LISTENERS ==========
document.getElementById('input-palavra').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        tentarPalavra();
    }
});

// ========== INICIALIZAR ==========
buscarConfig().then(() => iniciarJogo('diario'));
