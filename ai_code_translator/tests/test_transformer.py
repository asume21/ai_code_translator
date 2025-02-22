import unittest
from transformer_translator import TransformerTranslator
from AIcodetranslator import CodeTranslator

class TestTransformerTranslator(unittest.TestCase):
    def setUp(self):
        """Set up the translators before each test."""
        self.base_translator = CodeTranslator()
        self.transformer_translator = TransformerTranslator()
        self.transformer_translator.load_model()

    def test_simple_python_to_javascript(self):
        """Test simple Python to JavaScript translation."""
        python_code = """
def calculate_sum(a, b):
    result = a + b
    return result
"""
        expected_js = """
function calculateSum(a, b) {
    let result = a + b;
    return result;
}
"""
        # Test transformer translator
        transformer_result = self.transformer_translator.translate(python_code, "python", "javascript")
        self.assertIsNotNone(transformer_result)
        
        print("\nSimple Python to JavaScript Translation:")
        print("Original Python code:")
        print(python_code)
        print("\nExpected JavaScript code:")
        print(expected_js)
        print("\nTransformer Translator result:")
        print(transformer_result)

    def test_complex_python_to_javascript(self):
        """Test complex Python to JavaScript translation."""
        python_code = """
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        print(f"Hello, my name is {self.name} and I am {self.age} years old.")
"""
        expected_js = """
class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
    
    greet() {
        console.log(`Hello, my name is ${this.name} and I am ${this.age} years old.`);
    }
}
"""
        # Test transformer translator
        transformer_result = self.transformer_translator.translate(python_code, "python", "javascript")
        self.assertIsNotNone(transformer_result)
        
        print("\nComplex Python to JavaScript Translation:")
        print("Original Python code:")
        print(python_code)
        print("\nExpected JavaScript code:")
        print(expected_js)
        print("\nTransformer Translator result:")
        print(transformer_result)

    def test_tensorflow_to_paddle(self):
        """Test TensorFlow to PaddlePaddle translation."""
        tensorflow_code = """
import tensorflow as tf

# Create a simple sequential model
model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(32, 3, activation='relu', input_shape=(28, 28, 1)),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10, activation='softmax')
])
"""
        expected_paddle = """
import paddle

# Create a simple sequential model
model = paddle.nn.Sequential(
    paddle.nn.Conv2D(1, 32, kernel_size=3),
    paddle.nn.ReLU(),
    paddle.nn.MaxPool2D(kernel_size=2),
    paddle.nn.Flatten(),
    paddle.nn.Linear(in_features=5408, out_features=128),
    paddle.nn.ReLU(),
    paddle.nn.Dropout(p=0.2),
    paddle.nn.Linear(in_features=128, out_features=10),
    paddle.nn.Softmax()
)
"""
        # Test transformer translator
        transformer_result = self.transformer_translator.translate(tensorflow_code, "tensorflow", "paddle")
        self.assertIsNotNone(transformer_result)
        
        print("\nTensorFlow to PaddlePaddle Translation:")
        print("Original TensorFlow code:")
        print(tensorflow_code)
        print("\nExpected PaddlePaddle code:")
        print(expected_paddle)
        print("\nTransformer Translator result:")
        print(transformer_result)

if __name__ == '__main__':
    unittest.main()
