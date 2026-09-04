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
let SALTOS_MINIMOS = 4; // mínimo de palavras no caminho para vitória

// Armazena similaridades das arestas para exibição na lista de links
let registroLinks = []; // [{de, para, pct}]

// ========== CONFIGURAÇÃO VIS.JS ==========
const configuracaoVis = {
    nodes: {
        shape: 'box',
        shapeProperties: { borderRadius: 16 },
        margin: { top: 6, bottom: 6, left: 12, right: 12 },
        font: { size: 14, face: 'DM Sans, system-ui, sans-serif', color: '#e0e0e0' },
        borderWidth: 2,
        borderWidthSelected: 3,
        shadow: { enabled: false },
        chosen: false
    },
    edges: {
        color: { color: '#555', highlight: '#888' },
        width: 1,
        font: { size: 10, face: 'DM Sans, system-ui, sans-serif', color: '#777', align: 'top' },
        smooth: { type: 'continuous', roundness: 0.2 }
    },
    physics: {
        barnesHut: {
            springLength: 180,
            springConstant: 0.03,
            damping: 0.15,
            avoidOverlap: 0.3
        },
        stabilization: { iterations: 80 }
    },
    interaction: { hover: true, tooltipDelay: 200 }
};

// ========== TEMA (DARK/LIGHT) ==========
function aplicarTema(tema) {
    document.documentElement.setAttribute('data-theme', tema);
    localStorage.setItem('linxicon-tema', tema);
    document.getElementById('btn-tema').textContent = tema === 'light' ? '🌙' : '☀️';

    // Atualizar cores do Vis.js
    if (network) {
        const isDark = tema !== 'light';
        const fontColor = isDark ? '#e0e0e0' : '#333';
        /*
        network.setOptions({
            nodes: { font: { color: fontColor } },
            edges: { 
                color: { color: isDark ? '#555' : '#ccc', highlight: isDark ? '#888' : '#666' },
                font: { color: isDark ? '#777' : '#888' }
            }
        });
        */
    }
}

function alternarTema() {
    const atual = document.documentElement.getAttribute('data-theme');
    aplicarTema(atual === 'light' ? 'dark' : 'light');
}

