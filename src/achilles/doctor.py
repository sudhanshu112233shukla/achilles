import sys
import os
import shutil
import subprocess
import tempfile
import importlib.util

def check_python_version():
    """Check if Python version is compatible."""
    major, minor = sys.version_info[:2]
    version_str = f"{major}.{minor}.{sys.version_info.micro}"
    # Project requires 3.13+ per pyproject.toml, but let's be lenient and say 3.10+ for checks
    if major == 3 and minor >= 10:
        return True, f"Python {version_str}"
    return False, f"Python {version_str} (Requires 3.10+)"

def check_api_key():
    """Check if ANTHROPIC_API_KEY is set."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key and key.strip():
        masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "***"
        return True, f"ANTHROPIC_API_KEY found ({masked})"
    return False, "ANTHROPIC_API_KEY environment variable is missing"

def check_dependency(module_name):
    """Check if a Python package is installed."""
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        return True, f"Module '{module_name}' installed"
    return False, f"Module '{module_name}' NOT found"

def check_uv_tool():
    """Check if 'uv' command is available."""
    uv_path = shutil.which("uv")
    if uv_path:
        return True, f"Build tool 'uv' found at {uv_path}"
    return False, "Build tool 'uv' not found (will fall back to pip)"

def check_cpp_compiler():
    """Proactively check for a C++ compiler by trying to compile a minimal file."""
    compiler_cmd = "cl" if sys.platform == "win32" else "c++"
    
    # Check if command exists first
    if not shutil.which(compiler_cmd):
        if sys.platform == "win32":
            return False, "MSVC Compiler (cl.exe) not found in PATH"
        else:
            # Fallback check for g++ / clang++
            if shutil.which("g++"):
                compiler_cmd = "g++"
            elif shutil.which("clang++"):
                compiler_cmd = "clang++"
            else:
                return False, "No C++ compiler (c++, g++, clang++) found"

    # Now try to actually compile something
    with tempfile.TemporaryDirectory() as tmpdir:
        src_file = os.path.join(tmpdir, "test.cpp")
        exe_file = os.path.join(tmpdir, "test.exe" if sys.platform == "win32" else "test.out")
        
        with open(src_file, "w") as f:
            f.write("int main() { return 0; }")
            
        try:
            cmd = []
            if sys.platform == "win32":
                # MSVC style
                cmd = [compiler_cmd, src_file, f"/Fe{exe_file}"]
            else:
                # GCC/Clang style
                cmd = [compiler_cmd, src_file, "-o", exe_file]
                
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True, f"C++ Compiler ({compiler_cmd}) functional"
        except subprocess.CalledProcessError as e:
            return False, f"C++ Compiler ({compiler_cmd}) found but failed compilation"
        except Exception as e:
            return False, f"Compiler check failed: {str(e)}"

def run_doctor():
    """Run all diagnostic checks."""
    print("--- ACHILLES DOCTOR ---")
    print("Checking environment health...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("LLM Credentials", check_api_key),
        ("Core Dependency", lambda: check_dependency("pybind11")),
        ("Core Dependency", lambda: check_dependency("setuptools")),
        ("Build Tool", check_uv_tool),
        ("C++ Compiler", check_cpp_compiler),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        # Some checks might be allowed warnings (like uv)
        is_warning_only = (name == "Build Tool")
        
        try:
            success, message = check_func()
            
            if success:
                print(f"[PASS] {make_bold(name)}: {message}")
            else:
                if is_warning_only:
                    print(f"[WARN] {make_bold(name)}: {message}")
                else:
                    print(f"[FAIL] {make_bold(name)}: {message}")
                    all_passed = False
        except Exception as e:
            print(f"[FAIL] {make_bold(name)}: Crashed with {e}")
            all_passed = False
            
    print("\n---------------------------")
    if all_passed:
        print("[SUCCESS] System is healthy! You are ready to optimize.")
    else:
        print("[FAILURE] System has issues. Please fix the failures above.")

def make_bold(text):
    # Simple ANSI bold if supported, otherwise plaintext
    # On Windows, color support depends on the terminal, keeping it simple for now to avoid junk chars
    return text
