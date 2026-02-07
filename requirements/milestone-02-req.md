## Milestone v0.2 Requirements

### 1.  Enhance AI agents with memory persistence - availble in the TO DO list
- Allow users to maintain context across chat sessions within the same chat tab
- this allows users to continue a conversation without losing context for example: user can ask the tool to add a new column to the data and then ask for a summary
- when chat tab is closed, the context should be cleared. User should be warned that closing the tab will clear the context before proceeding
- context window should be configurable in the config file
- if context window is exceeded: user will be warned and if they choose to continue, the oldest messages should be removed

### 2. Add support for additional LLM providers - availble in the TO DO list
- Add support for Ollama - note: ollama can either be run locally or remotely
- Add support for OpenRouter, this gives flexibility to connect to various LLM providers such as DeepSeek, OpenAI, Anthropic, etc via OpenRouter configuration

### 3. Agent Level LLM Configuration
- Each agent should have its own LLM provider configuration. For example, coder agent can use Anthropic Sonnet 4.5 model, while code checker agent can use OpenAI GPT-4.0 model. 
- This should be configurable in the config file

### 4. Add support for additional tools
- Add support for web search tool using serper dev: https://serper.dev/
- This should be configurable in the config file
- Tools will be enabled for the Analyst agent and can be used to search the web for information such as latest market data for benchmarking purposes

### 5. Add support chat query suggestions
- When the user opens a new chat tab, display query suggestions based on the initial data analysis result
- display 5-6 suggestions which user can click to start a new chat
- when selected the chat should start with the selected query
- chat suggestion to be displayed in three groups:
  - 2-3 suggestions for general query analysis: Eg., "show me the data summary"
  - 2-3 suggestions for Benchmarking analysis Eg., "how does my tiktok campaign perform against the similary product in the industry" 
  - 2-3 suggestions for Trend and predictive analysis Eg. "how likely is bags category to perform in the next quarter"

### 6. Migrate email service from Mailgun API to standard SMTP - available in the TO DO list
- Update the email configuration to use standard SMTP settings instead of Mailgun
- This will allow users to use any SMTP provider for sending emails
- The configuration should be in the config file

### 7. Enable forgot password functionality via email
- The reset password link should be sent via email instead of sent on log
- Dev mode should be disabled once SMTP is configured (depends on SMTP configuration as per item 6 above)
- The configuration should be in the config file

