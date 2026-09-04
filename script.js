const container = document.getElementById('grafo-jogo');
let nodes = new vis.DataSet([]);
let edges = new vis.DataSet([]);
let network = null;

const configuracaoVis = {
    nodes: { shape: 'box', margin: 10, font: { size: 18 } },
    physics: { barnesHut: { springLength: 150, springConstant: 0.05 } }
};

async function iniciarJogo() {
    try {
        const resposta = await fetch('http://127.0.0.1:8000/desafio-diario');
        const dados = await resposta.json();

        nodes.add({ id: 1, label: dados.palavra_inicial, color: '#ffcccb' });
        nodes.add({ id: 2, label: dados.palavra_final, color: '#cce5ff' });

        const dadosGrafo = { nodes: nodes, edges: edges };
        network = new vis.Network(container, dadosGrafo, configuracaoVis);

        console.log("Jogo iniciado! Caminho secreto:", dados.caminho_secreto);
    } catch (erro) {
        alert("Erro ao conectar com a API. A API Python está rodando?");
        console.error(erro);
    }
}

iniciarJogo();


async function tentarPalavra() {
    const inputEl = document.getElementById('input-palavra');
    const palavraJogada = inputEl.value.trim().toLowerCase();

    if (!palavraJogada) return;

    const nosExistentes = nodes.get();
    if (nosExistentes.some(n => n.label === palavraJogada)) {
        alert("Você já jogou essa palavra!");
        inputEl.value = '';
        return;
    }

    let conectouComAlgo = false;
    let novoNodeId = nodes.length + 1;
    let novasArestas = [];

    for (let node of nosExistentes) {
        try {
            const resposta = await fetch('http://127.0.0.1:8000/validar-conexao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    palavra_alvo: node.label,
                    palavra_jogada: palavraJogada
                })
            });

            if (!resposta.ok) {
                if (resposta.status === 400) {
                    alert(`A palavra "${palavraJogada}" não existe no dicionário.`);
                    inputEl.value = '';
                    return;
                }
                continue;
            }

            const dados = await resposta.json();

            if (dados.conectou) {
                conectouComAlgo = true;
                novasArestas.push({
                    from: novoNodeId,
                    to: node.id,
                    label: dados.similaridade + '%',
                    font: { align: 'top', size: 12 }
                });
            }
        } catch (erro) {
            console.error("Erro na comunicação com a API:", erro);
        }
    }

    if (conectouComAlgo) {
        nodes.add({ id: novoNodeId, label: palavraJogada, color: '#e2f0cb' });
        edges.add(novasArestas);
    } else {
        alert(`A palavra "${palavraJogada}" não tem conexão forte o suficiente (mín. 40%) com nenhuma bolha atual.`);
    }

    inputEl.value = '';
    inputEl.focus();
}

document.getElementById('input-palavra').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        tentarPalavra();
    }
});