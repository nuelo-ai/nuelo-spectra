## Milestone v0.3 Requirements: Multi-file conversation support

### Current Behavior:
- In the current version of the tool, each file is processed independently
- user uploads a file, the file being onboarded and assessed by AI onboarding agent, and the context of the file is saved to be used for further conversation and analysis when user interacting with the agents
- user then can chat with the file via the Chat Tab where the result is displayed as Data Card
- The chat tab becomes the workspace to interact with the file

### Problem with the current behavior:
- Context within the Chat Tab is limited to the file single 
- Not possible to do a analysis accross different data sources
- One file can only have one chat session
- User has to upload the same file if the user wishes to have a separate conversation on the same data source 

### Solution to the problem:
- User should have the flexibility to interact with multiple files/data sources 
- There must be a mechanism to link multiple files to a single conversation
- A chat could be considered as a workspace where user can interact with multiple file data source
- File is independent of the chat session
- In general, this is very similar to current behavior of Chat GPT, where "Chat" is the center of the conversation

### New User Requirements:

1. Starting a new Chat
- To start a chat, it can be triggered by three ways:
    - User logs in to the application and user will be greeted with a new "chat session" that shows a friendly greetings asking what analysis they want to perform today
    - User can click on the "New Chat" button on the left sidebar to create a new chat session
    - via the upload mechanism, just after the file is uploaded, a new chat session will be created. See Requirement #3 "Adding the file via Upload Mechanism" for more details
- The chat has no context (no file is linked to the chat) in the beginning
- Before user can initiate a chat, user will be asked to link or add a file to the chat
- User can either choose to upload files to the chat or link existing files to the chat. See the Requirement #2 "selecting the file context" for more details.
- Once the file is linked to the chat, the chat will be initialized and user can start interacting with the file
- User can have multiple chat sesions open at the same time, each with its own context --> note that the key difference from the current versions here is that the "chat" is independent of the file.
- If user selects an existing chat sesion, the chat will be initialized with the context of the file linked to the chat

2. Selecting the file context via Chat Session
- User is already in the chat session
- Upload a new file
    - Upload using the button:
        - User clicks on the "Add File" button located below the chat input box: Similar to Chat GPT
        - A drop down shows up with options to upload a file or link an existing file
        - User selects upload a file option
        - User can upload a file from their local machine
    - Upload using drag/drop
        - User drags and drops a file from their local machine into the chat session
    - The upload process will trigger the same file onboarding process as in the current version where the file is analyzed, context is shown and user has the option to add more information. (This follow the same behavior as in the current version)
    - After filling the optional additional context, user can click "start chat" and it will redirect to the chat session ready for interaction
- Link existing file
    - User clicks on the "Add File" button located below the chat input box: Similar to Chat GPT
    - A drop down shows up with options to upload a file or link an existing file
    - User selects link an existing file option
    - A file modal will open up where user can select an existing file to link to the chat
    - The file will be linked to the chat and the chat will be initialized and user can start interacting with the file
- All the linked files to the chat will be displayed at the top of the chat session where user. 
    - An (i) icon will be displayed next to the file name to show the file context 
    - When (i) icon is clicked, a modal will open up showing the file context just like the current version

3. Adding the file via Upload Mechanism
- User logs in to the application
- User clicks the "My Files" button on the left sidebar, a "My Files" screen will open up
- User can click on the "Upload File" button on the "My Files" screen
- A modal will open up where user can upload a file from their local machine
- The upload process will trigger the same file onboarding process as in the current version where the file is analyzed, context is shown and user has the option to add more information. (This follow the same behavior as in the current version)
- After filling the optional additional context, user can click "start chat" and it will initialize a new chat session

4. Chat History
- User can view the chat history in the left sidebar
- User can click on the chat history to open a chat session on the main screen

5. Manage Files
- User clicks on the "My Files" button on the left sidebar
- A new "My Files" screen will open up that shows the list of files
- User can:
    - Upload a new file
    - List down all the files
    - Select a file to view the file context
    - Start a new chat session with the selected file
    - Delete the file
    - Download the file

### Key UI differences from the current version

- No more chat tabs, but now Session. No need to show the tabs at the top of the screen. When user clicks on the chat history, it will open a new chat session on the main screen. This will utilize the screen space better.
- A new file selection modal for user to select files to link to the chat session
- A new "My Files" screen that shows the list of files
- On the chat session, a list of files linked to the chat session will be displayed. This can be shown on the right side of the screen (for discussion)
- The Left sidebar will contain the following:
    - A "New Chat" button to start a new chat session
    - A "Chat History" section that shows the list of chat sessions (expanded/collapsed)
    - A "My Files" button, when clicked, it will open a new screen that list all the files

### UI Design
- Leverage the Claude Code UI Design Skills to optimize the UI design to be looked modern and user-friendly
- Allow users to switch between light and dark mode



