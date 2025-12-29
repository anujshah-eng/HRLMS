# Acelucid MindMentor


### Installation:
    uv sync

------------------------

### Running the Application:
#### Run with Uvicorn (for FastAPI or ASGI apps)
    uvicorn main:app --reload --port 8000

#### Code Linting:
    pylint **/*.py

## Environment Configuration
#### Environment configuration files are located in the envs/ directory:
    envs/.env.dev → Development
    envs/.env.staging → Staging
    envs/.env.prod → Production

#### Set the correct environment before running database setup or starting the application.

## Database Setup - Commands
## Windows (Command Prompt)
#### Development
set ENV=dev&& python -m scripts.seed  

#### Staging
set ENV=staging&& python -m scripts.seed  

#### Production
set ENV=prod&& python -m scripts.seed  

## Linux / macOS (Bash)
#### Development
ENV=dev python -m scripts.seed  

#### Staging
ENV=staging python -m scripts.seed  

#### Production
ENV=prod python -m scripts.seed  

## PowerShell
#### Development
$env:ENV="dev"; python -m scripts.seed  

#### Staging
$env:ENV="staging"; python -m scripts.seed  

#### Production
$env:ENV="prod"; python -m scripts.seed  
