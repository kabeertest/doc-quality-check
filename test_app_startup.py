import unittest
import subprocess
import time
import requests
import os
import signal
import psutil
from app import is_tesseract_available


class TestAppStartup(unittest.TestCase):
    """Unit tests for app startup functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.process = None
        
    def tearDown(self):
        """Clean up after each test method."""
        if self.process and self.process.poll() is None:
            # Terminate the process group
            parent = psutil.Process(self.process.pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except psutil.TimeoutExpired:
                parent.kill()
    
    def test_tesseract_availability(self):
        """Test that tesseract availability check works"""
        # This test checks if tesseract is available on the system
        is_available = is_tesseract_available()
        # Print the result for information
        print(f"Tesseract availability: {is_available}")
        
    def test_app_starts_without_error(self):
        """Test that the app starts without throwing an exception"""
        # Change to the app directory
        original_dir = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        
        try:
            # Start the Streamlit app in a subprocess using Python module
            self.process = subprocess.Popen(
                ["python", "-m", "streamlit", "run", "app.py", "--server.port", "8502"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a few seconds for the app to start
            time.sleep(5)
            
            # Check if the process is still running
            self.assertIsNone(self.process.poll(), "App process terminated unexpectedly")
            
        except FileNotFoundError:
            self.fail("Streamlit is not installed or not in PATH")
        except Exception as e:
            self.fail(f"Failed to start app: {str(e)}")
        finally:
            os.chdir(original_dir)
    
    def test_app_responds_on_port(self):
        """Test that the app responds on the expected port after starting"""
        # Change to the app directory
        original_dir = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        
        try:
            # Start the Streamlit app in a subprocess using Python module
            self.process = subprocess.Popen(
                ["python", "-m", "streamlit", "run", "app.py", "--server.port", "8503"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for the app to start
            time.sleep(8)
            
            # Check if the process is still running
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                self.fail(f"App terminated early. Stdout: {stdout.decode()}, Stderr: {stderr.decode()}")
            
            # Try to connect to the app
            try:
                response = requests.get("http://localhost:8503", timeout=10)
                # If we get here, the app is responding
                self.assertEqual(response.status_code, 200)
            except requests.exceptions.ConnectionError:
                self.fail("Could not connect to the app on http://localhost:8503")
                
        except FileNotFoundError:
            self.fail("Streamlit is not installed or not in PATH")
        except Exception as e:
            self.fail(f"Failed to test app response: {str(e)}")
        finally:
            os.chdir(original_dir)


if __name__ == '__main__':
    print("Running app startup tests...")
    unittest.main(verbosity=2)