import base64
import struct
import math

vec1_list = [1.0]
vec2_list = [5.189133789917912e-100]

dim = len(vec1_list)

b1 = base64.b64encode(struct.pack(f"<{dim}f", *vec1_list)).decode()
b2 = base64.b64encode(struct.pack(f"<{dim}f", *vec2_list)).decode()

vec1 = struct.unpack(f"<{dim}f", base64.b64decode(b1))
vec2 = struct.unpack(f"<{dim}f", base64.b64decode(b2))

print(f"vec1: {vec1}")
print(f"vec2: {vec2}")

mag1 = math.sqrt(sum(x * x for x in vec1_list))
mag2 = math.sqrt(sum(x * x for x in vec2_list))

print(f"mag1 (list): {mag1}")
print(f"mag2 (list): {mag2}")

mag1_struct = math.sqrt(math.fsum(x * x for x in vec1))
mag2_struct = math.sqrt(math.fsum(x * x for x in vec2))

print(f"mag1 (struct): {mag1_struct}")
print(f"mag2 (struct): {mag2_struct}")

dot_struct = math.fsum(a * b for a, b in zip(vec1, vec2, strict=True))
print(f"dot (struct): {dot_struct}")

sim = dot_struct / (mag1_struct * mag2_struct) if mag1_struct > 0 and mag2_struct > 0 else 0.0
print(f"similarity (struct): {sim}")

expected_similarity = math.fsum(a * b for a, b in zip(vec1_list, vec2_list, strict=True)) / (mag1 * mag2)
print(f"expected_similarity: {expected_similarity}")
