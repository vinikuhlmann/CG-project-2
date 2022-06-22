import glfw
import OpenGL.GL.shaders
from OpenGL.GL import *

class GlfwInstance:

    def __init__(self, width, height, num_textures) -> None:

        self.width = width
        self.height = height

        # Inicializa o glfw
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        self.window = glfw.create_window(width, height, "Iluminação", None, None)
        glfw.make_context_current(self.window)

        # GLSL vertex shader
        vertex_code = """
                attribute vec3 position;
                attribute vec2 texture_coord;
                attribute vec3 normals;
                
                varying vec2 out_texture;
                varying vec3 out_fragPos;
                varying vec3 out_normal;
                        
                uniform mat4 model;
                uniform mat4 view;
                uniform mat4 projection;        
                
                void main(){
                    gl_Position = projection * view * model * vec4(position,1.0);
                    out_texture = vec2(texture_coord);
                    out_fragPos = vec3(  model * vec4(position, 1.0));
                    out_normal = vec3( model *vec4(normals, 1.0));            
                }
                """

        # Glsl fragment shader
        fragment_code = """
                uniform vec3 lightPos; // define coordenadas de posicao da luz
                vec3 lightColor = vec3(1.0, 1.0, 1.0);
                
                uniform float ka; // coeficiente de reflexao ambiente
                uniform float kd; // coeficiente de reflexao difusa
                
                uniform vec3 viewPos; // define coordenadas com a posicao da camera/observador
                uniform float ks; // coeficiente de reflexao especular
                uniform float ns; // expoente de reflexao especular

                varying vec2 out_texture; // recebido do vertex shader
                varying vec3 out_normal; // recebido do vertex shader
                varying vec3 out_fragPos; // recebido do vertex shader
                uniform sampler2D samplerTexture;
                
                void main(){
                
                    vec3 ambient = ka * lightColor; // reflexão ambiente     
                
                    vec3 norm = normalize(out_normal); // normaliza vetores perpendiculares
                    vec3 lightDir = normalize(lightPos - out_fragPos); // direcao da luz
                    float diff = max(dot(norm, lightDir), 0.0); // verifica limite angular (entre 0 e 90)
                    vec3 diffuse = kd * diff * lightColor; // iluminacao difusa
                    
                    vec3 viewDir = normalize(viewPos - out_fragPos); // direcao do observador/camera
                    vec3 reflectDir = normalize(reflect(-lightDir, norm)); // direcao da reflexao
                    float spec = pow(max(dot(viewDir, reflectDir), 0.0), ns);
                    vec3 specular = ks * spec * lightColor; // reflexão especular    
                    
                    vec4 texture = texture2D(samplerTexture, out_texture);
                    vec4 result = vec4((ambient + diffuse + specular),1.0) * texture; // aplica iluminacao
                    gl_FragColor = result; // modelo de iluminação
                }
                """

        # Requisita slots da GPU
        self.program  = glCreateProgram()
        vertex   = glCreateShader(GL_VERTEX_SHADER)
        fragment = glCreateShader(GL_FRAGMENT_SHADER)

        # Associa o código-fonte aos slots solicitados
        glShaderSource(vertex, vertex_code)
        glShaderSource(fragment, fragment_code)

        # Compila os shaders
        glCompileShader(vertex)
        if not glGetShaderiv(vertex, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(vertex).decode()
            print(error)
            raise RuntimeError("Erro de compilacao do Vertex Shader")
        glCompileShader(fragment)
        if not glGetShaderiv(fragment, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(fragment).decode()
            print(error)
            raise RuntimeError("Erro de compilacao do Fragment Shader")

        # Conecta os shaders com o programa
        glAttachShader(self.program, vertex)
        glAttachShader(self.program, fragment)

        # Constrói o programa
        glLinkProgram(self.program)
        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            print(glGetProgramInfoLog(self.program))
            raise RuntimeError('Linking error')
            
        # Faz com que o programa seja o programa padrão
        glUseProgram(self.program)

        # Ativa texturas
        glEnable(GL_TEXTURE_2D)
        glGenTextures(num_textures)