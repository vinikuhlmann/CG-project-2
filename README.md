# CG-project-2
Projeto de construção de um cenário 3D com controle da câmera, movimento, textura e iluminação

## Arquivos

- **model.py:**
  - load_obj(): carrega arquivos .obj 
  - load_texture(): carrega texturas e conecta-as com seu id
  - Model3d: classe que armazena as listas de vértices, coordenadas de textuas e normais, o vértice inicial e a quantidade de vértices, as texturas e os parâmetros da matriz Model de um objeto, além de calcular sua matriz Model com base nos parâmetros
- **glfw_instance.py:**
  - GlfwInstance: instancia um programa e uma janela do GLFW, com todos os procedimentos necessários, como a criação e compilação de códigos GLSL

## Tarefas
### Estrutura do código
- [X] Classe de instanciação do programa
- [X] Classe de objetos 3D
- [ ] Administrador de renderização de objetos
- [ ] Classe de câmera/mouse

### Objetos
- [ ] Ambiente interno
- [ ] Três modelos internos
- [ ] Duas texturas de terreno
- [ ] Dois modelos externos estáticos
- [ ] Um modelo externo animado
- [ ] Céu para o ambiente externo
- [ ] Restrição de exploração aos limites do cenário
- [ ] Manipulação da matriz View e da Projection
- [ ] Fonte de luz móvel
