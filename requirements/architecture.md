# Spectra Architecture Requirements

Spectra is a web application that has a frontend and backend.

### Frontend: 

- Frontend: Next.js or React (subject for discussion) 
- Mobile responsive design
- Support streaming responses from AI Agent
- Dynamic components for AI Agent UI when displaying Data Cards - consider to use AG-UI (https://docs.ag-ui.com/introduction)

### Backend: 

- Backend: Python 

- AI Agent Framework: LangChain + FastAPI
    - persistent agent memory storage: PostgreSQL
    - API based communication between frontend and backend (keep it independent from UI)
    - LLM for AI Agent: configurable in settings via YAML file + environment variables
    - Sandbox environment for Python code execution: configurable in settings via YAML file + environment variables
    - Must support streaming responses from AI Agent
    - modular and independent AI Agent modules which can be customized and extended
    
- Authentication: 
    - Local authentication (Email and Password)

- Database: 
    - Local database: PostgreSQL
    - Google authentication

- File Storage: 
    - Support multiple file storage options: Local or S3 like storage (subject for discussion). Configurable in settings.
    - For MVP only use Local file storage - segregated by user


### Deployment: 

- Docker based deployment, configurable in settings via YAML file + environment variables
- Separation between frontend and backend. 
- Consider to separate the AI Agent module as a separate engine (container). To be discussed the pros and cons of this approach.
- AI Agent python runtime environment sandboxed (subject for discussion)


### AI Agent Modules

- AI Agent modules are modular and independent and wrapped as a FastAPI application
- must support streaming responses from AI Agent to the front end
- Use LangChain to build the AI Agent modules
- Tools for AI Agent modules can be configured in settings via YAML file + environment variables
- External tools e.g., search, crawler, etc can be used must be deterministic as part of the solution design
- AI Agents (non exhaustive list): 
    - Onbarding Agent: perform onboarding tasks for newly uploaded data
        - data format check
        - generate metadata for the dataset
        - suggest analysis
        - ask clarifying questions
    - Coding Agent: generate Python code based on user queries to the data. Output in dataset.
    - Code checker agent: ensure the code generated is according to the input and output structure format (pydantic format)
    - Data analysis Agent: perform data analysis to be displayed as Data Cards as output
    - Data visualization Agent: perform data visualization to be displayed as Data Cards as output
- Guardrails must be in place, for example: 
    - Ensure the code doesn't run risky operations such as deleting files, drop tables, etc
    - enforce deterministic code execution (avoid unlimited loops, etc)
- Agent execution must be traceable e.g, use of LangSmith
