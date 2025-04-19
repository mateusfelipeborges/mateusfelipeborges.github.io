// ✨ script.js - Ritual de Invocação ✨

document.addEventListener("DOMContentLoaded", () => {
    // Cria o botão mágico
    const botao = document.createElement("button");
    botao.textContent = "Invocar presença";
    botao.className = "interagir";
  
    // Ao clicar, revela uma mensagem ritualística
    botao.addEventListener("click", () => {
      const mensagem = document.createElement("p");
      mensagem.textContent = "Uma presença suave toca o véu entre mundos...";
      mensagem.style.opacity = 0;
      mensagem.style.transition = "opacity 2s";
  
      document.body.appendChild(mensagem);
  
      // Fade-in sutil
      setTimeout(() => {
        mensagem.style.opacity = 1;
      }, 100);
    });
  
    // Adiciona o botão ao corpo do site
    document.body.appendChild(botao);
  });
  