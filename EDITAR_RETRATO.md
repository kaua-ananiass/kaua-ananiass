# Ajustar o retrato pixel por pixel

Edite [`portrait-pixels.txt`](portrait-pixels.txt) pelo lápis do GitHub. Ele é a fonte do retrato exibido no README. Ao salvar a alteração na `main`, a ação **Atualizar estatisticas do perfil** recria `dark_mode.svg` e `light_mode.svg` sem perder seus ajustes; as estatísticas continuam automáticas. Não edite os SVGs diretamente, pois a ação os substitui.

Cada uma das 39 linhas representa uma linha do desenho. Entre os dois `|` há exatamente 51 caracteres (pixels). Os números `01` a `39` e os `|` são apenas guias: não os altere. Espaços também contam como pixels. Use um editor de fonte monoespaçada e evite Tab.

Legenda:

- Espaço: vazio; `.`: detalhe discreto do fundo.
- `@`, `%`, `#`, `*`, `+`, `=`: tons do retrato, do mais forte ao mais leve.
- `R`: vermelho da bolsa; `Y`: amarelo; `B`: azul; `G`: verde; `K`: sombra/fecho da bolsa.

A bolsa está principalmente nas linhas 23 a 28. Para movê-la um pixel à direita, por exemplo, troque um caractere colorido por um espaço ou tom da roupa à esquerda e coloque a mesma letra uma coluna à direita. Mantenha sempre 51 caracteres entre `|` e `|`. Se alguma linha ficar com tamanho inválido, o gerador mostrará a linha e interromperá a atualização em vez de publicar uma arte desalinhada.

Depois do commit, confira a execução em **Actions → Atualizar estatisticas do perfil** e recarregue o perfil. O arquivo `portrait-source.jpg` permanece como referência fotográfica, mas não substitui os pixels editados.
