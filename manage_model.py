#!/usr/bin/env python3
"""
Model Management Utility
Easily change the LLM model used throughout the application
"""
import os
import sys
from pathlib import Path


def get_current_model():
    """Get the currently configured model from .env file"""
    env_path = Path(__file__).parent / ".env"
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OLLAMA_MODEL='):
                    return line.split('=', 1)[1].strip()
    
    # Default if not found
    return "medllama2:7b"


def list_available_models():
    """List available Ollama models"""
    import subprocess
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]
                    models.append(model_name)
            return models
        else:
            print("Error listing models:", result.stderr)
            return []
    except FileNotFoundError:
        print("Ollama not found. Please install Ollama first.")
        return []


def update_env_file(new_model: str):
    """Update the .env file with new model"""
    env_path = Path(__file__).parent / ".env"
    
    if env_path.exists():
        # Read current content
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Update the OLLAMA_MODEL line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('OLLAMA_MODEL='):
                lines[i] = f'OLLAMA_MODEL={new_model}'
                break
        
        # Write back
        with open(env_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✓ Updated .env file: OLLAMA_MODEL={new_model}")
    else:
        print("Warning: .env file not found")


def pull_model(model_name: str):
    """Pull a model using Ollama"""
    import subprocess
    try:
        print(f"Pulling model {model_name}...")
        result = subprocess.run(['ollama', 'pull', model_name], check=True)
        print(f"✓ Successfully pulled {model_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error pulling model {model_name}: {e}")
        return False
    except FileNotFoundError:
        print("Ollama not found. Please install Ollama first.")
        return False


def change_model(new_model: str, auto_pull: bool = True):
    """Change the model used throughout the application"""
    print(f"Changing model to: {new_model}")
    
    # Check if model is available
    available_models = list_available_models()
    
    if new_model not in available_models:
        if auto_pull:
            print(f"Model {new_model} not found locally. Attempting to pull...")
            if not pull_model(new_model):
                print("Failed to pull model. Aborting.")
                return False
        else:
            print(f"Model {new_model} not found locally. Please pull it first with: ollama pull {new_model}")
            return False
    
    # Update .env file
    update_env_file(new_model)
    
    print(f"✓ Model changed to {new_model}")
    print("Note: Restart your application for changes to take effect.")
    return True


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Model Management Utility")
        print("Usage:")
        print(f"  {sys.argv[0]} current           - Show current model")
        print(f"  {sys.argv[0]} list             - List available models")
        print(f"  {sys.argv[0]} change <model>   - Change to specified model")
        print(f"  {sys.argv[0]} pull <model>     - Pull a specific model")
        print()
        print(f"Current model: {get_current_model()}")
        return
    
    command = sys.argv[1]
    
    if command == "current":
        print(f"Current model: {get_current_model()}")
    
    elif command == "list":
        models = list_available_models()
        current = get_current_model()
        print("Available models:")
        for model in models:
            marker = " (current)" if model == current else ""
            print(f"  {model}{marker}")
    
    elif command == "change":
        if len(sys.argv) < 3:
            print("Error: Please specify a model name")
            print(f"Usage: {sys.argv[0]} change <model_name>")
            return
        
        new_model = sys.argv[2]
        change_model(new_model)
    
    elif command == "pull":
        if len(sys.argv) < 3:
            print("Error: Please specify a model name")
            print(f"Usage: {sys.argv[0]} pull <model_name>")
            return
        
        model_name = sys.argv[2]
        pull_model(model_name)
    
    else:
        print(f"Unknown command: {command}")
        main()


if __name__ == "__main__":
    main()
