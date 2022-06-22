from glfw_instance import GlfwInstance as GI
from model import Coord3d
from model_manager import ModelManager

GI.initialize()
ModelManager.load_model('caixa', r=Coord3d(0.0, 1.0, 0.0))

print(ModelManager.models)
print(ModelManager.vertices)
print(ModelManager.texture_coords )
print(ModelManager.normals)
print(ModelManager.vertex_count)
print(ModelManager.texture_count)