// Inicializar tema (dark por padrão)
(function() {
    const salvo = localStorage.getItem('linxicon-tema');
    if (salvo) {
        aplicarTema(salvo);
    }
    // Dark é o padrão via CSS, não precisa fazer nada se não há tema salvo
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

// ========== ATUALIZAR PAINEL LATERAL ==========
function atualizarContagem() {
    const total = nodes.get().length;
    document.getElementById('contagem-palavras').textContent = total;
}

function atualizarListaLinks() {
    const container = document.getElementById('lista-links');
    
    if (registroLinks.length === 0) {
        container.innerHTML = '<p class="links-vazio">Nenhuma conexão ainda.</p>';
        return;
    }

    container.innerHTML = '';
    registroLinks.forEach(link => {
        const div = document.createElement('div');
        div.className = 'link-item conectado';
        div.innerHTML = `
            <div class="link-palavras">
                <span>${link.de}</span>
                <span class="link-sep">—</span>
                <span>${link.para}</span>
            </div>
            <span class="link-pct">(${link.pct}%)</span>
        `;
        container.appendChild(div);
    });
}

function atualizarMenorDistancia() {
    // Calcular a similaridade direta entre a última palavra conectada mais próxima
    // da origem e a mais próxima do destino (que ainda não estão ligadas)
    const todasArestas = edges.get();
    const todosNos = nodes.get();
    
    if (todosNos.length < 3) {
        document.getElementById('secao-menor-distancia').style.display = 'none';
        return;
    }

    // Encontrar as "fronteiras": nós conectados à origem vs conectados ao destino
    const adj = {};
    todosNos.forEach(n => adj[n.id] = []);
    todasArestas.forEach(e => {
        adj[e.from].push(e.to);
        adj[e.to].push(e.from);
    });

    // BFS da origem (id=1) para encontrar todos os nós alcançáveis
    const alcancaveisOrigem = new Set();
    const fila = [1];
    alcancaveisOrigem.add(1);
    while (fila.length > 0) {
        const atual = fila.shift();
        for (const vizinho of (adj[atual] || [])) {
            if (!alcancaveisOrigem.has(vizinho)) {
                alcancaveisOrigem.add(vizinho);
                fila.push(vizinho);
            }
        }
    }

    // Se destino (id=2) já é alcançável, mostrar gap como o caminho mais fraco
    if (alcancaveisOrigem.has(2)) {
        document.getElementById('secao-menor-distancia').style.display = 'none';
        return;
    }

    // Encontrar nós não alcançáveis pela origem (lado do destino)
    const alcancaveisDestino = new Set();
    const fila2 = [2];
    alcancaveisDestino.add(2);
    while (fila2.length > 0) {
        const atual = fila2.shift();
        for (const vizinho of (adj[atual] || [])) {
            if (!alcancaveisDestino.has(vizinho)) {
                alcancaveisDestino.add(vizinho);
                fila2.push(vizinho);
            }
        }
    }

    // Encontrar o par mais próximo entre os dois grupos
    // Usando os registros de links que temos (todas as similaridades calculadas)
    // Por agora, mostrar gap entre origem e destino calculado diretamente
    document.getElementById('secao-menor-distancia').style.display = 'block';
    document.getElementById('gap-origem').textContent = palavraInicial;
    document.getElementById('gap-destino').textContent = palavraFinal;
    
    // Encontrar o nó do lado da origem mais próximo ao lado do destino
    const nosOrigem = todosNos.filter(n => alcancaveisOrigem.has(n.id));
    const nosDestino = todosNos.filter(n => alcancaveisDestino.has(n.id));
    
    let menorGap = null;
    let melhorPar = null;

    // Usar as arestas existentes + similaridades conhecidas 
    // Para simplificar, vamos mostrar que os dois grupos não estão conectados
    document.getElementById('gap-display').textContent = 
        `${nosOrigem.map(n=>n.label).join(', ')} ↔ ${nosDestino.map(n=>n.label).join(', ')}`;
}

function exibirMenorCaminho(caminhoLabels) {
    const secao = document.getElementById('secao-menor-caminho');
    const container = document.getElementById('menor-caminho');
    secao.style.display = 'block';
    container.innerHTML = '';

    for (let i = 0; i < caminhoLabels.length - 1; i++) {
        const de = caminhoLabels[i];
        const para = caminhoLabels[i + 1];
        
        // Buscar a porcentagem no registro de links
        const link = registroLinks.find(l => 
            (l.de === de && l.para === para) || (l.de === para && l.para === de)
        );
        const pct = link ? link.pct : '?';

        const div = document.createElement('div');
        div.className = 'link-item no-caminho';
        div.innerHTML = `
            <div class="link-palavras">
                <span>${de}</span>
                <span class="link-sep">→</span>
                <span>${para}</span>
            </div>
            <span class="link-pct">(${pct}%)</span>
        `;
        container.appendChild(div);
    }
}

// ========== INICIAR JOGO ==========
async function iniciarJogo(modo) {
    modoAtual = modo || 'diario';
    jogoFinalizado = false;
    totalJogadas = 0;
    proximoId = 3;
    registroLinks = [];
    document.getElementById('contador-jogadas').textContent = '0';
    document.getElementById('contagem-palavras').textContent = '2';
    document.getElementById('modo-label').textContent = 
        modoAtual === 'diario' ? 'Desafio Diário' : 'Prática';

    // Limpar painel
    document.getElementById('lista-links').innerHTML = '<p class="links-vazio">Nenhuma conexão ainda.</p>';
    document.getElementById('secao-menor-distancia').style.display = 'none';
    document.getElementById('secao-menor-caminho').style.display = 'none';

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
        SALTOS_MINIMOS = dados.saltos_minimos || 4;

        // Atualizar tags visuais
        document.getElementById('tag-origem').textContent = palavraInicial;
        document.getElementById('tag-destino').textContent = palavraFinal;

        // Limpar e recriar grafo
        nodes.clear();
        edges.clear();

        nodes.add({
            id: 1,
            label: palavraInicial,
            color: { background: '#2a2548', border: '#7B68EE' },
            font: { color: '#c4b5fd' },
            borderWidth: 2,
            fixed: true,
            x: -250,
            y: 0
        });
        nodes.add({
            id: 2,
            label: palavraFinal,
            color: { background: '#3a2535', border: '#E87BA8' },
            font: { color: '#f0a0c0' },
            borderWidth: 2,
            fixed: true,
            x: 250,
            y: 0
        });

        const dadosGrafo = { nodes, edges };
        if (network !== null) {
            network.destroy();
            network = null;
        }
        network = new vis.Network(container, dadosGrafo, configuracaoVis);

        // Reaplicar tema ao Vis.js
        const tema = document.documentElement.getAttribute('data-theme');
        if (tema === 'light') {
            aplicarTema('light');
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
            const labels = caminho.map(id => {
                const no = nodes.get(id);
                return no ? no.label : '?';
            });
            
            // Verificação de dificuldade mínima:
            // Caminho precisa ter pelo menos 4 palavras (origem + 2 intermediárias + destino)
            if (labels.length < 4) {
                return { labels, tooShort: true };
            }
            
            return { labels, tooShort: false };
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

// ========== CALCULAR STATS DO HISTÓRICO ==========
function calcularStats() {
    const historico = JSON.parse(localStorage.getItem('linxicon-historico') || '[]');
    
    const totalPartidas = historico.length;
    const totalVitorias = historico.filter(h => h.vitoria !== false).length;
    
    // Calcular streak (dias consecutivos com vitória)
    let streakAtual = 0;
    let streakMax = 0;
    
    // Agrupar por data, pegar apenas vitórias no modo diário
    const vitoriasDiarias = [...new Set(
        historico
            .filter(h => h.modo === 'diario' && h.vitoria !== false)
            .map(h => h.data)
    )].sort().reverse();
    
    if (vitoriasDiarias.length > 0) {
        streakAtual = 1;
        for (let i = 1; i < vitoriasDiarias.length; i++) {
            const d1 = new Date(vitoriasDiarias[i - 1]);
            const d2 = new Date(vitoriasDiarias[i]);
            const diffDias = Math.round((d1 - d2) / (1000 * 60 * 60 * 24));
            if (diffDias === 1) {
                streakAtual++;
            } else {
                break;
            }
        }
        
        // Calcular streak máximo
        let tempStreak = 1;
        const datasOrdenadas = [...vitoriasDiarias].reverse();
        for (let i = 1; i < datasOrdenadas.length; i++) {
            const d1 = new Date(datasOrdenadas[i]);
            const d2 = new Date(datasOrdenadas[i - 1]);
            const diffDias = Math.round((d1 - d2) / (1000 * 60 * 60 * 24));
            if (diffDias === 1) {
                tempStreak++;
            } else {
                streakMax = Math.max(streakMax, tempStreak);
                tempStreak = 1;
            }
        }
        streakMax = Math.max(streakMax, tempStreak);
    }

    return { totalPartidas, totalVitorias, streakAtual, streakMax };
}

// ========== MODAL DE VITÓRIA ==========
function mostrarVitoria(caminhoLabels) {
    jogoFinalizado = true;

    // Exibir menor caminho no painel lateral
    exibirMenorCaminho(caminhoLabels);

    // Salvar histórico
    salvarHistorico(caminhoLabels, true);

    // Calcular stats
    const stats = calcularStats();
    document.getElementById('stat-partidas').textContent = stats.totalPartidas;
    document.getElementById('stat-vitorias').textContent = stats.totalVitorias;
    document.getElementById('stat-streak-atual').textContent = stats.streakAtual;
    document.getElementById('stat-streak-max').textContent = stats.streakMax;

    // Mostrar modal
    document.getElementById('modal-vitoria').classList.add('visivel');
}

function fecharModal() {
    document.getElementById('modal-vitoria').classList.remove('visivel');
    // NÃO reinicia o jogo — jogador pode inspecionar o grafo
}

function fecharModalOverlay(event) {
    // Fechar apenas se clicou no overlay, não no modal
    if (event.target === event.currentTarget) {
        fecharModal();
    }
}

function jogarNovamente() {
    fecharModal();
    iniciarJogo('pratica');
}

// ========== COMPARTILHAR ==========
function compartilhar() {
    const texto = `🔗 Linxicon PT-BR\n${palavraInicial} → ${palavraFinal}\n\n✅ ${totalJogadas} jogadas`;

    navigator.clipboard.writeText(texto).then(() => {
        mostrarToast('Resultado copiado para a área de transferência!', 'sucesso');
    }).catch(() => {
        mostrarToast('Erro ao copiar. Tente manualmente.', 'erro');
    });
}

// ========== HISTÓRICO (LOCALSTORAGE) ==========
function salvarHistorico(caminho, vitoria = true) {
    const historico = JSON.parse(localStorage.getItem('linxicon-historico') || '[]');
    historico.push({
        data: new Date().toISOString().slice(0, 10),
        modo: modoAtual,
        palavraInicial,
        palavraFinal,
        jogadas: totalJogadas,
        ponte: caminho.length,
        caminho: caminho,
        vitoria: vitoria
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
                    font: { align: 'top', size: 10 }
                };
                if (mostrarPorcentagem) {
                    arestaConfig.label = dados.similaridade + '%';
                }
                novasArestas.push(arestaConfig);
                
                // Registrar link para o painel lateral
                registroLinks.push({
                    de: palavraJogada,
                    para: node.label,
                    pct: dados.similaridade
                });
            }
        } catch (erro) {
            console.error('Erro na comunicação com a API:', erro);
        }
    }

    setLoading(false);

    // Sempre adicionar o nó, mesmo sem conexões
    nodes.add({
        id: novoNodeId,
        label: palavraJogada,
        color: { background: '#2a2a3e', border: '#888' },
        font: { color: '#e0e0e0' },
        borderWidth: 1
    });
    proximoId++;
    totalJogadas++;
    document.getElementById('contador-jogadas').textContent = totalJogadas;
    atualizarContagem();

    // Registrar palavra na sessão do backend
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

    if (conectouComAlgo) {
        edges.add(novasArestas);
        atualizarListaLinks();
        atualizarMenorDistancia();

        // Efeito visual: flash verde no novo nó
        setTimeout(() => {
            nodes.update({
                id: novoNodeId,
                color: { background: 'rgba(74, 222, 128, 0.2)', border: '#4ade80' }
            });
            setTimeout(() => {
                nodes.update({
                    id: novoNodeId,
                    color: { background: '#2a2a3e', border: '#888' }
                });
            }, 600);
        }, 100);

        mostrarToast(`"${palavraJogada}" conectou! (${maiorSimilaridade}%)`, 'sucesso');

        // Verificar vitória
        const resultado = verificarVitoria();
        if (resultado) {
            if (resultado.tooShort) {
                mostrarToast(
                    `Ponte muito curta! Precisa de pelo menos 2 palavras intermediárias.`, 
                    'morno'
                );
            } else {
                setTimeout(() => mostrarVitoria(resultado.labels), 800);
            }
        }
    } else {
        // Sem mensagem de rejeição, apenas confirmar que foi para o tabuleiro
        mostrarToast(`"${palavraJogada}" adicionada ao tabuleiro (sem conexões fortes).`, 'info');
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
