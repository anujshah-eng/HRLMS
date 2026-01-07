# Acelucid HRMS - AI Interview Backend

A powerful FastAPI-based backend system for managing AI-driven interviews. This application leverages OpenAI's Realtime API to conduct interactive voice-based interviews, evaluate candidate performance, and provide detailed analytical feedback.

## 🚀 Features

*   **Realtime AI Interviews**: 
    *   Create ephemeral interview sessions compatible with OpenAI's Realtime API.
    *   Supports custom job descriptions, required skills, and specific interview questions.
    *   Conducts voice-based interviews with multiple persona options (e.g., "Priya Sharma", "Sarah Johnson").
*   **Automated Evaluation**: 
    *   Comprehensive analysis of interview transcripts.
    *   Generates scores, strength/weakness analysis, and actionable recommendations.
*   **Interview Management**: 
    *   Track interview history, status, and outcomes.
    *   View detailed conversation logs and timestamps.
    *   Soft-delete capability for session management.
*   **Token & Cost Tracking**: 
    *   Monitor token usage for system instructions, realtime conversation, and evaluations.
*   **Hybrid Database Architecture**: 
    *   Utilizes **MongoDB** for unstructured interview data and logs.
    *   Utilizes **MySQL** for structured user and relational data.

## 🛠️ Technology Stack

*   **Core**: Python 3.12+, FastAPI
*   **AI & LLM**: LangChain, LangGraph, OpenAI Realtime API
*   **Databases**: 
    *   MongoDB (using Motor for async)
    *   MySQL (using aiomysql/pymysql)
    *   Alembic (Migration management)
*   **Authentication & Security**: Authlib, PyJWT, BCrypt
*   **DevOps & Tooling**: Uvicorn, UV (Package Manager), Docker support

## 📋 Prerequisites

Ensure you have the following installed:

*   **Python**: Version 3.12 or higher
*   **Databases**: Running instances of MySQL and MongoDB
*   **Package Manager**: `uv` (recommended) or `pip`

## ⚙️ Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Dependencies**:
    Using `uv` (recommended):
    ```bash
    uv sync
    ```
    Or using `pip`:
    ```bash
    pip install .
    ```

3.  **Environment Configuration**:
    Create a `.env` file in the root configuration directory or `envs/` folder as per your deployment strategy.
    
    Required Environment Variables (Example):
    ```env
    ENV=dev
    HOST=0.0.0.0
    PORT=8001
    
    # Database Credentials
    MYSQL_URL=mysql+pymysql://user:password@localhost:3306/db_name
    MONGODB_URL=mongodb://localhost:27017/db_name
    
    # AI/ML Keys
    OPENAI_API_KEY=sk-...
    GOOGLE_API_KEY=...
    ```

## 🏃‍♂️ Running the Application

Start the development server using Uvicorn:

```bash
uvicorn main:app --reload --port 8001
```

Or via the entrypoint script:

```bash
python main.py
```

The API will be available at `http://localhost:8001`.

## 📚 API Documentation

Once the application is running, you can access the interactive API documentation:

*   **Swagger UI**: `http://localhost:8001/docs`
*   **ReDoc**: `http://localhost:8001/redoc`

## 📂 Project Structure

```
├── agents/             # AI Agents and logic (LangGraph/LangChain)
├── config/             # Configuration loaders and validators
├── connections/        # Database connection managers (MySQL, MongoDB)
├── custom_utilities/   # Shared utility functions and exceptions
├── dto/                # Data Transfer Objects (Pydantic models)
├── models/             # Database models (SQLAlchemy)
├── repository/         # Data access layer
├── routers/            # FastAPI route definitions
├── services/           # Business logic layer
├── main.py             # Application entry point
├── pyproject.toml      # Project dependencies and metadata
└── README.md           # Project documentation
```

## 📝 License

Acelucid Technologies Pvt. Ltd.
