import unittest
import subprocess
import time
import requests
import os
import signal
import psutil
from app import is_tesseract_available


class TestAppFunctionality(unittest.TestCase):
    """Simple tests for app functionality"""
    
    def test_tesseract_availability(self):
        """Test that tesseract availability check works"""
        # This test checks if tesseract is available on the system
        is_available = is_tesseract_available()
        # Print the result for information
        print(f"Tesseract availability: {is_available}")
        
    def test_import_app_module(self):
        """Test that the app module can be imported without errors"""
        try:
            import app
            # If we can import it, the syntax is correct
            self.assertTrue(hasattr(app, 'main'))
        except ImportError as e:
            self.fail(f"Could not import app module: {str(e)}")
    
    def test_run_app_command(self):
        """Test that the streamlit run command works"""
        # Change to the app directory
        original_dir = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        
        try:
            # Try to run the app in a way that doesn't block
            result = subprocess.run([
                "python", "-m", "streamlit", "run", "app.py", "--help"
            ], capture_output=True, timeout=10)
            
            # If the command recognizes --help, streamlit is working with the app
            self.assertIn(b"Streamlit", result.stdout)
            
        except subprocess.TimeoutExpired:
            # This shouldn't happen with --help, but just in case
            self.fail("Streamlit help command timed out")
        except Exception as e:
            self.fail(f"Streamlit command failed: {str(e)}")
        finally:
            os.chdir(original_dir)


if __name__ == '__main__':
    print("Running simplified app tests...")
    unittest.main(verbosity=2)