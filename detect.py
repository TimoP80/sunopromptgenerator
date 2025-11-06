import tensorflow as tf

print("TensorFlow GPU devices:", tf.config.list_physical_devices('GPU'))
if len(tf.config.list_physical_devices('GPU')) > 0:
    print("TensorFlow is detecting a GPU.")
else:
    print("TensorFlow is not detecting a GPU.")